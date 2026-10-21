"""POST /api/v1/auth/register/: account creation with auto-login."""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

URL = "/api/v1/auth/register/"
User = get_user_model()


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
def test_register_creates_user_profile_and_tokens(client):
    resp = client.post(
        URL,
        {"username": "novo", "password": "s3nha-forte-123", "language": "en"},
        format="json",
    )
    assert resp.status_code == status.HTTP_201_CREATED
    body = resp.json()
    assert body["username"] == "novo"
    assert body["language"] == "en"
    assert body["access"] and body["refresh"]
    assert User.objects.get(username="novo").profile.language == "en"


@pytest.mark.django_db
def test_register_token_works_on_protected_endpoint(client):
    body = client.post(
        URL, {"username": "tok", "password": "s3nha-forte-123"}, format="json"
    ).json()
    resp = client.get("/api/v1/decks/", HTTP_AUTHORIZATION=f"Bearer {body['access']}")
    assert resp.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_register_rejects_duplicate_username_case_insensitive(client):
    User.objects.create_user(username="Dup", password="pw1234567")
    resp = client.post(
        URL, {"username": "dup", "password": "s3nha-forte-123"}, format="json"
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "username" in resp.json()


@pytest.mark.django_db
def test_register_rejects_weak_password(client):
    resp = client.post(URL, {"username": "weak", "password": "123"}, format="json")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert not User.objects.filter(username="weak").exists()
