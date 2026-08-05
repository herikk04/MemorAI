"""Pytest configuration for the backend.

Uses the test settings module (in-memory SQLite, eager Celery) via the
DJANGO_SETTINGS_MODULE environment variable, and wires up the Django
postgresql database fixtures.
"""
import os

import django
from django.conf import settings


def pytest_configure(config):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "memorai.settings.test")
    if not settings.configured:
        django.setup()
