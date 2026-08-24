"""Integration tests for the review endpoint + SRS persistence."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from flashcards.models import Card, Deck, Review


def _url(card_id):
    # Namespaced router action; reverse by hand since DefaultRouter exposes
    # the route at /cards/<pk>/review/.
    return f"/api/v1/cards/{card_id}/review/"


class ReviewEndpointTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="u", password="pw1234567"
        )
        self.deck = Deck.objects.create(name="Python", owner=self.user)
        self.card = Card.objects.create(deck=self.deck, front="list?", back="[]")
        self.client.force_authenticate(self.user)

    def test_review_good_advances_srs(self):
        resp = self.client.post(
            _url(self.card.id),
            {"rating": Review.Rating.GOOD, "time_ms": 4200},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.card.refresh_from_db()
        self.assertEqual(self.card.reps, 1)
        self.assertEqual(self.card.interval, 1.0)
        self.assertIsNotNone(self.card.due)
        self.assertEqual(self.card.last_reviewed_at, self.card.last_reviewed_at)
        self.assertTrue(Review.objects.filter(card=self.card).exists())
        review = Review.objects.get(card=self.card)
        self.assertEqual(review.rating, Review.Rating.GOOD)
        self.assertEqual(review.time_ms, 4200)
        self.assertEqual(review.user, self.user)
        # Sprint 2 wired the AI feedback flow. With the mock provider the
        # flow returns status="success", so feedback_source is "ai:feedback"
        # and there is non-empty text from the mock client.
        self.assertEqual(review.feedback_source, "ai:feedback")
        self.assertTrue(review.feedback_text)

    def test_review_again_lapses(self):
        # Advance once so lapsed state is meaningful
        self.client.post(_url(self.card.id), {"rating": Review.Rating.GOOD})
        self.card.refresh_from_db()
        self.assertEqual(self.card.reps, 1)

        resp = self.client.post(_url(self.card.id), {"rating": Review.Rating.AGAIN})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.card.refresh_from_db()
        self.assertEqual(self.card.reps, 0)
        self.assertEqual(self.card.lapses, 1)
        self.assertEqual(self.card.interval, 1.0)

    def test_invalid_rating_rejected(self):
        resp = self.client.post(_url(self.card.id), {"rating": 5})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_rating_rejected(self):
        resp = self.client.post(_url(self.card.id), {"time_ms": 100})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_request_rejected(self):
        self.client.force_authenticate(None)
        resp = self.client.post(
            _url(self.card.id), {"rating": Review.Rating.EASY}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_review_on_foreign_deck_returns_404(self):
        # Ownership scoping (Sprint 1.5): a card owned by another user is
        # invisible to the requester, so Django treats it as not found.
        other = get_user_model().objects.create_user(
            username="other", password="pw1234567"
        )
        other_deck = Deck.objects.create(name="alien", owner=other)
        other_card = Card.objects.create(
            deck=other_deck, front="x", back="y"
        )
        resp = self.client.post(
            _url(other_card.id), {"rating": Review.Rating.GOOD}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class DueEndpointTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="due", password="pw1234567"
        )
        self.deck = Deck.objects.create(name="d", owner=self.user)
        self.card_due = Card.objects.create(deck=self.deck, front="a", back="b")
        # Force it overdue by persisting a past due date directly.
        from django.utils import timezone
        self.card_due.due = timezone.now()
        self.card_due.save(update_fields=["due"])
        self.card_future = Card.objects.create(deck=self.deck, front="c", back="d")
        from datetime import timedelta
        self.card_future.due = timezone.now() + timedelta(days=5)
        self.card_future.save(update_fields=["due"])
        self.client.force_authenticate(self.user)

    def test_due_lists_only_overdue(self):
        resp = self.client.get("/api/v1/cards/due/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ids = [c["id"] for c in resp.data]
        self.assertIn(self.card_due.id, ids)
        self.assertNotIn(self.card_future.id, ids)

    def test_due_excludes_cards_owned_by_other_users(self):
        # Sprint 1.5 ownership scoping via deck__owner.
        other = get_user_model().objects.create_user(
            username="other-due", password="pw1234567"
        )
        other_deck = Deck.objects.create(name="other-d", owner=other)
        other_card = Card.objects.create(deck=other_deck, front="x", back="y")
        from django.utils import timezone
        other_card.due = timezone.now()
        other_card.save(update_fields=["due"])
        resp = self.client.get("/api/v1/cards/due/")
        ids = [c["id"] for c in resp.data]
        self.assertNotIn(other_card.id, ids)
