"""Pytest configuration for the backend.

Uses the test settings module (in-memory SQLite, eager Celery) via the
DJANGO_SETTINGS_MODULE environment variable, and wires up the Django
postgresql database fixtures.
"""
import os
import sys
from pathlib import Path

import django
from django.conf import settings

# Make backend/apps/ importable as a top-level namespace, mirroring the logic
# in manage.py / wsgi.py / asgi.py.
_APPS_DIR = str(Path(__file__).resolve().parent.parent / "apps")
if _APPS_DIR not in sys.path:
    sys.path.insert(0, _APPS_DIR)


def pytest_configure(config):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "memorai.settings.test")
    if not settings.configured:
        django.setup()
