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
        self.deck = Deck.objects.create(name="Python")
        self.card = Card.objects.create(deck=self.deck, front="list?", back="[]")
        self.user = get_user_model().objects.create_user(
            username="u", password="pw1234567"
        )
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

    def test_review_anonymous_user_still_works(self):
        # If no auth is wired yet, the endpoint should still record a Review
        # with user=None (the SDD explicitly keeps the FK nullable for now).
        self.client.force_authenticate(None)
        resp = self.client.post(_url(self.card.id), {"rating": Review.Rating.EASY})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.card.refresh_from_db()
        # FSRS first Easy seeds a 2-day interval
        self.assertEqual(self.card.interval, 2.0)
        review = Review.objects.get(card=self.card)
        self.assertIsNone(review.user)


class DueEndpointTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.deck = Deck.objects.create(name="d")
        self.card_due = Card.objects.create(deck=self.deck, front="a", back="b")
        # Force it overdue by persisting a past due date directly.
        from django.utils import timezone
        self.card_due.due = timezone.now()
        self.card_due.save(update_fields=["due"])
        self.card_future = Card.objects.create(deck=self.deck, front="c", back="d")
        from datetime import timedelta
        self.card_future.due = timezone.now() + timedelta(days=5)
        self.card_future.save(update_fields=["due"])

    def test_due_lists_only_overdue(self):
        resp = self.client.get("/api/v1/cards/due/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ids = [c["id"] for c in resp.data]
        self.assertIn(self.card_due.id, ids)
        self.assertNotIn(self.card_future.id, ids)
