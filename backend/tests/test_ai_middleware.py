"""Tests for the AI quota middleware (Sprint 2 - 7/7)."""
from __future__ import annotations

import datetime as _dt
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.ai.models import AIUsage


class FeedbackQuotaMiddlewareTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/v1/ai/feedback/"
        self.payload = {"front": "q", "back": "a", "rating": 3}

    def test_anonymous_passes_through(self):
        resp = self.client.post(self.url, self.payload, format="json")
        # Mock provider will run and return 200.
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_authenticated_normal_quota_returns_200(self):
        User = get_user_model()
        u = User.objects.create_user(username="q1", password="pw1234567")
        self.client.force_authenticate(u)
        resp = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_authenticated_exhausted_returns_429(self):
        User = get_user_model()
        u = User.objects.create_user(username="q2", password="pw1234567")
        self.client.force_authenticate(u)
        caps = AIUsage.caps()
        # Burn the full token cap today so the middleware blocks.
        AIUsage.objects.create(
            user=u,
            day=_dt.date.today(),
            tokens_in=caps["tokens"],
            tokens_out=0,
            cost_usd=Decimal("0"),
            calls=1,
        )
        resp = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        body = resp.json()
        self.assertIn(body["reason"], {"daily_token_cap_per_user", "daily_cost_cap_usd"})

    def test_authenticated_cost_exhausted_returns_429(self):
        User = get_user_model()
        u = User.objects.create_user(username="q3", password="pw1234567")
        self.client.force_authenticate(u)
        caps = AIUsage.caps()
        # Burn the full cost cap today.
        AIUsage.objects.create(
            user=u,
            day=_dt.date.today(),
            tokens_in=0,
            tokens_out=0,
            cost_usd=Decimal(str(caps["cost_usd"])),
            calls=1,
        )
        resp = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(resp.json()["reason"], "daily_cost_cap_usd")
