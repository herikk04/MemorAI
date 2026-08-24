"""Abstract LLM client and shared dataclasses.

All providers (OpenAI, Anthropic, Ollama, Mock) implement LLMClient so the
orchestrator is provider-agnostic. Swapping providers is done in
factory.get_llm_client() based on settings.AI_CONFIG["provider"].
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Protocol

from .errors import LLMError, LLMTimeoutError  # noqa: F401  (re-exported)

logger = logging.getLogger("apps.ai")


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    tokens_in: int
    tokens_out: int
    model: str
    provider: str
    raw: dict[str, Any] = field(default_factory=dict)
    # cost_usd filled in by the client when it knows pricing; otherwise the
    # orchestrator estimates it via apps.ai.services.cost.estimate_cost.
    cost_usd: float | None = None


class LLMClient(Protocol):
    """Provider-agnostic LLM adapter.

    Implementations are responsible for:
      - reading their API key from settings.AI_CONFIG (or env) at __init__
      - applying the timeout/max_tokens from AI_CONFIG
      - never logging the API key or full user payloads
      - raising LLMError (defined in errors.py) on failure
    """

    name: str

    def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> LLMResponse: ...


__all__ = ["LLMClient", "Message", "LLMResponse", "LLMError", "LLMTimeoutError"]
