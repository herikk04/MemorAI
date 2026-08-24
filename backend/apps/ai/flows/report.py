"""Report flow: personalized evolution summary.

Computes user-level SRS metrics over their Reviews, fills a prompt and
calls the LLM to produce a concise progress report. Used by the Celery
task `generate_report_task`; can also be called directly (eager in
dev/test).

Always returns a ReportResult; on LLM failure we still return the
metrics with a heuristic paragraph and status=fallback, so the user
never sees a broken report.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Max, Sum

from ..clients import LLMResponse, Message, get_llm_client
from ..models import AIEvent
from ..prompts.loader import load_prompt
from ..services.orchestrator import _record_event

logger = logging.getLogger("apps.ai.flows.report")


@dataclass
class ReportMetrics:
    total_reviews: int
    total_lapses: int
    avg_reps: float
    last_review_at: str


@dataclass
class ReportResult:
    user_id: int | None
    metrics: ReportMetrics
    text: str
    status: str
    prompt_version: str
    model: str
    provider: str
    tokens_in: int
    tokens_out: int
    error: str = ""


def _heuristic_report(metrics: ReportMetrics, user_id: int | None) -> str:
    """Deterministic fallback when the LLM is unavailable."""
    if metrics.total_reviews == 0:
        return "[heuristic] Voce ainda nao tem revisoes registradas. Comece revisando um card."
    ret = f"[heuristic] Total de revisoes: {metrics.total_reviews}. Lapsos: {metrics.total_lapses}. Repeticoes medias: {metrics.avg_reps:.1f}."
    if metrics.total_lapses == 0:
        ret += " Bom aproveitamento: nenhum lapso."
    elif metrics.total_lapses > metrics.total_reviews * 0.3:
        ret += " Muitos lapsos relativos ao volume; vale revisar cards mais cedo."
    return ret


def _gather_metrics(user) -> tuple[ReportMetrics, list[Any]]:
    """Return (metrics, sample_reviews) for the user.

    Returns an empty ReportMetrics with zero counts when the user is
    anonymous (no auth yet) or when there are no reviews. We never
    blow up on missing data.
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return (
            ReportMetrics(0, 0, 0.0, ""),
            [],
        )

    from flashcards.models import Review

    qs = Review.objects.filter(user=user)
    agg = qs.aggregate(
        total=Count("id"),
        lapses=Sum("card__lapses"),
        avg_reps=Avg("card__reps"),
        last=Max("reviewed_at"),
    )
    total = int(agg["total"] or 0)
    lapses = int(agg["lapses"] or 0)
    avg_reps = float(agg["avg_reps"] or 0.0)
    last = agg["last"]
    last_str = last.isoformat() if last else ""
    return (
        ReportMetrics(
            total_reviews=total,
            total_lapses=lapses,
            avg_reps=round(avg_reps, 2),
            last_review_at=last_str,
        ),
        list(qs.select_related("card")[:10]),
    )


def run_report(payload: dict[str, Any], *, language: str = "pt", user=None) -> ReportResult:
    """Run the report flow. Never raises."""
    User = get_user_model()
    user_obj = user if (user is not None and isinstance(user, User)) else None

    metrics, _ = _gather_metrics(user_obj or user)

    if metrics.total_reviews == 0:
        # No data yet -> skip the LLM and return a heuristic right away.
        return ReportResult(
            user_id=getattr(user_obj, "id", None) or getattr(user, "id", None),
            metrics=metrics,
            text=_heuristic_report(metrics, getattr(user_obj, "id", None)),
            status=AIEvent.Status.FALLBACK,
            prompt_version="",
            model="",
            provider="",
            tokens_in=0,
            tokens_out=0,
        )

    prompt_payload = {
        "total_reviews": metrics.total_reviews,
        "total_lapses": metrics.total_lapses,
        "avg_reps": f"{metrics.avg_reps:.1f}",
        "last_review_at": metrics.last_review_at,
    }
    loaded = load_prompt("report", language, prompt_payload)

    try:
        client = get_llm_client()
        llm_resp: LLMResponse = client.complete(
            messages=[
                Message(role="system", content=loaded.system),
                Message(role="user", content=loaded.user),
            ],
        )
        text = llm_resp.content
        status = AIEvent.Status.SUCCESS
        error = ""
    except Exception as exc:  # noqa: BLE001
        logger.warning("report flow fell back: %s", exc)
        text = _heuristic_report(metrics, getattr(user_obj, "id", None))
        status = AIEvent.Status.FALLBACK
        llm_resp = None
        error = str(exc)[:256]

    _record_event(
        flow="report",
        prompt_version=loaded.version,
        model=(llm_resp.model if llm_resp else ""),
        provider=(llm_resp.provider if llm_resp else ""),
        tokens_in=(llm_resp.tokens_in if llm_resp else 0),
        tokens_out=(llm_resp.tokens_out if llm_resp else 0),
        cost_usd=(llm_resp.cost_usd or 0.0 if llm_resp else 0.0),
        status=status,
        error=error,
        user=user_obj,
    )

    return ReportResult(
        user_id=getattr(user_obj, "id", None),
        metrics=metrics,
        text=text or _heuristic_report(metrics, getattr(user_obj, "id", None)),
        status=status,
        prompt_version=loaded.version,
        model=llm_resp.model if llm_resp else "",
        provider=llm_resp.provider if llm_resp else "",
        tokens_in=llm_resp.tokens_in if llm_resp else 0,
        tokens_out=llm_resp.tokens_out if llm_resp else 0,
        error=error,
    )
