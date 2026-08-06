"""Feedback flow.

Given a card review (front/back of the flashcard plus the rating the
learner gave) produce a short personalized explanation. The orchestrator
calls this via run_flow("feedback", payload).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ..clients import LLMResponse, Message, get_llm_client
from ..models import AIEvent
from ..prompts.loader import load_prompt

logger = logging.getLogger("apps.ai.flows.feedback")

RATING_LABELS = {1: "Again", 2: "Hard", 3: "Good", 4: "Easy"}


@dataclass
class FeedbackResult:
    text: str
    tokens_in: int
    tokens_out: int
    model: str
    provider: str
    status: str
    prompt_version: str
    cost_usd: float


def _fallback(payload: dict[str, Any]) -> str:
    """Deterministic fallback when the LLM is unavailable.

    Per the SDD (sec 3.2): the AI never blocks the UX. We produce a short,
    rule-based explanation so the review endpoint still returns something
    useful even if OPENAI_API_KEY is empty or the provider times out.
    """
    rating = payload.get("rating")
    label = RATING_LABELS.get(rating, "review")
    front = payload.get("front", "")
    lapses = int(payload.get("lapses", 0) or 0)
    if rating == 1 or lapses > 2:
        tail = "Revise este card com mais frequencia; ele entrou em lapso."
    elif rating == 2:
        tail = "Bom reforco: vale repetir logo para fixar."
    else:
        tail = "Voce dominou este card; pode espacar as revisoes."
    return f"[heuristic:{label}] {front[:80]} ... {tail}"


def run_feedback(
    payload: dict[str, Any],
    *,
    language: str = "pt",
    user=None,
) -> FeedbackResult:
    """Run the feedback flow. Always returns FeedbackResult, never raises.

    On any LLM error we record an AIEvent with status=fallback/error/timeout
    and return a deterministic explanation so callers can keep going.
    """
    from ..services.orchestrator import _record_event  # local import to avoid cycle

    # Validate the minimum required input early.
    for key in ("front", "back", "rating"):
        if key not in payload:
            raise ValueError(f"feedback flow missing required key {key!r}")

    rating = int(payload["rating"])
    prompt_payload = {
        "front": payload["front"],
        "back": payload["back"],
        "rating_label": RATING_LABELS.get(rating, "Review"),
        "time_ms": int(payload.get("time_ms", 0) or 0),
        "reps": int(payload.get("reps", 0) or 0),
        "lapses": int(payload.get("lapses", 0) or 0),
    }
    loaded = load_prompt("feedback", language, prompt_payload)

    try:
        client = get_llm_client()
        llm_resp: LLMResponse = client.complete(
            messages=[
                Message(role="system", content=loaded.system),
                Message(role="user", content=loaded.user),
            ],
        )
    except Exception as exc:  # noqa: BLE001  (we want broad fallback here)
        logger.warning("feedback flow fell back to heuristic: %s", exc)
        text = _fallback(prompt_payload)
        status = (
            AIEvent.Status.FALLBACK if isinstance(exc, Exception) else AIEvent.Status.ERROR
        )
        _record_event(
            flow="feedback",
            prompt_version=loaded.version,
            model="",
            provider="",
            tokens_in=0,
            tokens_out=0,
            cost_usd=0.0,
            status=status,
            error=str(exc)[:256],
            user=user,
        )
        return FeedbackResult(
            text=text,
            tokens_in=0,
            tokens_out=0,
            model="",
            provider="",
            status=status,
            prompt_version=loaded.version,
            cost_usd=0.0,
        )

    status = AIEvent.Status.SUCCESS
    _record_event(
        flow="feedback",
        prompt_version=loaded.version,
        model=llm_resp.model,
        provider=llm_resp.provider,
        tokens_in=llm_resp.tokens_in,
        tokens_out=llm_resp.tokens_out,
        cost_usd=llm_resp.cost_usd or 0.0,
        status=status,
        error="",
        user=user,
    )

    return FeedbackResult(
        text=llm_resp.content or _fallback(prompt_payload),
        tokens_in=llm_resp.tokens_in,
        tokens_out=llm_resp.tokens_out,
        model=llm_resp.model,
        provider=llm_resp.provider,
        status=status,
        prompt_version=loaded.version,
        cost_usd=llm_resp.cost_usd or 0.0,
    )
