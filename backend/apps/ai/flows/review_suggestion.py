"""Review-suggestion flow (Sprint 4).

Prioritises cards the user should review next based on SRS state.
Primary driver is the card's `due` field — overdue cards come first,
then cards closest to due, then cards with more lapses and fewer reps
(weakest retention).

This flow is heuristic-driven and intentionally does NOT call the LLM;
it returns a ranked list that the UI can render directly. A later
sprint can attach an LLM explanation per suggestion via a separate
flow (e.g. suggestion_explain) without changing this contract.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import F
from django.utils import timezone

from ..models import AIEvent

logger = logging.getLogger("apps.ai.flows.review_suggestion")


@dataclass
class SuggestionHit:
    card_id: int
    deck_id: int
    deck_name: str
    front: str
    reason: str  # short deterministic reason text
    due_in_seconds: int  # <0 = overdue; seconds until due otherwise


@dataclass
class SuggestionResult:
    user_id: int | None
    status: str
    hits: list[SuggestionHit] = field(default_factory=list)


def _reason(due_in_seconds: int, lapses: int) -> str:
    if due_in_seconds < 0:
        return "Vencido: nivel de prioridade maximo para retencao."
    if due_in_seconds < 24 * 3600:
        return "Vence em breve: revisar agora mantem o intervalo."
    if lapses >= 3:
        return "Card com muitos lapses: vale revisar para fixar."
    return "Card em manutencao: revisao preventiva."


def run_review_suggestion(
    payload: dict[str, Any], *, language: str = "pt", user=None
) -> SuggestionResult:
    """Return a ranked list of cards to review. Never raises."""
    User = get_user_model()
    user_obj = user if (user is not None and isinstance(user, User)) else None
    if user_obj is None or not getattr(user_obj, "is_authenticated", False):
        # Anonymous: no SRS history tied to a user; return empty list.
        return SuggestionResult(user_id=None, status=AIEvent.Status.SUCCESS, hits=[])

    top_k = int(payload.get("top_k", 10) or 10)
    now = timezone.now()

    from flashcards.models import Card

    # Cards the user owns via Review. We pull deck_name via select_related.
    # Order: due NULL last, due ASC (most overdue first), lapses DESC, reps ASC.
    cards = (
        Card.objects.filter(reviews__user=user_obj)
        .distinct()
        .select_related("deck")
        .order_by(F("due").asc(nulls_last=True), "-lapses", "reps")
    )

    hits: list[SuggestionHit] = []
    seen: set[int] = set()
    for card in cards:
        if card.id in seen:
            continue
        seen.add(card.id)
        due_in_seconds = 0
        if card.due is not None:
            delta = card.due - now
            due_in_seconds = int(delta.total_seconds())
            # If overdue, due_in_seconds goes negative.
            if due_in_seconds > 0 and due_in_seconds > 7 * 24 * 3600:
                # Skip cards that aren't due for a week to keep the list
                # useful for "what to do right now" use cases.
                continue
        hits.append(
            SuggestionHit(
                card_id=card.id,
                deck_id=card.deck_id,
                deck_name=card.deck.name,
                front=card.front,
                reason=_reason(due_in_seconds, card.lapses),
                due_in_seconds=due_in_seconds,
            )
        )
        if len(hits) >= top_k:
            break

    # Audit (lightweight): one AIEvent per suggestion flow call.
    AIEvent.objects.create(
        user=user_obj,
        flow="review_suggestion",
        prompt_version="",  # heuristic flow; no YAML prompt
        model="",  # noqa: no LLM call
        provider="heuristic",
        tokens_in=0,
        tokens_out=0,
        cost_usd=0,
        latency_ms=0,
        status=AIEvent.Status.SUCCESS,
        error="",
    )

    return SuggestionResult(user_id=user_obj.id, status=AIEvent.Status.SUCCESS, hits=hits)
