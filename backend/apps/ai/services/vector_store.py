"""Vector store adapter for the Embedding model.

Two implementations of VectorStore, switched at runtime by the DB engine:

- PgVectorStore: runs cosine-similarity search via pgvector's operators
  (~/<=>) directly in SQL. Used when DATABASES["default"]["ENGINE"] is
  postgresql.
- InMemoryVectorStore: used on SQLite (dev/test). Reads every Embedding row
  into memory and ranks by cosine similarity in Python. Acceptable for the
  small dev dataset and for deterministic test assertions; never intended
  for production scale.

Both expose the same interface (upsert + search_similar + delete) so the
RAG flow does not care which one it is talking to.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Protocol

from django.db import connection

from ..models import Embedding

logger = logging.getLogger("apps.ai.vector_store")


@dataclass(frozen=True)
class SimilarityHit:
    entity_type: str
    entity_id: int
    score: float  # cosine similarity in [-1, 1]; higher is more similar
    embedding_id: int


class VectorStore(Protocol):
    def upsert(
        self,
        *,
        entity_type: str,
        entity_id: int,
        vector: list[float],
        model: str,
        version: str,
        dim: int,
    ) -> Embedding: ...

    def search_similar(
        self,
        query_vector: list[float],
        *,
        entity_type: str | None = None,
        top_k: int = 5,
        model: str | None = None,
        version: str | None = None,
    ) -> list[SimilarityHit]: ...

    def delete(self, *, entity_type: str, entity_id: int) -> int: ...


def _cosine(a: list[float], b: list[float]) -> float:
    """Plain cosine similarity. Assumes both vectors are non-empty and L2
    normalised (which the MockEmbeddingClient guarantees); falls back to a
    full dot product / norm if not.
    """
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class InMemoryVectorStore:
    """Reference implementation used when pgvector isn't available.

    Read-linearize over matching Embedding rows and rank in Python by
    cosine similarity. Fine for the dev/test dataset and for asserting on
    RAG semantics in tests.
    """

    name = "inmemory"

    def upsert(
        self,
        *,
        entity_type: str,
        entity_id: int,
        vector: list[float],
        model: str,
        version: str,
        dim: int,
    ) -> Embedding:
        obj, _ = Embedding.objects.update_or_create(
            entity_type=entity_type,
            entity_id=entity_id,
            model=model,
            version=version,
            defaults={"vector": vector, "dim": dim},
        )
        return obj

    def search_similar(
        self,
        query_vector: list[float],
        *,
        entity_type: str | None = None,
        top_k: int = 5,
        model: str | None = None,
        version: str | None = None,
    ) -> list[SimilarityHit]:
        qs = Embedding.objects.all()
        if entity_type is not None:
            qs = qs.filter(entity_type=entity_type)
        if model is not None:
            qs = qs.filter(model=model)
        if version is not None:
            qs = qs.filter(version=version)
        scored: list[SimilarityHit] = []
        for row in qs:
            stored = row.vector or []
            if not stored:
                continue
            score = _cosine(query_vector, stored)
            scored.append(
                SimilarityHit(
                    entity_type=row.entity_type,
                    entity_id=row.entity_id,
                    score=score,
                    embedding_id=row.id,
                )
            )
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:top_k]

    def delete(self, *, entity_type: str, entity_id: int) -> int:
        qs = Embedding.objects.filter(entity_type=entity_type, entity_id=entity_id)
        return qs.delete()[0]


class PgVectorStore:
    """PostgreSQL + pgvector similarity search via the <=> operator.

    Uses Django ORM annotations with pgvector.django.functions so the
    CosineDistance builtin maps to vector_cosine_ops. Only selected when
    the DB engine is postgresql and pgvector.django is in INSTALLED_APPS.
    """

    name = "pgvector"

    def upsert(
        self,
        *,
        entity_type: str,
        entity_id: int,
        vector: list[float],
        model: str,
        version: str,
        dim: int,
    ) -> Embedding:
        obj, _ = Embedding.objects.update_or_create(
            entity_type=entity_type,
            entity_id=entity_id,
            model=model,
            version=version,
            defaults={"vector": vector, "dim": dim},
        )
        return obj

    def search_similar(
        self,
        query_vector: list[float],
        *,
        entity_type: str | None = None,
        top_k: int = 5,
        model: str | None = None,
        version: str | None = None,
    ) -> list[SimilarityHit]:
        from pgvector.django import CosineDistance

        qs = Embedding.objects.all()
        if entity_type is not None:
            qs = qs.filter(entity_type=entity_type)
        if model is not None:
            qs = qs.filter(model=model)
        if version is not None:
            qs = qs.filter(version=version)
        qs = qs.annotate(distance=CosineDistance("vector", query_vector))
        qs = qs.order_by("distance")[:top_k]
        hits: list[SimilarityHit] = []
        for row in qs:
            # cosine distance is 1 - cosine similarity, so flip the sign.
            hits.append(
                SimilarityHit(
                    entity_type=row.entity_type,
                    entity_id=row.entity_id,
                    # If distance column is missing (e.g. NULL vector), treat as 0.
                    score=1.0 - float(getattr(row, "distance", 1.0) or 1.0),
                    embedding_id=row.id,
                )
            )
        return hits

    def delete(self, *, entity_type: str, entity_id: int) -> int:
        qs = Embedding.objects.filter(entity_type=entity_type, entity_id=entity_id)
        return qs.delete()[0]


def get_vector_store() -> VectorStore:
    if connection.vendor == "postgresql":
        return PgVectorStore()
    return InMemoryVectorStore()
