"""Re-export the Celery app so `celery -A memorai worker ...` works.

The actual app lives in `config/celery.py` to keep the project package
(``memorai/``) thin and to match the SDD's `backend/config/celery.py`
layout.
"""
from config.celery import app as celery_app  # noqa: F401

__all__ = ("celery_app",)
