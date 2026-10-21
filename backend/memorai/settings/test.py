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
# Store eager results so AsyncResult(task_id) works in tests (polling path).
CELERY_TASK_STORE_EAGER_RESULT = True
# In-memory result backend so AsyncResult lookups resolve in eager mode.
CELERY_RESULT_BACKEND = "cache+memory://"

# Auth tests hit login/register many times from one client; the throttle has
# its own dedicated test (tests/test_auth_throttle.py) that lowers the rate.
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {"auth": "1000/min"}  # noqa: F405

# Cheaper AI defaults during tests (mock-friendly)
AI_CONFIG["default_model"] = "test-mock-model"
AI_CONFIG["provider"] = "mock"
# Force empty keys so tests never accidentally hit a real provider.
AI_CONFIG["openai_api_key"] = ""
AI_CONFIG["anthropic_api_key"] = ""
