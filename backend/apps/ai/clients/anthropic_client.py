"""Anthropic LLM client. Mirrors openai_client.py with the anthropic SDK."""
from __future__ import annotations

from typing import Any

from django.conf import settings

from .base import LLMResponse, Message
from .errors import LLMConfigError, LLMError, LLMTimeoutError


class AnthropicClient:
    name = "anthropic"

    def __init__(self, **_: Any) -> None:
        try:
            import anthropic  # noqa: F401
        except ImportError as exc:
            raise LLMConfigError(
                "anthropic package is not installed. "
                "Install with: pip install anthropic"
            ) from exc

        cfg = getattr(settings, "AI_CONFIG", {})
        key = cfg.get("anthropic_api_key") or ""
        if not key:
            raise LLMConfigError("ANTHROPIC_API_KEY not configured.")
        self._client = anthropic.Anthropic(api_key=key)
        self.default_model = cfg.get("default_model", "claude-3-5-sonnet-latest")
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
        import anthropic

        # Anthropic separates system prompt from the message list.
        system_msgs = [m.content for m in messages if m.role == "system"]
        conv = [m for m in messages if m.role != "system"]
        try:
            resp = self._client.messages.create(
                model=model or self.default_model,
                system="\n\n".join(system_msgs) if system_msgs else None,
                messages=[{"role": m.role, "content": m.content} for m in conv],
                temperature=temperature,
                max_tokens=max_tokens or self.default_max_tokens,
                timeout=timeout or self.default_timeout,
            )
        except anthropic.APITimeoutError as exc:
            raise LLMTimeoutError(str(exc)) from exc
        except anthropic.APIError as exc:
            raise LLMError(str(exc)) from exc

        content = "".join(block.text for block in resp.content if hasattr(block, "text"))
        usage = resp.usage
        return LLMResponse(
            content=content,
            tokens_in=getattr(usage, "input_tokens", 0) if usage else 0,
            tokens_out=getattr(usage, "output_tokens", 0) if usage else 0,
            model=getattr(resp, "model", model or self.default_model),
            provider=self.name,
            cost_usd=None,
            raw={"id": getattr(resp, "id", "")},
        )
