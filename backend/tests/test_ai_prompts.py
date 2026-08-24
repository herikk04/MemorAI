"""Tests for apps.ai.prompts.loader."""
from __future__ import annotations

import pytest

from apps.ai.prompts.loader import PromptError, load_prompt


_PT_PAYLOAD = {
    "front": "Q",
    "back": "A",
    "rating_label": "Again",
    "time_ms": 1000,
    "reps": 0,
    "lapses": 0,
}


class TestPromptLoader:
    def test_renders_required_vars_pt(self):
        p = load_prompt("feedback", "pt", _PT_PAYLOAD)
        assert p.flow == "feedback"
        assert p.language == "pt-BR"
        assert p.version == "1.0"
        assert "Q" in p.user
        assert "A" in p.user
        assert "Again" in p.user
        assert "Tutor de programacao" in p.system or "Voce e um tutor" in p.system

    def test_renders_en_prompt(self):
        p = load_prompt("feedback", "en", {**_PT_PAYLOAD, "rating_label": "Good"})
        assert p.language == "en"
        assert "You are a programming tutor" in p.system
        assert "Good" in p.user

    def test_missing_required_var_raises(self):
        bad = {k: v for k, v in _PT_PAYLOAD.items() if k != "front"}
        with pytest.raises(PromptError):
            load_prompt("feedback", "pt", bad)

    def test_unknown_flow_raises(self):
        with pytest.raises(PromptError):
            load_prompt("not-a-flow", "pt", _PT_PAYLOAD)

    def test_defaults_filled_when_optional_missing(self):
        minimal = {"front": "q", "back": "a", "rating_label": "Good"}
        p = load_prompt("feedback", "pt", minimal)
        # pt template uses "Tempo gasto: 0 ms" when time_ms defaults to 0.
        assert "Tempo gasto: 0 ms" in p.user
        assert "Repeticoes anteriores: 0" in p.user
        assert "Lapsos: 0" in p.user
