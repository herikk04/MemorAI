"""Factory for picking an LLMClient based on settings.AI_CONFIG.

Resolution order:
  1. AI_CONFIG["provider"] when set ("openai" | "anthropic" | "azure" |
     "ollama" | "mock").
  2. If provider requires a key and the key is empty, fall back to mock so
     dev works out-of-the-box and `openai import <file>` benchmarks never
     explode just because someone forgot to set OPENAI_API_KEY.

Tests explicitly set AI_CONFIG["provider"] = "mock" in settings/test.py.
"""
from __future__ import annotations

import logging

from django.conf import settings

from .base import LLMClient
from .errors import LLMConfigError

logger = logging.getLogger("apps.ai")


def _cfg() -> dict:
    return getattr(settings, "AI_CONFIG", {})


def _need_key(name: str) -> str:
    key = _cfg().get(name, "")
    if not key:
        raise LLMConfigError(f"Missing key for {name}")
    return key


def get_llm_client(provider: str | None = None) -> LLMClient:
    cfg = _cfg()
    provider = (provider or cfg.get("provider") or "").lower()

    if provider in ("", "mock"):
        from .mock_client import MockLLMClient
        return MockLLMClient()

    if provider == "openai":
        if not cfg.get("openai_api_key"):
            logger.warning("LLM_PROVIDER=openai but OPENAI_API_KEY empty; using mock.")
            from .mock_client import MockLLMClient
            return MockLLMClient()
        from .openai_client import OpenAIClient
        return OpenAIClient()

    if provider == "anthropic":
        if not cfg.get("anthropic_api_key"):
            logger.warning("LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY empty; using mock.")
            from .mock_client import MockLLMClient
            return MockLLMClient()
        from .anthropic_client import AnthropicClient
        return AnthropicClient()

    if provider == "ollama":
        from .ollama_client import OllamaClient
        return OllamaClient()

    raise LLMConfigError(f"Unknown LLM_PROVIDER {provider!r}")
