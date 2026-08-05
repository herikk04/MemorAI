"""Unit tests for flashcards.services.scheduler.

These exercise the scheduling logic in isolation, without touching the DB
beyond constructing in-memory Card dataclasses (we use the actual Card
model but never save it, since the scheduler only reads fields).
"""
from __future__ import annotations

from datetime import timedelta, timezone

import pytest
from django.utils import timezone as djtz

from flashcards.models import Card, Review
from flashcards.services.scheduler import (
    FSRSScheduler,
    SM2Scheduler,
    get_scheduler,
    schedule_review,
)


def _card(**kwargs):
    """Build an unsaved Card with sensible SRS defaults."""
    defaults = dict(
        front="q",
        back="a",
        interval=0.0,
        ease=2.5,
        reps=0,
        lapses=0,
        srs_algorithm=Card.SRSAlgorithm.FSRS,
    )
    defaults.update(kwargs)
    return Card(**defaults)


@pytest.fixture
def now():
    return djtz.now()


class TestFSRSScheduler:
    def test_first_good_seeds_day1_interval(self, now):
        card = _card()
        upd = FSRSScheduler().schedule(card, Review.Rating.GOOD, now=now)
        assert upd.interval == 1.0
        assert upd.reps == 1
        assert upd.lapses == 0
        assert upd.due == now + timedelta(days=1)
        assert upd.last_reviewed_at == now

    def test_again_resets_reps_and_increments_lapses(self, now):
        card = _card(reps=3, lapses=1, interval=10.0)
        upd = FSRSScheduler().schedule(card, Review.Rating.AGAIN, now=now)
        assert upd.reps == 0
        assert upd.lapses == 2
        assert upd.interval == 1.0

    def test_easy_grows_interval_and_ease(self, now):
        card = _card(reps=2, lapses=0, interval=6.0, ease=2.5)
        upd = FSRSScheduler().schedule(card, Review.Rating.EASY, now=now)
        assert upd.interval > 6.0
        assert upd.ease > 2.5
        assert upd.reps == 3

    def test_ease_clamped_to_min(self, now):
        card = _card(reps=2, lapses=5, interval=2.0, ease=1.31)
        upd = FSRSScheduler().schedule(card, Review.Rating.HARD, now=now)
        assert upd.ease >= 1.3

    def test_ease_clamped_to_max(self, now):
        card = _card(reps=10, lapses=0, interval=120.0, ease=3.49)
        upd = FSRSScheduler().schedule(card, Review.Rating.EASY, now=now)
        assert upd.ease <= 3.5


class TestSM2Scheduler:
    def test_first_good_yields_day2(self, now):
        card = _card()
        upd = SM2Scheduler().schedule(card, Review.Rating.GOOD, now=now)
        assert upd.interval == 2.0
        assert upd.reps == 1

    def test_third_good_uses_ease_multiplier(self, now):
        card = _card(reps=2, lapses=0, interval=6.0, ease=2.5)
        upd = SM2Scheduler().schedule(card, Review.Rating.GOOD, now=now)
        assert upd.interval == pytest.approx(6.0 * 2.5)
        assert upd.reps == 3

    def test_again_lapse_resets(self, now):
        card = _card(reps=5, lapses=2, interval=30.0, ease=2.6)
        upd = SM2Scheduler().schedule(card, Review.Rating.AGAIN, now=now)
        assert upd.reps == 0
        assert upd.lapses == 3
        assert upd.interval == 1.0


def test_get_scheduler_falls_back_to_default():
    assert isinstance(get_scheduler("fsrs"), FSRSScheduler)
    assert isinstance(get_scheduler("sm2"), SM2Scheduler)
    with pytest.raises(ValueError):
        get_scheduler("nope")


def test_schedule_review_picks_algorithm_from_card(now):
    card_fsrs = _card(srs_algorithm=Card.SRSAlgorithm.FSRS)
    upd_fsrs = schedule_review(card_fsrs, Review.Rating.GOOD, now=now)
    assert upd_fsrs.interval == 1.0  # FSRS seeds day 1

    card_sm2 = _card(srs_algorithm=Card.SRSAlgorithm.SM2)
    upd_sm2 = schedule_review(card_sm2, Review.Rating.GOOD, now=now)
    assert upd_sm2.interval == 2.0  # SM-2 first Good is day 2


def test_due_is_timezone_aware(now):
    card = _card()
    upd = FSRSScheduler().schedule(card, Review.Rating.GOOD, now=now)
    assert upd.due.tzinfo is not None
    # Sanity: due is ahead of now by the interval
    assert upd.due > now
    # Ensure timezone is UTC-like
    assert upd.due.utcoffset() == timezone.utc.utcoffset(None)
