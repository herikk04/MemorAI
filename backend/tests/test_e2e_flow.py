"""End-to-end API flow: register -> deck -> card -> due -> review -> dashboard."""
from __future__ import annotations

import pytest
from rest_framework.test import APIClient

API = "/api/v1"


@pytest.mark.django_db
def test_new_user_can_study_a_card_end_to_end():
    client = APIClient()

    tokens = client.post(
        f"{API}/auth/register/",
        {"username": "aluno", "password": "s3nha-forte-123"},
        format="json",
    ).json()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    deck = client.post(f"{API}/decks/", {"name": "Python"}, format="json").json()
    card = client.post(
        f"{API}/cards/",
        {"deck": deck["id"], "front": "O que é uma list?", "back": "Sequência mutável"},
        format="json",
    ).json()

    # A brand-new card is immediately in the review queue.
    due = client.get(f"{API}/cards/due/").json()
    assert [c["id"] for c in due] == [card["id"]]
    assert client.get(f"{API}/dashboard/").json()["due_count"] == 1

    resp = client.post(f"{API}/cards/{card['id']}/review/", {"rating": 3}, format="json")
    assert resp.status_code == 201
    assert resp.json()["card"]["due"] is not None

    # After the review the card leaves the queue and the dashboard reflects it.
    assert client.get(f"{API}/cards/due/").json() == []
    stats = client.get(f"{API}/dashboard/").json()
    assert stats["due_count"] == 0
    assert stats["reviewed_today"] == 1
    assert stats["streak_days"] == 1
    assert stats["decks"][0]["learned_cards"] == 1
