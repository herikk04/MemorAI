"""Mock LLM client for dev and tests.

Returns deterministic responses without any network access. The content
echoes the user message and a marker, so tests can assert on it.
"""
from __future__ import annotations

import hashlib
import json
import re
import time

from .base import LLMResponse, Message


def _mock_cards_json(user_msg: str) -> str:
    """Deterministic cards array for prompts shaped like generate_cards.*.yaml."""
    topic = re.search(r"(?:Topico|Topic):\s*(.+)", user_msg)
    count = re.search(r"(?:Quantidade de cards|Number of cards):\s*(\d+)", user_msg)
    name = topic.group(1).strip() if topic else "topic"
    n = int(count.group(1)) if count else 3
    return json.dumps(
        [{"front": f"[mock] {name} #{i}?", "back": f"[mock] answer {i}"} for i in range(1, n + 1)]
    )


class MockLLMClient:
    name = "mock"

    def __init__(self, model: str = "mock-model", **_: object) -> None:
        self.model = model

    def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> LLMResponse:
        # Unreachable in prod; the factory only picks mock when explicitly
        # asked, or when no real key is present (dev fallback).
        user_msg = next((m.content for m in messages if m.role == "user"), "")
        system_msg = next((m.content for m in messages if m.role == "system"), "")
        digest = hashlib.sha256(user_msg.encode("utf-8")).hexdigest()[:8]
        if "JSON" in system_msg:
            # Structured-output prompts (e.g. generate_cards) get a JSON array.
            content = _mock_cards_json(user_msg)
        else:
            content = f"[mock-feedback:{digest}] explanation for: {user_msg[:120]}"
        tokens_in = sum(len(m.content) // 4 for m in messages) or 4
        tokens_out = max(10, len(content) // 4)
        time.sleep(0)
        return LLMResponse(
            content=content,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            model=model or self.model,
            provider=self.name,
            cost_usd=0.0,
            raw={"mock": True},
        )
