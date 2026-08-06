"""Tests for the RAG flow + reindex signals + /ai/search/ endpoint."""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.ai.models import AIEvent, Embedding
from apps.ai.services.orchestrator import run_flow
from apps.ai.services.rag_index import drop_card, reindex_card
from flashcards.models import Card, Deck


class TestReindexSignal:
    """Cards auto-embed on save via post_save signal registered in apps.py."""

    @pytest.mark.django_db
    def test_creating_a_card_produces_an_embedding(self):
        deck = Deck.objects.create(name="d")
        card = Card.objects.create(deck=deck, front="python list", back="[]")
        assert Embedding.objects.filter(entity_id=card.id, entity_type="card").exists()

    @pytest.mark.django_db
    def test_updating_a_card_keeps_single_embedding(self):
        deck = Deck.objects.create(name="d")
        card = Card.objects.create(deck=deck, front="q", back="a")
        before = Embedding.objects.filter(entity_id=card.id).count()
        card.front = "q updated"
        card.save()
        after = Embedding.objects.filter(entity_id=card.id).count()
        assert before == after == 1

    @pytest.mark.django_db
    def test_deleting_a_card_drops_its_embedding(self):
        deck = Deck.objects.create(name="d")
        card = Card.objects.create(deck=deck, front="q", back="a")
        assert Embedding.objects.filter(entity_id=card.id).exists()
        card.delete()
        assert not Embedding.objects.filter(entity_id=card.id).exists()


class TestReindexService:
    @pytest.mark.django_db
    def test_reindex_card_creates_embedding(self):
        deck = Deck.objects.create(name="d")
        card = Card.objects.create(deck=deck, front="q", back="a")
        Embedding.objects.filter(entity_id=card.id).delete()
        emb = reindex_card(card)
        assert emb is not None
        assert emb.entity_type == "card"
        assert emb.entity_id == card.id

    @pytest.mark.django_db
    def test_drop_card_is_idempotent(self):
        deck = Deck.objects.create(name="d")
        card = Card.objects.create(deck=deck, front="q", back="a")
        # Delete twice should be safe.
        drop_card(card)
        drop_card(card)
        assert not Embedding.objects.filter(entity_id=card.id).exists()


class TestRunRagFlow:
    @pytest.mark.django_db
    def test_happy_path_returns_hits(self):
        deck = Deck.objects.create(name="Python")
        Card.objects.create(deck=deck, front="iterar dict python", back="for k, v in d.items()")
        Card.objects.create(deck=deck, front="criar lista python", back="[]")
        result = run_flow("rag", {"query": "como iterar dicionario python"}, user=None)
        assert result.status == "success"
        assert result.provider == "mock"
        assert len(result.hits) >= 1
        hit = result.hits[0]
        assert hit.deck_name == "Python"
        assert hit.deck_id == deck.id

    @pytest.mark.django_db
    def test_records_event(self):
        events_before = AIEvent.objects.filter(flow="rag").count()
        run_flow("rag", {"query": "q"}, user=None)
        events_after = AIEvent.objects.filter(flow="rag").count()
        assert events_after == events_before + 1
        ev = AIEvent.objects.filter(flow="rag").latest("created_at")
        assert ev.status == "success"
        assert ev.tokens_in > 0

    def test_empty_query_returns_error_result(self):
        result = run_flow("rag", {"query": ""}, user=None)
        assert result.status == "error"
        assert result.error == "empty query"
        assert result.hits == []


class TestSearchEndpoint(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/v1/ai/search/"
        # Sprint 1.5: IsAuthenticated default.
        User = get_user_model()
        self.user = User.objects.create_user(
            username="searcher", password="pw1234567"
        )
        self.client.force_authenticate(self.user)

    @pytest.mark.django_db
    def test_happy_path(self):
        deck = Deck.objects.create(name="Python")
        Card.objects.create(deck=deck, front="iterar dict python", back="for k, v in d.items()")
        resp = self.client.post(
            self.url,
            {"query": "como iterar dicionario", "top_k": 5},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["status"] == "success"
        assert body["provider"] == "mock"
        assert len(body["hits"]) >= 1
        assert "score" in body["hits"][0]
        assert "deck_name" in body["hits"][0]

    def test_missing_query_rejected(self):
        resp = self.client.post(self.url, {"top_k": 5}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_top_k_out_of_range_rejected(self):
        resp = self.client.post(
            self.url,
            {"query": "q", "top_k": 51},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_request_rejected(self):
        self.client.force_authenticate(None)
        resp = self.client.post(
            self.url, {"query": "q", "top_k": 5}, format="json"
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
