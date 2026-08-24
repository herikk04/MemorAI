"""Tests for the embedding client layer (apps.ai.services.embeddings)."""
from __future__ import annotations

import math

import pytest

from apps.ai.services.embeddings import (
    EmbeddingResult,
    MockEmbeddingClient,
    get_embedding_client,
)


class TestMockEmbeddingClient:
    def test_returns_dim_from_settings(self):
        c = MockEmbeddingClient()
        r = c.embed("hello")
        assert isinstance(r, EmbeddingResult)
        assert len(r.vector) == 1536
        assert all(isinstance(v, float) for v in r.vector)
        assert r.provider == "mock"
        assert r.tokens >= 1

    def test_vectors_are_l2_normalized(self):
        v = MockEmbeddingClient().embed("abc").vector
        norm = math.sqrt(sum(x * x for x in v))
        assert norm == pytest.approx(1.0, abs=1e-6)

    def test_deterministic_for_same_input(self):
        c = MockEmbeddingClient()
        a = c.embed("same query")
        b = c.embed("same query")
        assert a.vector == b.vector

    def test_different_inputs_diverge(self):
        c = MockEmbeddingClient()
        a = c.embed("python")
        b = c.embed("rust")
        # Same dim, different content.
        assert len(a.vector) == len(b.vector)
        assert a.vector != b.vector

    def test_cosine_between_identical_is_one(self):
        c = MockEmbeddingClient()
        v = c.embed("x").vector
        cos = sum(x * y for x, y in zip(v, v)) / (
            math.sqrt(sum(x * x for x in v)) * math.sqrt(sum(y * y for y in v))
        )
        assert cos == pytest.approx(1.0, abs=1e-6)


class TestFactory:
    def test_default_is_mock(self):
        c = get_embedding_client()
        assert isinstance(c, MockEmbeddingClient)

    def test_explicit_mock_provider(self):
        assert isinstance(get_embedding_client("mock"), MockEmbeddingClient)

    def test_openai_without_key_falls_back_to_mock(self):
        # settings/test.py sets empty openai_api_key
        c = get_embedding_client("openai")
        assert isinstance(c, MockEmbeddingClient)

    def test_unknown_provider_falls_back_to_mock(self):
        assert isinstance(get_embedding_client("acme"), MockEmbeddingClient)
