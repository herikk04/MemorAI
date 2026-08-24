"""Integration test for the /api/v1/ai/feedback/ endpoint."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.ai.models import AIEvent


class FeedbackEndpointTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/v1/ai/feedback/"
        # Sprint 1.5: all AI endpoints require an authenticated user.
        User = get_user_model()
        self.user = User.objects.create_user(
            username="ai-endpoint", password="pw1234567"
        )
        self.client.force_authenticate(self.user)

    def test_happy_path(self):
        events_before = AIEvent.objects.count()
        resp = self.client.post(
            self.url,
            {
                "front": "Qual a saida de print([1,2]+[3])",
                "back": "[1, 2, 3]",
                "rating": 1,
                "time_ms": 8500,
                "reps": 4,
                "lapses": 2,
                "language": "pt",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        body = resp.json()
        self.assertIn("text", body)
        self.assertTrue(body["text"])
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["prompt_version"], "1.0")
        self.assertEqual(body["provider"], "mock")
        # AIEvent recorded by the flow's audit hook.
        self.assertEqual(AIEvent.objects.count(), events_before + 1)

    def test_missing_required_field_rejected(self):
        resp = self.client.post(self.url, {"back": "x", "rating": 1}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rating_out_of_range_rejected(self):
        resp = self.client.post(
            self.url,
            {"front": "q", "back": "a", "rating": 5},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_request_rejected(self):
        self.client.force_authenticate(None)
        resp = self.client.post(
            self.url,
            {"front": "q", "back": "a", "rating": 3},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_updates_usage(self):
        from apps.ai.models import AIUsage

        before = AIUsage.objects.filter(user=self.user).count()
        resp = self.client.post(
            self.url,
            {"front": "q", "back": "a", "rating": 3},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        after = AIUsage.objects.filter(user=self.user).count()
        self.assertEqual(after, before + 1)
