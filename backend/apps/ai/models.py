"""Models for the AI core (apps.ai).

AIEvent: audit log of every LLM call (tokens, cost, latency, status).
AIUsage: per-(user, day) aggregate of tokens/cost used to enforce quotas.
Embedding: vector + metadata for cards/decks so RAG flows can do semantic
   search. Uses pgvector when running on PostgreSQL (with HNSW index for
   fast cosine similarity); falls back to a JSON list when on SQLite
   (dev/test) since pgvector needs the Postgres extension.

Design notes:
- We deliberately do NOT store raw prompt payloads or full completion text in
  AIEvent by default. The `prompt_hash` field lets us correlate repeated calls
  without persisting user content, preserving privacy. If the flow opts in
  (AuditConfig.keep_payload=True), the payload goes into a JSON field -- but
  the guardrails layer (safety/) is responsible for scrubbing PII before that.
- Cost is stored as a Decimal (USD) to avoid float drift on running totals.
- The Embedding.vector field stores dimensionality from AI_CONFIG["embedding_dim"]
  (default 1536 for text-embedding-3-small); changing it later requires migrating
  existing rows.
"""
from decimal import Decimal

from django.apps import apps as django_apps
from django.conf import settings
from django.db import connection, models


def _is_postgres() -> bool:
    """Detect at runtime whether the default DB engine is PostgreSQL.

    Cheap to call (reads connection.vendor). Used to switch the vector field
    type and to skip creating the ivfflat/hnsw index on SQLite.
    """
    try:
        return connection.vendor == "postgresql"
    except Exception:
        return False


def _vector_field_cls():
    """Return VectorField (pgvector) on PostgreSQL, JSONField on others.

    pgvector.django.VectorField requires the pgvector Postgres extension and
    the pgvector.django app in INSTALLED_APPS, both gated to Postgres in
    settings/base.py. On SQLite we store the embedding as a plain JSON list of
    floats so the same flow code can run in dev and tests.
    """
    if _is_postgres():
        from pgvector.django import VectorField

        return VectorField
    return models.JSONField


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


class Embedding(models.Model):
    """Vector + metadata for a card/deck so RAG flows can do semantic search.

    The vector column is a pgvector VectorField on Postgres (with HNSW index)
    and a plain JSON list on SQLite (dev/test), chosen at migration time via
    _vector_field_cls(). The Dim, model and version let us coordinate
    re-embeddings across the codebase dims; if AI_CONFIG changes, old rows
    keep their dim and dim/model so search can coalesce them.
    """

    class EntityType(models.TextChoices):
        CARD = "card", "Card"
        DECK = "deck", "Deck"

    entity_type = models.CharField(max_length=8, choices=EntityType.choices)
    entity_id = models.PositiveIntegerField()
    vector = _vector_field_cls()()
    model = models.CharField(max_length=64, default="")
    version = models.CharField(max_length=16, default="")
    dim = models.PositiveIntegerField(default=1536)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["model", "version"]),
        ]
        # One vector per (entity_type, entity_id, model, version) so
        # re-embedding with a new model doesn't overwrite the old rows.
        constraints = [
            models.UniqueConstraint(
                fields=["entity_type", "entity_id", "model", "version"],
                name="unique_embedding_per_entity_model_version",
            ),
        ]

    def __str__(self):
        return f"Embedding({self.entity_type}:{self.entity_id} dim={self.dim})"

    @classmethod
    def active_dim(cls) -> int:
        return getattr(settings, "AI_CONFIG", {}).get("embedding_dim", 1536)

    @classmethod
    def active_model(cls) -> str:
        return getattr(settings, "AI_CONFIG", {}).get(
            "embedding_model", "text-embedding-3-small"
        )


# Silence the unused-import warning for django_apps in linters; it is imported
# intentionally because pgvector.django must be a ready app before VectorField
# columns can be created, and importing apps here keeps the dependency explicit
# for readers tracing why the conditional registration matters.
_ = django_apps
