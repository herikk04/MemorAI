"""Embedding client: generates vector representations of text.

Mirrors the LLM client layer in apps.ai.clients: an EmbeddingClient
Protocol + concrete implementations (OpenAI, Mock) and a factory.

The vector dimension defaults from AI_CONFIG["embedding_dim"] (1536 for
text-embedding-3-small). All clients return a list of floats so the
VectorStore adapter can store it regardless of which provider produced
it.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import Protocol

from django.conf import settings

logger = logging.getLogger("apps.ai.embeddings")


@dataclass(frozen=True)
class EmbeddingResult:
    vector: list[float]
    model: str
    provider: str
    tokens: int


class EmbeddingClient(Protocol):
    name: str

    def embed(self, text: str, *, model: str | None = None) -> EmbeddingResult: ...


class MockEmbeddingClient:
    """Deterministic embedding for dev/tests: SHA-256-derived float vector.

    No network access; the vector space is small (default dim=1536) but
    deterministic for the same input text, so similarity tests can rely on
    hash-distance rather than a real model.
    """

    name = "mock"

    def __init__(self, dim: int | None = None) -> None:
        cfg = getattr(settings, "AI_CONFIG", {})
        self.dim = dim or cfg.get("embedding_dim", 1536)
        self.model = "mock-embedding"

    def embed(self, text: str, *, model: str | None = None) -> EmbeddingResult:
        # Produce a stable vector by hashing segments of the text and
        # mapping each to a float in [-1, 1]. Each component i uses a
        # different salted digest so identical short strings diverge
        # across dimensions.
        vec: list[float] = []
        for i in range(self.dim):
            digest = hashlib.sha256(f"{i}|{text}".encode("utf-8")).digest()
            # Take 4 bytes as a uint32, map to [-1, 1].
            n = int.from_bytes(digest[:4], "big") / 2**32
            vec.append(n * 2 - 1)
        # L2-normalize so cosine similarity is well-defined and comparable
        # across wrapper dims across rows.
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        vec = [v / norm for v in vec]
        return EmbeddingResult(
            vector=vec,
            model=model or self.model,
            provider=self.name,
            tokens=max(1, len(text) // 4),
        )


class OpenAIEmbeddingClient:
    name = "openai"

    def __init__(self) -> None:
        try:
            import openai  # noqa: F401
        except ImportError as exc:
            from .errors_shared import EmbeddingConfigError

            raise EmbeddingConfigError(
                "openai package not installed for embeddings."
            ) from exc
        cfg = getattr(settings, "AI_CONFIG", {})
        key = cfg.get("openai_api_key") or ""
        if not key:
            from .errors_shared import EmbeddingConfigError

            raise EmbeddingConfigError("OPENAI_API_KEY not configured for embeddings.")
        self._client = openai.OpenAI(api_key=key)
        self.default_model = cfg.get("embedding_model", "text-embedding-3-small")

    def embed(self, text: str, *, model: str | None = None) -> EmbeddingResult:
        import openai

        try:
            resp = self._client.embeddings.create(
                model=model or self.default_model,
                input=text,
            )
        except openai.APIError as exc:
            from .errors_shared import EmbeddingError

            raise EmbeddingError(str(exc)) from exc
        vec = resp.data[0].embedding
        usage = resp.usage
        return EmbeddingResult(
            vector=vec,
            model=getattr(resp, "model", model or self.default_model),
            provider=self.name,
            tokens=usage.total_tokens if usage else 0,
        )


def get_embedding_client(provider: str | None = None) -> EmbeddingClient:
    cfg = getattr(settings, "AI_CONFIG", {})
    provider = (provider or cfg.get("provider") or "").lower()

    if provider in ("", "mock"):
        return MockEmbeddingClient()

    if provider == "openai":
        if not cfg.get("openai_api_key"):
            logger.warning(
                "provider=openai but OPENAI_API_KEY empty; using mock embeddings."
            )
            return MockEmbeddingClient()
        try:
            return OpenAIEmbeddingClient()
        except Exception as exc:  # noqa: BLE001
            logger.warning("OpenAI embedding client init failed; using mock: %s", exc)
            return MockEmbeddingClient()

    # Unknown provider -> mock ( Anthropic/Ollama don't have a unified
    # embeddings API we wire here; they can be added later without breaking
    # callers since the adapter is the only entry point).
    logger.warning("Unknown embedding provider %r; using mock.", provider)
    return MockEmbeddingClient()
