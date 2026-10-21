"""Assisted card generation: parser, flow and endpoint."""
from __future__ import annotations

from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.ai.clients import LLMResponse
from apps.ai.flows.generate_cards import parse_cards, run_generate_cards
from apps.ai.models import AIEvent

URL = "/api/v1/ai/generate-cards/"


class TestParseCards:
    def test_plain_array(self):
        cards = parse_cards('[{"front": "a?", "back": "b"}]', 5)
        assert [(c.front, c.back) for c in cards] == [("a?", "b")]

    def test_markdown_fence_and_prose_are_tolerated(self):
        raw = 'Aqui:\n```json\n[{"front": "a?", "back": "b"}]\n```'
        assert len(parse_cards(raw, 5)) == 1

    def test_drops_invalid_and_duplicates_and_respects_limit(self):
        raw = (
            '[{"front": "q1", "back": "a"}, {"front": "Q1", "back": "dup"},'
            ' {"front": "", "back": "x"}, {"front": 3, "back": "x"}, "junk",'
            ' {"front": "q2", "back": "b"}, {"front": "q3", "back": "c"}]'
        )
        assert [c.front for c in parse_cards(raw, 2)] == ["q1", "q2"]

    def test_no_array_raises(self):
        with pytest.raises(ValueError):
            parse_cards("sorry, I cannot", 5)


@pytest.mark.django_db
class TestFlow:
    def test_mock_provider_returns_requested_count(self):
        result = run_generate_cards({"topic": "decorators", "count": 3})
        assert result.status == AIEvent.Status.SUCCESS
        assert len(result.cards) == 3
        assert AIEvent.objects.filter(flow="generate_cards", status="success").count() == 1

    def test_unparseable_output_falls_back_without_cards(self):
        bad = LLMResponse(content="nope", tokens_in=1, tokens_out=1, model="m", provider="p")
        with mock.patch("apps.ai.flows.generate_cards.get_llm_client") as get:
            get.return_value.complete.return_value = bad
            result = run_generate_cards({"topic": "x"})
        assert result.cards == []
        assert result.status == AIEvent.Status.FALLBACK
        assert AIEvent.objects.filter(flow="generate_cards", status="fallback").exists()

    def test_pii_in_source_text_is_masked_before_the_provider(self):
        with mock.patch("apps.ai.flows.generate_cards.get_llm_client") as get:
            get.return_value.complete.return_value = LLMResponse(
                content='[{"front": "q", "back": "a"}]',
                tokens_in=1, tokens_out=1, model="m", provider="p",
            )
            run_generate_cards({"topic": "x", "source_text": "write to ana@example.com"})
        sent = get.return_value.complete.call_args.kwargs["messages"][1].content
        assert "ana@example.com" not in sent
        assert "[email-masked]" in sent

    def test_missing_topic_is_rejected(self):
        with pytest.raises(ValueError):
            run_generate_cards({"topic": "  "})


@pytest.mark.django_db
class TestEndpoint:
    @pytest.fixture
    def client(self):
        c = APIClient()
        c.force_authenticate(get_user_model().objects.create_user(username="g", password="pw1234567"))
        return c

    def test_requires_auth(self):
        assert APIClient().post(URL, {"topic": "x"}, format="json").status_code == 401

    def test_returns_proposals(self, client):
        resp = client.post(URL, {"topic": "list comprehensions", "count": 2, "language": "en"}, format="json")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert len(body["cards"]) == 2
        assert set(body["cards"][0]) == {"front", "back"}

    def test_validates_input(self, client):
        assert client.post(URL, {}, format="json").status_code == 400
        assert client.post(URL, {"topic": "x", "count": 99}, format="json").status_code == 400
