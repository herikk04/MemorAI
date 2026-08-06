"""Sprint 4 tests: Celery tasks, analytics flows and their endpoints.

Covers run_report, run_review_suggestion, the generate_*_task wrappers
and the /report/, /suggestions/ and /tasks/<id>/ HTTP surface. Runs
against the eager Celery config so `.delay()` executes synchronously.
"""
from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.ai.flows.report import run_report
from apps.ai.flows.review_suggestion import run_review_suggestion
from apps.ai.models import AIEvent
from apps.ai.tasks import generate_report_task, generate_suggestions_task
from flashcards.models import Card, Deck, Review


@pytest.fixture
def user():
    return get_user_model().objects.create_user(username="analytics", password="pw1234567")


@pytest.fixture
def deck():
    return Deck.objects.create(name="Analytics Deck")


def make_card(deck, *, due_ago=None, due_in=None, lapses=0, reps=0, front="front"):
    due = None
    now = timezone.now()
    if due_ago is not None:
        due = now - timedelta(seconds=due_ago)
    elif due_in is not None:
        due = now + timedelta(seconds=due_in)
    return Card.objects.create(
        deck=deck,
        front=front,
        back="back",
        due=due,
        lapses=lapses,
        reps=reps,
    )


class TestReportFlow:
    @pytest.mark.django_db
    def test_empty_user_returns_heuristic(self):
        result = run_report({}, user=user)
        assert result.status == AIEvent.Status.FALLBACK
        assert result.metrics.total_reviews == 0
        assert result.text

    @pytest.mark.django_db
    def test_anonymous_returns_empty_metrics(self):
        result = run_report({}, user=None)
        assert result.metrics.total_reviews == 0
        assert result.text

    @pytest.mark.django_db
    def test_metrics_aggregate_reviews(self, user, deck):
        card = make_card(deck, due_in=3600, lapses=1, reps=2)
        Review.objects.create(card=card, user=user, rating=3)
        result = run_report({}, user=user)
        assert result.metrics.total_reviews == 1
        assert result.metrics.total_lapses == 1
        assert result.metrics.avg_reps == pytest.approx(2.0)

    @pytest.mark.django_db
    def test_report_never_raises(self, user, deck, monkeypatch):
        make_card(deck, due_in=60, lapses=1, reps=1)
        Review.objects.create(card=make_card(deck, due_in=120), user=user, rating=3)

        def boom(*args, **kwargs):
            raise RuntimeError("llm down")

        monkeypatch.setattr("apps.ai.flows.report.get_llm_client", boom)
        result = run_report({}, user=user)
        assert result.status == AIEvent.Status.FALLBACK
        assert result.text


class TestReviewSuggestionFlow:
    @pytest.mark.django_db
    def test_anonymous_returns_empty(self):
        result = run_review_suggestion({}, user=None)
        assert result.hits == []
        assert result.user_id is None

    @pytest.mark.django_db
    def test_overdue_first(self, user, deck):
        soon = make_card(deck, due_in=3600, front="soon")
        overdue = make_card(deck, due_ago=60 * 60 * 5, front="overdue")
        Review.objects.create(card=soon, user=user, rating=3)
        Review.objects.create(card=overdue, user=user, rating=2)
        hits = run_review_suggestion({}, user=user).hits
        assert [h.card_id for h in hits] == [overdue.id, soon.id]
        assert hits[0].due_in_seconds < 0

    @pytest.mark.django_db
    def test_more_lapses_ranked_above(self, user, deck):
        low = make_card(deck, due_in=600, lapses=1, front="low")
        high = make_card(deck, due_in=600, lapses=5, front="high")
        # Force identical due timestamps so lapses is the tie-breaker.
        same_due = timezone.now() + timedelta(seconds=600)
        low.due = same_due
        low.save()
        high.due = same_due
        high.save()
        Review.objects.create(card=low, user=user, rating=3)
        Review.objects.create(card=high, user=user, rating=1)
        hits = run_review_suggestion({}, user=user).hits
        assert [h.card_id for h in hits] == [high.id, low.id]

    @pytest.mark.django_db
    def test_week_away_cards_skipped(self, user, deck):
        far = make_card(deck, due_in=8 * 24 * 3600, front="far")
        Review.objects.create(card=far, user=user, rating=3)
        hits = run_review_suggestion({}, user=user).hits
        assert hits == []

    @pytest.mark.django_db
    def test_top_k_limits_hits(self, user, deck):
        for i in range(5):
            card = make_card(deck, due_ago=i * 60, front=f"c{i}")
            Review.objects.create(card=card, user=user, rating=3)
        hits = run_review_suggestion({"top_k": 2}, user=user).hits
        assert len(hits) == 2

    @pytest.mark.django_db
    def test_records_ai_event(self, user, deck):
        card = make_card(deck, due_in=300)
        Review.objects.create(card=card, user=user, rating=3)
        before = AIEvent.objects.count()
        run_review_suggestion({}, user=user)
        assert AIEvent.objects.count() == before + 1
        ev = AIEvent.objects.latest("created_at")
        assert ev.flow == "review_suggestion"
        assert ev.provider == "heuristic"
        assert ev.tokens_in == 0


