"""Celery application for MemorAI.

The app is named `memorai` (so `celery -A memorai worker` works) and reads
its settings from Django via settings.CELERY_BROKER_URL /
CELERY_RESULT_BACKEND.

When no broker is configured (dev/test on SQLite without Redis), the
settings set CELERY_TASK_ALWAYS_EAGER = True so `.delay()` and
.apply_async()` run synchronously. This keeps the dev loop frictionless
and lets tests exercise the task code paths without a broker.

Routing: all AI tasks default to the `ai` queue so that, in production,
the AI worker can be scaled independently from any future non-AI workers.
"""
from __future__ import annotations

import os

from celery import Celery

# Set default Django settings before instantiating Celery so the app can
# read CELERY_* settings lazily via `app.config_from_object("django.conf:settings")`.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "memorai.settings.dev")

app = Celery("memorai")

# Read config from Django settings but use the `CELERY_` namespace so we
# don't collide with Django keys.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover tasks in apps via autodiscover. We point at the apps that own
# tasks; this avoids scanning non-task apps and keeps startup tight.
app.autodiscover_tasks(["apps.ai"])


@app.task(bind=True)
def debug_task(self):  # pragma: no cover - utility for `celery inspect`
    """Print the executing task's request for debugging."""
    print(f"Request: {self.request!r}")
