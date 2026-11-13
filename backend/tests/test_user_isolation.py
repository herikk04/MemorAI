"""Regression tests for cross-user isolation and the review queue.

Covers: new cards entering /cards/due/, card creation in foreign decks,
RAG search scoped by owner, task polling ownership, the ?deck= filter and
embedding reindex only on content changes.
"""
from __future__ import annotations

from unittest import mock

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.ai.models import Embedding
from flashcards.models import Card, Deck


def _user(name):
    return get_user_model().objects.create_user(username=name, password="pw1234567")


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


class IsolationTests(APITestCase):
    def setUp(self):
        self.alice, self.bob = _user("alice"), _user("bob")
        self.alice_deck = Deck.objects.create(name="A", owner=self.alice)
        self.bob_deck = Deck.objects.create(name="B", owner=self.bob)
        self.alice_client, self.bob_client = _client(self.alice), _client(self.bob)

    def test_new_card_is_due(self):
        card = Card.objects.create(deck=self.alice_deck, front="f", back="b")
        resp = self.alice_client.get("/api/v1/cards/due/")
        self.assertIn(card.id, [c["id"] for c in resp.data])

    def test_cannot_create_card_in_foreign_deck(self):
        resp = self.bob_client.post(
            "/api/v1/cards/",
            {"deck": self.alice_deck.id, "front": "x", "back": "y"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Card.objects.filter(deck=self.alice_deck).exists())

    def test_cannot_move_card_to_foreign_deck(self):
        card = Card.objects.create(deck=self.bob_deck, front="f", back="b")
        resp = self.bob_client.patch(
            f"/api/v1/cards/{card.id}/", {"deck": self.alice_deck.id}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_create_card_in_own_deck(self):
        resp = self.alice_client.post(
            "/api/v1/cards/",
            {"deck": self.alice_deck.id, "front": "x", "back": "y"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_search_does_not_leak_other_users_cards(self):
        Card.objects.create(deck=self.alice_deck, front="segredo", back="alice")
        mine = Card.objects.create(deck=self.bob_deck, front="meu", back="bob")
        resp = self.bob_client.post(
            "/api/v1/ai/search/", {"query": "segredo"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ids = [h["card_id"] for h in resp.data["hits"]]
        self.assertEqual(ids, [mine.id])

    def test_owner_can_poll_own_task(self):
        from apps.ai.views import _remember_task_owner

        _remember_task_owner("t-123", self.alice)
        resp = self.alice_client.get("/api/v1/ai/tasks/t-123/")
        self.assertNotEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        # Another user gets the same 404 as for an unknown id.
        resp = self.bob_client.get("/api/v1/ai/tasks/t-123/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_deck_filter_on_cards_list(self):
        a = Card.objects.create(deck=self.alice_deck, front="1", back="1")
        other = Deck.objects.create(name="A2", owner=self.alice)
        Card.objects.create(deck=other, front="2", back="2")
        resp = self.alice_client.get(f"/api/v1/cards/?deck={self.alice_deck.id}")
        self.assertEqual([c["id"] for c in resp.data], [a.id])


class ReindexTests(APITestCase):
    def setUp(self):
        self.user = _user("u")
        self.deck = Deck.objects.create(name="d", owner=self.user)
        self.card = Card.objects.create(deck=self.deck, front="f", back="b")

    def test_review_does_not_reindex_card(self):
        client = _client(self.user)
        with mock.patch("apps.ai.signals.reindex_card") as reindex:
            resp = client.post(
                f"/api/v1/cards/{self.card.id}/review/", {"rating": 3}, format="json"
            )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        reindex.assert_not_called()

    def test_content_change_reindexes_card(self):
        with mock.patch("apps.ai.signals.reindex_card") as reindex:
            self.card.front = "novo"
            self.card.save(update_fields=["front"])
        reindex.assert_called_once()
        self.assertTrue(Embedding.objects.filter(entity_id=self.card.id).exists())
