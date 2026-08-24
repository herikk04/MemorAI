"""Safety layer for the AI core.

The guardrails layer sits between the flow layer and the LLM client:
flows format prompts and then call sanitize_inputs() so that visibly
PII-like content (emails, credit-card-shaped numbers) is masked before
the payload reaches the provider. The orchestrator wraps the provider
call so the masked text is what gets logged/sent, and the original is
never persisted outside the app's own controlled stores (Card/Review).

This is intentionally a regex-based, cheap sanitizer. A heavier
moderation pass (call to a moderation API) is a later sprint and would
plug into the same `moderate()` hook.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger("apps.ai.safety")

# Patterns run in order; phone/cpf/email are more specific and must run
# before the more permissive card regex, which would otherwise consume the
# digits of phone numbers. Anchored with word boundaries; card regex forbids
# the leading "+" so phone numbers are never matched as cards.
_EMAIL = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
# Brazilian phone-ish with country code: +55 11 9xxxx-xxxx (optional spaces/dashes)
_PHONE = re.compile(r"\+55\s?\(?\d{2}\)?\s?9?\s?\d{4,5}-?\d{4}")
# Brazilian CPF-ish: 000.000.000-00 (lenient on verification digits)
_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
# Card-like: 13 to 19 digits, optionally separated by space/dash. Does NOT
# match strings starting with "+" so phones don't trigger it.
_CARD = re.compile(r"(?<!\+)(?<!\d[ -])\b(?:\d[ -]?){12,18}\d\b")

_PATTERNS = (
    ("email", _EMAIL, "[email-masked]"),
    ("phone", _PHONE, "[phone-masked]"),
    ("cpf", _CPF, "[cpf-masked]"),
    ("card", _CARD, "[card-masked]"),
)


@dataclass(frozen=True)
class SanitizationResult:
    text: str
    masked: list[str]  # names of patterns that triggered


def sanitize_text(text: str) -> SanitizationResult:
    """Mask PII-like substrings in `text`. Idempotent on already-masked text."""
    masked_found: list[str] = []
    out = text
    for name, pattern, replacement in _PATTERNS:
        new, count = pattern.subn(replacement, out)
        if count:
            masked_found.append(name)
            out = new
    return SanitizationResult(text=out, masked=masked_found)


def sanitize_inputs(payload: dict) -> dict:
    """Sanitize all string values in `payload` in place; returns the dict.

    Non-string values are left untouched. We log which PII categories were
    masked (without their original values) at INFO so the AIEvent audit
    trail can show whether the prompt was sanitised without persisting PII.
    """
    masked_summary: list[str] = []
    for key, value in payload.items():
        if isinstance(value, str):
            result = sanitize_text(value)
            if result.masked:
                masked_summary.extend(f"{key}:{m}" for m in result.masked)
                payload[key] = result.text
    if masked_summary:
        logger.info("sanitize_inputs masked PII: %s", ",".join(masked_summary))
    return payload


def moderate(text: str) -> str:
    """Future hook for content moderation. For now returns text unchanged."""
    return text
