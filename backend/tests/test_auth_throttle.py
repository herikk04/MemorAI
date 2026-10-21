"""Login and register are rate limited per client (brute-force protection)."""
from __future__ import annotations

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle


@pytest.fixture(autouse=True)
def low_rate(monkeypatch):
    cache.clear()
    monkeypatch.setattr(ScopedRateThrottle, "THROTTLE_RATES", {"auth": "3/min"})
    yield
    cache.clear()


@pytest.mark.django_db
def test_login_is_throttled_after_repeated_attempts():
    client = APIClient()
    codes = [
        client.post("/api/v1/auth/login/", {"username": "x", "password": "y"}).status_code
        for _ in range(5)
    ]
    assert codes[:3] == [401, 401, 401]
    assert codes[3:] == [429, 429]


@pytest.mark.django_db
def test_register_is_throttled():
    client = APIClient()
    codes = [
        client.post("/api/v1/auth/register/", {"username": "", "password": ""}).status_code
        for _ in range(4)
    ]
    assert codes[-1] == 429
