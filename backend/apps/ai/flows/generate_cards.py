"""Assisted flashcard generation.

Given a topic (and optional source text/code) ask the LLM for a JSON array
of {front, back} cards. The flow only *proposes* cards: persisting them is
the caller's decision, so the learner can review before saving.

Unlike feedback there is no sensible deterministic fallback (we cannot invent
card content), so on LLM or parsing failure the result has no cards and a
non-success status; the UX is never blocked.
"""
from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any

from ..clients import LLMResponse, Message, get_llm_client
from ..models import AIEvent
from ..prompts.loader import load_prompt
from ..safety import sanitize_text
from ..services.orchestrator import _record_event, elapsed_ms

logger = logging.getLogger("apps.ai.flows.generate_cards")

MAX_COUNT = 10
_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


@dataclass
class GeneratedCard:
    front: str
    back: str


@dataclass
class GenerateCardsResult:
    cards: list[GeneratedCard] = field(default_factory=list)
    status: str = AIEvent.Status.SUCCESS
    tokens_in: int = 0
    tokens_out: int = 0
    model: str = ""
    provider: str = ""
    prompt_version: str = ""
    cost_usd: float = 0.0


def parse_cards(raw: str, limit: int) -> list[GeneratedCard]:
    """Extract valid, de-duplicated cards from the model output.

    Tolerates markdown fences and prose around the array. Raises ValueError
    when no JSON array can be found at all.
    """
    text = _FENCE.sub("", raw.strip())
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end <= start:
        raise ValueError("no JSON array in model output")
    items = json.loads(text[start : end + 1])
    if not isinstance(items, list):
        raise ValueError("model output is not a JSON array")

    cards: list[GeneratedCard] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        front, back = item.get("front"), item.get("back")
        if not (isinstance(front, str) and isinstance(back, str)):
            continue
        front, back = front.strip(), back.strip()
        key = front.casefold()
        if not front or not back or key in seen:
            continue
        seen.add(key)
        cards.append(GeneratedCard(front=front, back=back))
        if len(cards) >= limit:
            break
    return cards


def run_generate_cards(
    payload: dict[str, Any], *, language: str = "pt", user=None
) -> GenerateCardsResult:
    """Run the flow. Never raises for provider/parsing problems."""
    topic = str(payload.get("topic", "")).strip()
    if not topic:
        raise ValueError("generate_cards flow missing required key 'topic'")
    count = max(1, min(int(payload.get("count", 5) or 5), MAX_COUNT))

    # Mask PII-like content before it reaches the provider.
    safe_topic = sanitize_text(topic).text
    safe_source = sanitize_text(str(payload.get("source_text", "") or "")).text
    loaded = load_prompt(
        "generate_cards",
        language,
        {"topic": safe_topic, "count": count, "source_text": safe_source},
    )

    started = time.monotonic()
    try:
        client = get_llm_client()
        resp: LLMResponse = client.complete(
            messages=[
                Message(role="system", content=loaded.system),
                Message(role="user", content=loaded.user),
            ],
            temperature=0.4,
        )
        cards = parse_cards(resp.content or "", count)
        if not cards:
            raise ValueError("model returned no valid cards")
    except Exception as exc:  # noqa: BLE001  (broad on purpose: AI never blocks UX)
        logger.warning("generate_cards flow failed: %s", exc)
        _record_event(
            flow="generate_cards",
            prompt_version=loaded.version,
            model="",
            provider="",
            tokens_in=0,
            tokens_out=0,
            cost_usd=0.0,
            status=AIEvent.Status.FALLBACK,
            error=str(exc)[:256],
            user=user,
            latency_ms=elapsed_ms(started),
        )
        return GenerateCardsResult(status=AIEvent.Status.FALLBACK, prompt_version=loaded.version)

    _record_event(
        flow="generate_cards",
        prompt_version=loaded.version,
        model=resp.model,
        provider=resp.provider,
        tokens_in=resp.tokens_in,
        tokens_out=resp.tokens_out,
        cost_usd=resp.cost_usd or 0.0,
        status=AIEvent.Status.SUCCESS,
        error="",
        user=user,
        latency_ms=elapsed_ms(started),
    )
    return GenerateCardsResult(
        cards=cards,
        status=AIEvent.Status.SUCCESS,
        tokens_in=resp.tokens_in,
        tokens_out=resp.tokens_out,
        model=resp.model,
        provider=resp.provider,
        prompt_version=loaded.version,
        cost_usd=resp.cost_usd or 0.0,
    )
