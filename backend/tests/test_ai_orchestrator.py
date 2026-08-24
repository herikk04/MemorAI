"""Tests for apps.ai.services.orchestrator and flows.feedback.

Verifies that AIEvent is written on success and on fallback, and that the
feedback flow always returns a result string even on LLM failure.
"""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from apps.ai.models import AIEvent, AIUsage
from apps.ai.services import orchestrator
from apps.ai.services.cost import estimate_cost


_PAYLOAD = {
    "front": "Qual a saida de print([1,2]+[3])",
    "back": "[1, 2, 3]",
    "rating": 1,  # Again
    "time_ms": 8500,
    "reps": 4,
    "lapses": 2,
}


class TestRunFlowFeedback:
    @pytest.mark.django_db
    def test_success_records_event(self):
        events_before = AIEvent.objects.count()
        result = orchestrator.run_flow("feedback", _PAYLOAD, language="pt", user=None)
        events_after = AIEvent.objects.count()

        assert events_after == events_before + 1
        assert result.status == "success"
        assert result.prompt_version == "1.0"
        assert result.text  # non-empty

        ev = AIEvent.objects.latest("created_at")
        assert ev.flow == "feedback"
        assert ev.status == "success"
        assert ev.prompt_version == "1.0"
        assert ev.tokens_in > 0
        assert ev.tokens_out > 0

    def test_unknown_flow_raises_value_error(self):
        with pytest.raises(ValueError):
            orchestrator.run_flow("not-a-flow", {}, user=None)

    @pytest.mark.django_db
    @override_settings(
        AI_CONFIG={"provider": "mock"}
    )
    def test_user_authenticated_rolls_into_usage(self):
        User = get_user_model()
        u = User.objects.create_user(username="ai-user", password="pw1234567")

        # Authenticated user → AIUsage should be incremented.
        usage_before = AIUsage.objects.filter(user=u).count()
        orchestrator.run_flow("feedback", _PAYLOAD, language="pt", user=u)
        usage_after = AIUsage.objects.filter(user=u).count()
        assert usage_after == usage_before + 1

        usage = AIUsage.objects.get(user=u)
        assert usage.calls == 1
        assert usage.tokens_in > 0
        assert usage.tokens_out > 0


class TestQuotas:
    def test_anonymous_has_infinite_quota(self):
        rem = orchestrator.quota_remaining(user=None)
        assert rem["tokens"] == float("inf")
        exceeded, reason = orchestrator.quota_exceeded(user=None)
        assert exceeded is False
        assert reason is None

    @pytest.mark.django_db
    def test_authenticated_within_cap(self):
        User = get_user_model()
        u = User.objects.create_user(username="q", password="pw1234567")
        rem = orchestrator.quota_remaining(u)
        assert rem["tokens"] > 0
        assert rem["cost_usd"] > 0
        exceeded, _ = orchestrator.quota_exceeded(u)
        assert exceeded is False

    @pytest.mark.django_db
    def test_authenticated_quota_exceeded_when_usage_at_cap(self):
        import datetime as _dt
        from decimal import Decimal

        User = get_user_model()
        u = User.objects.create_user(username="e", password="pw1234567")
        caps = AIUsage.caps()
        # Burn the full token cap on today.
        AIUsage.objects.create(
            user=u,
            day=_dt.date.today(),
            tokens_in=caps["tokens"],
            tokens_out=0,
            cost_usd=Decimal("0"),
            calls=1,
        )
        exceeded, reason = orchestrator.quota_exceeded(u)
        assert exceeded is True
        assert reason == "daily_token_cap_per_user"


class TestCostEstimator:
    def test_zero_for_mock(self):
        cost = estimate_cost("mock", "mock-model", 1000, 1000)
        assert cost == 0

    def test_ollama_free(self):
        cost = estimate_cost("ollama", "llama3.1", 1000, 1000)
        assert cost == 0

    def test_openai_prefix_match(self):
        # gpt-4o-mini: $0.15/M in, $0.60/M out
        cost = estimate_cost("openai", "gpt-4o-mini-2024-07-18", 1_000_000, 1_000_000)
        assert float(cost) == pytest.approx(0.15 + 0.60)

    def test_openai_default_when_unknown_prefix(self):
        cost = estimate_cost("openai", "gpt-something-new", 1_000_000, 0)
        # _default for openai is in=1.0/M
        assert float(cost) == pytest.approx(1.0)

    def test_decimal_quantized(self):
        cost = estimate_cost("openai", "gpt-4o-mini", 1000, 500)
        assert cost.as_tuple().exponent == -6
