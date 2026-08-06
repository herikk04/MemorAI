"""Tests for the AI safety layer (PII masking)."""
from __future__ import annotations

from apps.ai.safety import sanitize_inputs, sanitize_text


class TestSanitizeText:
    def test_masks_email(self):
        r = sanitize_text("contato jose@example.com")
        assert "jose@example.com" not in r.text
        assert "[email-masked]" in r.text
        assert "email" in r.masked

    def test_masks_credit_card(self):
        r = sanitize_text("card 4111 1111 1111 1111")
        assert "4111" not in r.text
        assert "[card-masked]" in r.text
        assert "card" in r.masked

    def test_masks_cpf(self):
        r = sanitize_text("cpf 123.456.789-00")
        assert "123.456.789-00" not in r.text
        assert "cpf" in r.masked

    def test_masks_phone_brazilian(self):
        r = sanitize_text("tel +55 11 91234-5678")
        assert "91234-5678" not in r.text
        assert "phone" in r.masked

    def test_no_pii_leaves_text(self):
        r = sanitize_text("def foo(): return 42")
        assert r.text == "def foo(): return 42"
        assert r.masked == []

    def test_idempotent_on_already_masked(self):
        once = sanitize_text("mail me at a@b.com")
        twice = sanitize_text(once.text)
        assert twice.text == once.text
        assert twice.masked == []


class TestSanitizeInputs:
    def test_masks_only_string_fields(self):
        out = sanitize_inputs(
            {"front": "Meu contato: ana@mail.com", "rating": 1, "reps": 3}
        )
        assert "[email-masked]" in out["front"]
        assert out["rating"] == 1
        assert out["reps"] == 3

    def test_does_not_touch_non_pii_strings(self):
        out = sanitize_inputs({"front": "qual a saida de print([1,2])"})
        assert out["front"] == "qual a saida de print([1,2])"
