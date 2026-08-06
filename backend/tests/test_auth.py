"""Sprint 1.5 — auth via SimpleJWT (login, refresh, verify, 401 base).

Covers the /api/v1/auth/ surface and the agent that auth is now enforced
on the rest of the API. Flows that take a user object are still tested
via internal calls (run_report / run_review_suggestion) in their own
test modules; this file focuses on the HTTP surface.
"""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def credentials():
    return {"username": "auth-user", "password": "pw1234567"}


@pytest.fixture
def user(credentials):
    return User.objects.create_user(**credentials)


@pytest.fixture
def client():
    return APIClient()


class TestLogin:
    @pytest.mark.django_db
    def test_login_returns_token_pair_and_profile(self, client, user, credentials):
        resp = client.post("/api/v1/auth/login/", credentials, format="json")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert "access" in body
        assert "refresh" in body
        assert body["user_id"] == user.id
        assert body["username"] == user.get_username()
        # No profile row yet -> default language code is "pt".
        assert body["language"] == "pt"

    @pytest.mark.django_db
    def test_login_attaches_profile_language(self, client, credentials):
        user = User.objects.create_user(**credentials)
        from apps.users.models import Profile

        Profile.objects.create(user=user, language=Profile.Language.EN)
        resp = client.post("/api/v1/auth/login/", credentials, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["language"] == "en"

    @pytest.mark.django_db
    def test_login_wrong_password_rejected(self, client, user, credentials):
        bad = dict(credentials, password="wrong")
        resp = client.post("/api/v1/auth/login/", bad, format="json")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert "access" not in resp.json()


class TestRefreshAndVerify:
    @pytest.mark.django_db
    def test_refresh_rotates_and_blacklists_old(self, client, user, credentials):
        login = client.post("/api/v1/auth/login/", credentials, format="json")
        old_refresh = login.json()["refresh"]
        resp = client.post(
            "/api/v1/auth/refresh/", {"refresh": old_refresh}, format="json"
        )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert "access" in body
        assert body["refresh"] != old_refresh  # rotation

        # Old refresh is now blacklisted and cannot be reused.
        again = client.post(
            "/api/v1/auth/refresh/", {"refresh": old_refresh}, format="json"
        )
        assert again.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_verify_endpoint_accepts_access(self, client, user, credentials):
        login = client.post("/api/v1/auth/login/", credentials, format="json")
        access = login.json()["access"]
        resp = client.post("/api/v1/auth/verify/", {"token": access}, format="json")
        assert resp.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_verify_rejects_garbage(self, client):
        resp = client.post(
            "/api/v1/auth/verify/", {"token": "not-a-token"}, format="json"
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestJwtAuthenticationOnApi:
    """Bearer-token auth should let authenticated clients through."""

    @pytest.mark.django_db
    def test_bearer_token_unlocks_feedback(self, client, user, credentials):
        from apps.ai.models import AIEvent

        login = client.post("/api/v1/auth/login/", credentials, format="json")
        access = login.json()["access"]
        before = AIEvent.objects.count()
        resp = client.post(
            "/api/v1/ai/feedback/",
            {"front": "q", "back": "a", "rating": 3, "language": "pt"},
            HTTP_AUTHORIZATION=f"Bearer {access}",
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert AIEvent.objects.count() == before + 1

    @pytest.mark.django_db
    def test_malformed_bearer_returns_401(self, client):
        resp = client.post(
            "/api/v1/ai/feedback/",
            {"front": "q", "back": "a", "rating": 3},
            HTTP_AUTHORIZATION="Bearer not-a-token",
            format="json",
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestProfileAutoCreated:
    @pytest.mark.django_db
    def test_user_can_create_pack_link_via_admin_signal_optional(
        self, client, user, credentials
    ):
        # Profiles are created on demand by the serializer / API; a login
        # without an explicit Profile row should still succeed (Sprint 1.5
        # does not require a default Profile per user).
        from apps.users.models import Profile

        assert not Profile.objects.filter(user=user).exists()
        resp = client.post("/api/v1/auth/login/", credentials, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["language"] == "pt"
