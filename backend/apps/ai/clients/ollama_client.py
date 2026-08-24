"""Ollama local LLM client (self-hosted, no API key).

Useful for open-source/offline deployments. The openai SDK is reused in
Ollama's OpenAI-compatible mode (Ollama exposes /v1 since 0.1.x), so we
avoid adding another dependency.
"""
from __future__ import annotations

from typing import Any

from django.conf import settings

from .base import LLMResponse, Message
from .errors import LLMConfigError, LLMError, LLMTimeoutError


class OllamaClient:
    name = "ollama"

    def __init__(self, **_: Any) -> None:
        try:
            import openai  # noqa: F401
        except ImportError as exc:
            raise LLMConfigError(
                "openai package is required (Ollama is hit via OpenAI api)."
            ) from exc

        cfg = getattr(settings, "AI_CONFIG", {})
        base_url = cfg.get("ollama_base_url") or "http://localhost:11434/v1"
        # Ollama ignores the api key but the openai SDK requires one non-empty.
        self._client = openai.OpenAI(base_url=base_url, api_key="ollama")
        self.default_model = cfg.get("default_model", "llama3.1")
        self.default_timeout = cfg.get("timeout_seconds", 60)
        self.default_max_tokens = cfg.get("max_tokens", 1024)

    def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> LLMResponse:
        import openai

        try:
            resp = self._client.chat.completions.create(
                model=model or self.default_model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                temperature=temperature,
                max_tokens=max_tokens or self.default_max_tokens,
                timeout=timeout or self.default_timeout,
            )
        except openai.APITimeoutError as exc:
            raise LLMTimeoutError(str(exc)) from exc
        except openai.APIError as exc:
            raise LLMError(str(exc)) from exc

        choice = resp.choices[0]
        usage = resp.usage
        return LLMResponse(
            content=choice.message.content or "",
            tokens_in=usage.prompt_tokens if usage else 0,
            tokens_out=usage.completion_tokens if usage else 0,
            model=getattr(resp, "model", model or self.default_model),
            provider=self.name,
            cost_usd=0.0,
            raw={"id": getattr(resp, "id", "")},
        )
