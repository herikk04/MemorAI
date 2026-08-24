"""LLM-specific exceptions."""


class LLMError(Exception):
    """Raised by LLM clients on provider failures."""


class LLMTimeoutError(LLMError):
    """Raised when the provider times out, enabling fallback to heuristics."""


class LLMConfigError(LLMError):
    """Raised when the client is misconfigured (missing key/model)."""