class TestAnalyticsTasks:
    @pytest.mark.django_db
    def test_report_task_serializes(self, user, deck):
        card = make_card(deck, due_in=300, lapses=1, reps=1)
        Review.objects.create(card=card, user=user, rating=3)
        result = generate_report_task.delay(user.id, "pt").get()
        assert result["user_id"] == user.id
        assert result["metrics"]["total_reviews"] == 1
        assert isinstance(result["metrics"]["last_review_at"], str)

    @pytest.mark.django_db
    def test_suggestions_task_serializes(self, user, deck):
        card = make_card(deck, due_ago=300)
        Review.objects.create(card=card, user=user, rating=3)
        result = generate_suggestions_task.delay(user.id, 5).get()
        assert result["hits"][0]["card_id"] == card.id
        assert result["hits"][0]["due_in_seconds"] < 0

    @pytest.mark.django_db
    def test_task_without_user_returns_empty(self):
        result = generate_report_task.delay(None, "pt").get()
        assert result["user_id"] is None
        suggestions = generate_suggestions_task.delay(None, 5).get()
        assert suggestions["hits"] == []


class TestAnalyticsEndpoints:
    @pytest.fixture(autouse=True)
    def client(self):
        return APIClient()

    @pytest.mark.django_db
    def test_report_endpoint_returns_metrics(self, user, deck, client):
        card = make_card(deck, due_in=300)
        Review.objects.create(card=card, user=user, rating=3)
        client.force_authenticate(user)
        resp = client.get("/api/v1/ai/report/", {"language": "pt"})
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["metrics"]["total_reviews"] == 1
        assert "text" in body

    @pytest.mark.django_db
    def test_suggestions_endpoint_returns_hits(self, user, deck, client):
        card = make_card(deck, due_ago=600)
        Review.objects.create(card=card, user=user, rating=3)
        client.force_authenticate(user)
        resp = client.post(
            "/api/v1/ai/suggestions/", {"top_k": 5}, format="json"
        )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["hits"][0]["card_id"] == card.id
        assert AIEvent.objects.filter(flow="review_suggestion").count() == 1

    @pytest.mark.django_db
    def test_suggestions_invalid_top_k_rejected(self, user, client):
        client.force_authenticate(user)
        resp = client.post(
            "/api/v1/ai/suggestions/", {"top_k": 999}, format="json"
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_task_result_polling(self, user, deck, client):
        card = make_card(deck, due_in=300, lapses=1, reps=1)
        Review.objects.create(card=card, user=user, rating=3)
        task = generate_report_task.delay(user.id, "pt")
        resp = client.get(f"/api/v1/ai/tasks/{task.id}/")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["result"]["metrics"]["total_reviews"] == 1

    @pytest.mark.django_db
    def test_unknown_task_id_returns_pending(self, client):
        resp = client.get("/api/v1/ai/tasks/00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == status.HTTP_202_ACCEPTED
        assert resp.json()["status"] in ("PENDING", "FAILURE")
