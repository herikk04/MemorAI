"""Versioned prompt loader for apps.ai.

Prompts live as YAML files under apps/ai/prompts/. Each file has:
  - version (string, semver-ish; bumped on every meaningful edit)
  - language (pt-BR, en, ...)
  - system (the system prompt sent to the LLM)
  - template (the user prompt, with {{var}} placeholders)
  - vars (schema for the variables; type/required/default/enum)

The loader renders templates using Python str.format-style placeholders
(wrapped as {{var}} in the YAML to avoid brace clashes in code samples)
and validates that every required var is provided. The rendered (system +
user) tuple is cached in-memory for the process lifetime; prompts are
immutable once loaded, which is what enables AIEvent.prompt_version to be
a meaningful audit key.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from django.core.cache import cache

logger = logging.getLogger("apps.ai")

PROMPT_DIR = Path(__file__).resolve().parent

_PLACEHOLDER = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")


class PromptError(Exception):
    pass


@dataclass(frozen=True)
class LoadedPrompt:
    flow: str
    language: str
    version: str
    system: str
    user: str
    model_hint: str | None


def _list_files() -> dict[str, Path]:
    """Map flow.language -> path. e.g. feedback.pt -> .../feedback.pt.yaml."""
    out: dict[str, Path] = {}
    for p in PROMPT_DIR.glob("*.yaml"):
        stem = p.stem  # "feedback.pt" or "feedback"
        out[stem] = p
    return out


def _load_raw(flow: str, language: str) -> dict[str, Any]:
    key = f"{flow}.{language}"
    files = _list_files()
    path = files.get(key) or files.get(flow)
    if path is None:
        raise PromptError(f"No prompt file for flow={flow!r} lang={language!r}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise PromptError(f"YAML error in {path.name}: {exc}") from exc
    if not isinstance(data, dict):
        raise PromptError(f"Prompt {path.name} is not a mapping")
    return data


def _validate_vars(template: str, vars_schema: dict, payload: dict[str, Any]) -> dict[str, Any]:
    required = {name: spec for name, spec in vars_schema.items() if spec.get("required")}
    for name, spec in required.items():
        if name not in payload or payload[name] is None:
            raise PromptError(f"Missing required var {name!r}")
    filled = {}
    for name, spec in vars_schema.items():
        if name in payload and payload[name] is not None:
            filled[name] = payload[name]
        elif "default" in spec:
            filled[name] = spec["default"]
        elif spec.get("required"):
            raise PromptError(f"Missing required var {name!r}")
    unknown = set(payload) - set(vars_schema)
    if unknown:
        logger.warning("Prompt %s got unknown vars: %s", set(payload).intersection(unknown), sorted(unknown))
    return filled


def _render(text: str, vars_map: dict[str, Any]) -> str:
    def repl(m: re.Match) -> str:
        name = m.group(1)
        return str(vars_map.get(name, m.group(0)))
    return _PLACEHOLDER.sub(repl, text)


def load_prompt(flow: str, language: str, payload: dict[str, Any]) -> LoadedPrompt:
    """Load + validate + render a prompt. Cached by (flow, language, version).

    payload must contain the variables declared under `vars` in the YAML.
    """
    cache_key = f"ai:prompt:{flow}:{language}"
    raw = cache.get(cache_key)
    if raw is None:
        raw = _load_raw(flow, language)
        cache.set(cache_key, raw, timeout=3600)
    version = str(raw.get("version", ""))
    if not version:
        raise PromptError("Prompt missing required 'version'")
    system = raw.get("system", "")
    template = raw.get("template", "")
    vars_schema = raw.get("vars", {}) or {}
    filled = _validate_vars(template, vars_schema, payload)
    user = _render(template, filled)
    return LoadedPrompt(
        flow=flow,
        language=raw.get("language", language),
        version=version,
        system=system,
        user=user,
        model_hint=raw.get("model_hint"),
    )
