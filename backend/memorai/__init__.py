"""Memorai project package."""

from .celery import celery_app as app  # noqa: F401  (so `celery -A memorai worker` finds it)

__all__ = ("app",)
