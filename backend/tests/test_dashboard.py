"""GET /api/v1/dashboard/ and its aggregation helpers."""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from flashcards.models import Card, Deck, Review
from flashcards.services.stats import compute_streak

User = get_user_model()
TODAY = date(2026, 1, 10)


def days(*offsets):
    return {TODAY - timedelta(days=o) for o in offsets}


def test_streak_counts_consecutive_days_through_today():
    assert compute_streak(days(0, 1, 2), TODAY) == 3


def test_streak_alive_if_reviewed_yesterday_only():
    assert compute_streak(days(1, 2), TODAY) == 2


def test_streak_breaks_on_gap():
    assert compute_streak(days(0, 2, 3), TODAY) == 1
    assert compute_streak(days(2, 3), TODAY) == 0
    assert compute_streak(set(), TODAY) == 0


@pytest.fixture
def user():
    return User.objects.create_user(username="dash", password="pw1234567")


@pytest.fixture
def client(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


@pytest.mark.django_db
def test_requires_auth():
    assert APIClient().get("/api/v1/dashboard/").status_code == 401


@pytest.mark.django_db
def test_empty_account(client):
    body = client.get("/api/v1/dashboard/").json()
    assert body == {
        "due_count": 0,
        "total_cards": 0,
        "reviewed_today": 0,
        "streak_days": 0,
        "retention_30d": None,
        "decks": [],
    }


@pytest.mark.django_db
def test_aggregates_and_per_deck_counts(client, user):
    deck = Deck.objects.create(name="py", owner=user)
    new = Card.objects.create(deck=deck, front="a", back="b")
    future = Card.objects.create(
        deck=deck, front="c", back="d", reps=2, due=timezone.now() + timedelta(days=3)
    )
    Review.objects.create(user=user, card=new, rating=Review.Rating.GOOD)
    Review.objects.create(user=user, card=future, rating=Review.Rating.AGAIN)

    # Another user's data must not leak in.
    other = User.objects.create_user(username="o", password="pw1234567")
    other_deck = Deck.objects.create(name="x", owner=other)
    Card.objects.create(deck=other_deck, front="z", back="z")

    body = client.get("/api/v1/dashboard/").json()
    assert body["due_count"] == 1  # only the never-reviewed card
    assert body["total_cards"] == 2
    assert body["reviewed_today"] == 2
    assert body["streak_days"] == 1
    assert body["retention_30d"] == 0.5
    assert body["decks"] == [
        {"id": deck.id, "name": "py", "total_cards": 2, "due_count": 1, "learned_cards": 1}
    ]
