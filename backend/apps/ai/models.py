"""Models for the AI core (apps.ai).

AIEvent: audit log of every LLM call (tokens, cost, latency, status).
AIUsage: per-(user, day) aggregate of tokens/cost used to enforce quotas.

Design notes:
- We deliberately do NOT store raw prompt payloads or full completion text in
  AIEvent by default. The `prompt_hash` field lets us correlate repeated calls
  without persisting user content, preserving privacy. If the flow opts in
  (AuditConfig.keep_payload=True), the payload goes into a JSON field — but the
  guardrails layer (safety/) is responsible for scrubbing PII before that.
- Cost is stored as a Decimal (USD) to avoid float drift on running totals.
"""
from decimal import Decimal

from django.conf import settings
from django.db import models


class AIEvent(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "success", "Success"
        ERROR = "error", "Error"
        TIMEOUT = "timeout", "Timeout"
        FALLBACK = "fallback", "Fallback (heuristic)"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="ai_events",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    flow = models.CharField(max_length=64, help_text="e.g. 'feedback'")
    prompt_version = models.CharField(max_length=32, blank=True, default="")
    model = models.CharField(max_length=64, blank=True, default="")
    provider = models.CharField(max_length=32, blank=True, default="")
    tokens_in = models.PositiveIntegerField(default=0)
    tokens_out = models.PositiveIntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal("0"))
    latency_ms = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SUCCESS)
    error = models.CharField(max_length=256, blank=True, default="")
    # SHA256 of (prompt_name + version + inputs), used to dedupe without
    # storing user content. The orchestrator computes it.
    prompt_hash = models.CharField(max_length=64, blank=True, default="", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["flow", "-created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"AIEvent({self.flow}/{self.status}@{self.created_at:%Y-%m-%d %H:%M})"


class AIUsage(models.Model):
    """Per-(user, day) running total to enforce AI_DAILY_*_CAP quotas."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="ai_usage_daily",
        on_delete=models.CASCADE,
    )
    day = models.DateField()
    tokens_in = models.PositiveIntegerField(default=0)
    tokens_out = models.PositiveIntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal("0"))
    calls = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("user", "day")]
        ordering = ["-day"]

    def __str__(self):
        return f"AIUsage({self.user_id}/{self.day}: {self.calls} calls, ${self.cost_usd})"

    @classmethod
    def caps(cls):
        """Per-user daily caps, read from settings.AI_CONFIG (set in base.py)."""
        return {
            "tokens": getattr(settings, "AI_CONFIG", {}).get(
                "daily_token_cap_per_user", 200_000
            ),
            "cost_usd": float(
                getattr(settings, "AI_CONFIG", {}).get("daily_cost_cap_usd", 10.0)
            ),
        }
