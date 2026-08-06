"""AI orchestrator: single entry point for the rest of the codebase.

apps.ai.services.orchestrator.run_flow(name, payload, language, user)
is the only function other apps should call. It dispatches to a flow
module in apps/ai/flows/{name}.py (which must expose run_{name}(payload,
language=..., user=...) and record its own AIEvent rows via the helper
_record_event defined here).

This is the boundary that protects the rest of the system from the AI
internals: if we ever swap how AIEvent / AIUsage are written (e.g. via
Celery in Sprint 4) only this module changes.
"""
from __future__ import annotations

import datetime as _dt
import importlib
import logging
from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from ..models import AIEvent, AIUsage

logger = logging.getLogger("apps.ai")


def run_flow(name: str, payload: dict[str, Any], *, language: str = "pt", user=None):
    """Dispatch to apps.ai.flows.{name}.run_{name}(payload, language, user).

    Returns whatever the flow returns (typically a dataclass). Raises
    ValueError for unknown flow names; flow-specific errors surface as
    their own exceptions per each flow's contract.
    """
    module_path = f"apps.ai.flows.{name}"
    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise ValueError(f"Unknown AI flow {name!r}") from exc

    func_name = f"run_{name}"
    func = getattr(module, func_name, None)
    if func is None:
        raise ValueError(f"Flow {name!r} has no callable {func_name!r}")
    return func(payload, language=language, user=user)


@transaction.atomic
def _record_event(
    *,
    flow: str,
    prompt_version: str,
    model: str,
    provider: str,
    tokens_in: int,
    tokens_out: int,
    cost_usd: float,
    status: str,
    error: str,
    user,
) -> AIEvent:
    """Persist an AIEvent and roll up into AIUsage (quotas).

    Called only by flow modules after each LLM call (success or fallback).
    Transaction-wrapped so an AIUsage update never happens without the
    matching AIEvent row.
    """
    User = get_user_model()
    user_obj = user if (user is not None and isinstance(user, User)) else None

    cost = Decimal(str(cost_usd or 0.0)).quantize(Decimal("0.000001"))
    event = AIEvent.objects.create(
        user=user_obj,
        flow=flow,
        prompt_version=prompt_version,
        model=model,
        provider=provider,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost,
        latency_ms=0,  # filled by a wrapper when added in Sprint 4
        status=status,
        error=error,
    )

    if user_obj is not None:
        _bump_usage(user_obj, tokens_in, tokens_out, cost)
    return event


def _bump_usage(user, tokens_in: int, tokens_out: int, cost: Decimal) -> None:
    day = _dt.date.today()
    usage, _ = AIUsage.objects.get_or_create(user=user, day=day)
    usage.tokens_in += tokens_in
    usage.tokens_out += tokens_out
    usage.cost_usd += cost
    usage.calls += 1
    usage.save()


def quota_remaining(user) -> dict[str, float]:
    """Returns remaining tokens and cost for the current day (for middleware)."""
    if user is None or not user.is_authenticated:
        return {"tokens": float("inf"), "cost_usd": float("inf")}
    day = timezone.now().date()
    try:
        usage = AIUsage.objects.get(user=user, day=day)
    except AIUsage.DoesNotExist:
        usage = None
    caps = AIUsage.caps()
    used_tokens = (usage.tokens_in + usage.tokens_out) if usage else 0
    used_cost = float(usage.cost_usd) if usage else 0.0
    return {
        "tokens": max(0.0, float(caps["tokens"]) - used_tokens),
        "cost_usd": max(0.0, float(caps["cost_usd"]) - used_cost),
    }


def quota_exceeded(user) -> tuple[bool, str | None]:
    """Returns (exceeded, reason) for the AI middleware to enforce caps."""
    if user is None or not user.is_authenticated:
        return (False, None)
    rem = quota_remaining(user)
    if rem["tokens"] <= 0:
        return (True, "daily_token_cap_per_user")
    if rem["cost_usd"] <= 0:
        return (True, "daily_cost_cap_usd")
    return (False, None)
