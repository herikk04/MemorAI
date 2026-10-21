"""Dashboard aggregates for a user: due queue, daily activity, streak, retention."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

from flashcards.models import Card, Deck, Review

RETENTION_WINDOW_DAYS = 30


def compute_streak(review_days: set[date], today: date) -> int:
    """Consecutive days with at least one review.

    A streak stays alive until the end of the day after the last review, so
    having reviewed yesterday but not yet today still counts.
    """
    day = today if today in review_days else today - timedelta(days=1)
    streak = 0
    while day in review_days:
        streak += 1
        day -= timedelta(days=1)
    return streak


def dashboard_stats(user, now: datetime | None = None) -> dict:
    now = now or timezone.now()
    today = timezone.localdate(now)
    due_q = Q(due__isnull=True) | Q(due__lte=now)
    deck_due_q = Q(cards__due__isnull=True) | Q(cards__due__lte=now)

    cards = Card.objects.filter(deck__owner=user)
    reviews = Review.objects.filter(user=user)

    review_days = set(
        reviews.annotate(day=TruncDate("reviewed_at")).values_list("day", flat=True).distinct()
    )
    window = reviews.filter(reviewed_at__gte=now - timedelta(days=RETENTION_WINDOW_DAYS))
    window_total = window.count()
    window_ok = window.exclude(rating=Review.Rating.AGAIN).count()

    decks = (
        Deck.objects.filter(owner=user)
        .annotate(
            total_cards=Count("cards", distinct=True),
            due_count=Count("cards", filter=deck_due_q, distinct=True),
            learned_cards=Count("cards", filter=Q(cards__reps__gt=0), distinct=True),
        )
        .order_by("-updated_at")
    )

    return {
        "due_count": cards.filter(due_q).count(),
        "total_cards": cards.count(),
        "reviewed_today": reviews.filter(reviewed_at__date=today).count(),
        "streak_days": compute_streak(review_days, today),
        "retention_30d": round(window_ok / window_total, 4) if window_total else None,
        "decks": [
            {
                "id": d.id,
                "name": d.name,
                "total_cards": d.total_cards,
                "due_count": d.due_count,
                "learned_cards": d.learned_cards,
            }
            for d in decks
        ],
    }
