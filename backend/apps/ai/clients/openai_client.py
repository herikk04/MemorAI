"""OpenAI LLM client.

The openai SDK is imported lazily inside __init__ so the rest of the system
boots even if the package is not installed (e.g. when running tests against
the mock provider). API key is read from settings via django-environ and
never logged.
"""
from __future__ import annotations

from typing import Any

from django.conf import settings

from .base import LLMResponse, Message
from .errors import LLMConfigError, LLMError, LLMTimeoutError


class OpenAIClient:
    name = "openai"

    def __init__(self, **_: Any) -> None:
        try:
            import openai  # noqa: F401  (import check)
        except ImportError as exc:
            raise LLMConfigError(
                "openai package is not installed. "
                "Install with: pip install openai"
            ) from exc

        cfg = getattr(settings, "AI_CONFIG", {})
        key = cfg.get("openai_api_key") or ""
        if not key:
            raise LLMConfigError("OPENAI_API_KEY not configured.")
        self._client = openai.OpenAI(api_key=key)
        self.default_model = cfg.get("default_model", "gpt-4o-mini")
        self.default_timeout = cfg.get("timeout_seconds", 30)
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
            cost_usd=None,
            raw={"id": getattr(resp, "id", "")},
        )
