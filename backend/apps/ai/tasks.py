"""Celery tasks for the AI analytics flows (Sprint 4).

Each task wraps a flow so heavy analytics can be scheduled and retried
asynchronously in production. In dev/test Celery runs eager (no Redis),
so `.delay()` is synchronous and flows can be unit-tested directly via
run_flow("report", ...).

Routing: tasks set `queue="ai"` so production deployments can scale AI
workers independently (per SDD 2.2). When CELERY_TASK_ALWAYS_EAGER is
True the queue setting is a no-op.
"""
from __future__ import annotations

import logging
from celery import shared_task
from django.contrib.auth import get_user_model

logger = logging.getLogger("apps.ai.tasks")


@shared_task(bind=True, queue="ai", max_retries=2)
def generate_report_task(self, user_id: int | None, language: str = "pt"):
    """Generate a personalized evolution report for the given user."""
    from apps.ai.services.orchestrator import run_flow

    User = get_user_model()
    user = User.objects.filter(pk=user_id).first() if user_id else None
    try:
        result = run_flow("report", {}, language=language, user=user)
        return _serialize_report_result(result)
    except Exception as exc:  # noqa: BLE001
        logger.exception("generate_report_task failed for user=%s: %s", user_id, exc)
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True, queue="ai", max_retries=2)
def generate_suggestions_task(self, user_id: int | None, top_k: int = 10):
    """Rank cards the user should review next, based on SRS state."""
    from apps.ai.services.orchestrator import run_flow

    User = get_user_model()
    user = User.objects.filter(pk=user_id).first() if user_id else None
    try:
        result = run_flow(
            "review_suggestion", {"top_k": top_k}, language="pt", user=user
        )
        return _serialize_suggestion_result(result)
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "generate_suggestions_task failed for user=%s: %s", user_id, exc
        )
        raise self.retry(exc=exc, countdown=30)


def _serialize_report_result(result) -> dict:
    """Convert a ReportResult dataclass to a JSON-serializable dict."""
    return {
        "user_id": result.user_id,
        "metrics": {
            "total_reviews": result.metrics.total_reviews,
            "total_lapses": result.metrics.total_lapses,
            "avg_reps": result.metrics.avg_reps,
            "last_review_at": result.metrics.last_review_at,
        },
        "text": result.text,
        "status": result.status,
        "prompt_version": result.prompt_version,
        "model": result.model,
        "provider": result.provider,
        "tokens_in": result.tokens_in,
        "tokens_out": result.tokens_out,
    }


def _serialize_suggestion_result(result) -> dict:
    """Convert a SuggestionResult dataclass to a JSON-serializable dict."""
    return {
        "user_id": result.user_id,
        "status": result.status,
        "hits": [
            {
                "card_id": hit.card_id,
                "deck_id": hit.deck_id,
                "deck_name": hit.deck_name,
                "front": hit.front,
                "reason": hit.reason,
                "due_in_seconds": hit.due_in_seconds,
            }
            for hit in result.hits
        ],
    }
