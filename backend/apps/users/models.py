"""Profile and auth auxiliary models for MemorAI.

The user identity itself stays in ``django.contrib.auth`` (``User``) so
existing FKs (e.g. ``flashcards.Review.user``) and Django admin keep
working unchanged. This app stores per-account metadata that does not
belong on the auth User table: preferred language, notification prefs
and audit hooks for the AI quota reset.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models


class Profile(models.Model):
    """One-to-one extension of ``auth.User`` with MemorAI preferences."""

    class Language(models.TextChoices):
        PT = "pt", "Portugues"
        EN = "en", "English"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="profile",
        on_delete=models.CASCADE,
    )
    language = models.CharField(
        max_length=2,
        choices=Language.choices,
        default=Language.PT,
    )
    # Day-of-month the daily AI quota resets is driven by
    # apps.ai.services.orchestrator; we only persist the user-visible
    # preference here so the report endpoint can reference it.
    notify_review_due = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Profile({self.user.username})"
