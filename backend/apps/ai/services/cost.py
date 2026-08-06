"""Cost estimation for LLM calls.

Real providers return usage but not always price; we approximate using a
tiny pricing table keyed by (provider, model-prefix). When the provider
already filled cost_usd (e.g. Ollama sets 0), we trust it. This module is
the single place to update pricing so the orchestrator never hardcodes it.
"""
from __future__ import annotations

from decimal import Decimal

# Per-million-token prices in USD. Match by provider then by model prefix.
# Prices hallucinated; keep low conservative defaults; tune in prod.
_PRICING_PER_M = {
    "openai": {
        "gpt-4o":        {"in": 5.0, "out": 15.0},
        "gpt-4o-mini":   {"in": 0.15, "out": 0.60},
        "gpt-4.1-mini":  {"in": 0.40, "out": 1.60},
        "gpt-3.5":       {"in": 0.50, "out": 1.50},
        "_default":      {"in": 1.0, "out": 3.0},
    },
    "anthropic": {
        "claude-3-5-sonnet": {"in": 3.0, "out": 15.0},
        "claude-3-5-haiku":  {"in": 0.80, "out": 4.0},
        "_default":          {"in": 3.0, "out": 15.0},
    },
    "ollama":  {"_default": {"in": 0.0, "out": 0.0}},
    "mock":    {"_default": {"in": 0.0, "out": 0.0}},
}


def _lookup(provider: str, model: str) -> dict[str, float]:
    table = _PRICING_PER_M.get(provider) or _PRICING_PER_M["openai"]
    for prefix, price in table.items():
        if prefix != "_default" and model.startswith(prefix):
            return price
    return table.get("_default", {"in": 0.0, "out": 0.0})


def estimate_cost(provider: str, model: str, tokens_in: int, tokens_out: int) -> Decimal:
    price = _lookup(provider, model)
    cost = (tokens_in / 1_000_000) * price["in"] + (tokens_out / 1_000_000) * price["out"]
    return Decimal(str(cost)).quantize(Decimal("0.000001"))
