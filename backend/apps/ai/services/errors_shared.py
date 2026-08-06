"""Shared exceptions for the embeddings client layer (kept separate so the
clients don't need to import from the LLM client errors module)."""


class EmbeddingError(Exception):
    pass


class EmbeddingConfigError(EmbeddingError):
    pass
