"""Tests for apps.ai.clients (mock client, factory, errors)."""
from __future__ import annotations

import pytest
from django.test import override_settings

from apps.ai.clients import (
    LLMConfigError,
    LLMResponse,
    Message,
    get_llm_client,
)
from apps.ai.clients.mock_client import MockLLMClient


class TestMockLLMClient:
    def test_returns_deterministic_content(self):
        c = MockLLMClient()
        r = c.complete([Message("user", "ola")])
        assert c.name == "mock"
        assert isinstance(r, LLMResponse)
        assert r.provider == "mock"
        assert "[mock-feedback:" in r.content
        assert r.cost_usd == 0.0
        assert r.tokens_in > 0
        assert r.tokens_out > 0

    def test_content_changes_with_input(self):
        a = MockLLMClient().complete([Message("user", "aaa")])
        b = MockLLMClient().complete([Message("user", "bbb")])
        assert a.content != b.content


class TestFactoryFallbacks:
    def test_unknown_provider_raises(self):
        with pytest.raises(LLMConfigError):
            get_llm_client("does-not-exist")

    @override_settings(AI_CONFIG={"provider": "openai", "openai_api_key": ""})
    def test_openai_without_key_falls_back_to_mock(self):
        c = get_llm_client("openai")
        assert isinstance(c, MockLLMClient)

    @override_settings(AI_CONFIG={"provider": "anthropic", "anthropic_api_key": ""})
    def test_anthropic_without_key_falls_back_to_mock(self):
        c = get_llm_client("anthropic")
        assert isinstance(c, MockLLMClient)

    @override_settings(AI_CONFIG={"provider": "mock"})
    def test_mock_explicit(self):
        assert isinstance(get_llm_client(), MockLLMClient)

    @override_settings(AI_CONFIG={"provider": ""})
    def test_empty_provider_uses_mock(self):
        assert isinstance(get_llm_client(), MockLLMClient)
