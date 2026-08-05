"""Test settings — fast in-memory DB, eager Celery."""
from .base import *  # noqa: F401,F403
from .base import AI_CONFIG  # noqa: F401

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Cheaper AI defaults during tests (mock-friendly)
AI_CONFIG["default_model"] = "test-mock-model"
