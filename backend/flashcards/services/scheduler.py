"""
Spaced-repetition scheduling (Sprint 1).

Provides a pluggable Scheduler interface with two implementations:
  - FSRSScheduler (default): a compact FSRS-style algorithm.
  - SM2Scheduler: the classic SM-2 algorithm used by Anki.

Both take the current Card state + the user's Rating and return a
ScheduleUpdate describing the new (interval, ease, reps, lapses, due)
state. The caller (the review API) is responsible for persisting it.

Keeping this logic out of the Card model / views lets us:
  - unit-test scheduling in isolation (no DB round-trip)
  - swap algorithms per-card via Card.srs_algorithm
  - in Sprint 2+, feed Calendly-style "logical due" data to the AI
    orchestrator for "review suggestion" flows.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol

from flashcards.models import Card, Review


Rating = Review.Rating


@dataclass(frozen=True)
class ScheduleUpdate:
    interval: float
    ease: float
    reps: int
    lapses: int
    due: datetime
    last_reviewed_at: datetime

    @property
    def due_in_days(self) -> float:
        return self.interval


class Scheduler(Protocol):
    name: str

    def schedule(self, card: Card, rating: int, now: datetime | None = None) -> ScheduleUpdate: ...


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _add_days(base: datetime, days: float) -> datetime:
    return base + timedelta(days=days)


class FSRSScheduler:
    """Compact FSRS-style scheduler.

    This is intentionally a small, deterministic implementation rather than a
    full FSRS-5 port: it captures the essential behaviour (stability growth,
    difficulty eased by good/easy ratings, lapses reset interval and decay
    ease) so the system has a sane default before per-user parameter fitting
    lands in a later sprint. Swapping in a full FSRS implementation later is
    a drop-in replacement since it implements the same Scheduler protocol.
    """

    name = "fsrs"
    # FSRS-4.5 stability/difficulty knobs, kept conservative for a new user.
    FACTOR_AGAIN = 0.4
    FACTOR_HARD = 0.6
    FACTOR_GOOD = 1.0
    FACTOR_EASY = 1.3

    EASE_MIN = 1.3
    EASE_MAX = 3.5
    EASE_DECAY = 0.2
    EASE_GROWTH = 0.1
    EASE_AGAIN_PENALTY = 0.2

    DAY0 = 0.0
    DAY1 = 1.0

    def schedule(self, card: Card, rating: int, now: datetime | None = None) -> ScheduleUpdate:
        now = now or _now()
        reps = card.reps
        lapses = card.lapses
        ease = card.ease
        interval = card.interval

        if rating == Rating.AGAIN:
            reps = 0
            lapses += 1
            ease = max(self.EASE_MIN, ease - self.EASE_AGAIN_PENALTY)
            interval = self.DAY1
        else:
            reps += 1
            if reps == 1:
                # First successful review seeds the interval.
                interval = {
                    Rating.HARD: self.DAY1,
                    Rating.GOOD: self.DAY1,
                    Rating.EASY: 2.0,
                }[rating]
            else:
                factor = {
                    Rating.HARD: self.FACTOR_HARD,
                    Rating.GOOD: self.FACTOR_GOOD,
                    Rating.EASY: self.FACTOR_EASY,
                }[rating]
                # Apply ease adjustment, then scale interval by ease and factor.
                ease_delta = {
                    Rating.HARD: -self.EASE_DECAY,
                    Rating.GOOD: 0.0,
                    Rating.EASY: +self.EASE_GROWTH,
                }[rating]
                ease = max(self.EASE_MIN, min(self.EASE_MAX, ease + ease_delta))
                interval = max(self.DAY1, interval * ease * factor)

        return ScheduleUpdate(
            interval=round(interval, 4),
            ease=round(ease, 4),
            reps=reps,
            lapses=lapses,
            due=_add_days(now, interval),
            last_reviewed_at=now,
        )


class SM2Scheduler:
    """Classic SuperMemo SM-2 (the algorithm Anki's default derives from).

    Included as the explicit fallback named in the SDD's Trade-offs (item 6)
    so the codebase is never coupled to a single scheduler.
    """

    name = "sm2"
    EASE_MIN = 1.3
    EASE_MAX = 3.5
    DAY0 = 0.0
    DAY1 = 1.0

    def schedule(self, card: Card, rating: int, now: datetime | None = None) -> ScheduleUpdate:
        now = now or _now()
        reps = card.reps
        lapses = card.lapses
        ease = card.ease
        interval = card.interval

        # SM-2 quality scale maps 0-5 to our 4-point rating.
        if rating == Rating.AGAIN:
            reps = 0
            lapses += 1
            ease = max(self.EASE_MIN, ease - 0.2)
            interval = self.DAY1
        else:
            reps += 1
            if reps == 1:
                interval = {Rating.HARD: 1.0, Rating.GOOD: 2.0, Rating.EASY: 4.0}[rating]
            elif reps == 2:
                interval = {Rating.HARD: 3.0, Rating.GOOD: 6.0, Rating.EASY: 9.0}[rating]
            else:
                ease_delta = {Rating.HARD: -0.14, Rating.GOOD: 0.0, Rating.EASY: 0.1}[rating]
                ease = max(self.EASE_MIN, min(self.EASE_MAX, ease + ease_delta))
                interval = max(self.DAY1, interval * ease)

        return ScheduleUpdate(
            interval=round(interval, 4),
            ease=round(ease, 4),
            reps=reps,
            lapses=lapses,
            due=_add_days(now, interval),
            last_reviewed_at=now,
        )


_SCHEDULERS: dict[str, Scheduler] = {
    FSRSScheduler.name: FSRSScheduler(),
    SM2Scheduler.name: SM2Scheduler(),
}


def get_scheduler(algorithm: str) -> Scheduler:
    """Resolve a scheduler by name. Falls back to FSRS (the default)."""
    try:
        return _SCHEDULERS[algorithm]
    except KeyError:
        raise ValueError(
            f"Unknown SRS algorithm {algorithm!r}. "
            f"Available: {sorted(_SCHEDULERS)}"
        ) from None


def schedule_review(card: Card, rating: int, now: datetime | None = None) -> ScheduleUpdate:
    """Convenience entry point used by the review API.

    Picks the scheduler from Card.srs_algorithm and applies it.
    """
    scheduler = get_scheduler(card.srs_algorithm)
    return scheduler.schedule(card, rating, now)


# A tiny guard so accidental log2(0) / division-by-zero paths can never
# surface as NaN intervals even if a future scheduler sets interval=0.
def _sanitize_interval(value: float) -> float:
    if not math.isfinite(value) or value <= 0:
        return 1.0
    return value
