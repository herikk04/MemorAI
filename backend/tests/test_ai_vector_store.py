"""Tests for the VectorStore adapters (InMemory part, since tests run on SQLite)."""
from __future__ import annotations

import pytest

from apps.ai.models import Embedding
from apps.ai.services.vector_store import InMemoryVectorStore, get_vector_store


@pytest.mark.django_db
class TestInMemoryVectorStore:
    def setup_method(self):
        self.store = InMemoryVectorStore()
        # Upsert two embedding rows with distinct vectors.
        self.store.upsert(
            entity_type=Embedding.EntityType.CARD,
            entity_id=1,
            vector=[1.0, 0.0, 0.0],
            model="mock-embedding",
            version="1",
            dim=3,
        )
        self.store.upsert(
            entity_type=Embedding.EntityType.CARD,
            entity_id=2,
            vector=[0.0, 1.0, 0.0],
            model="mock-embedding",
            version="1",
            dim=3,
        )

    def test_upsert_creates_and_updates(self):
        assert Embedding.objects.count() == 2
        # Re-upserting same key updates the row, does not duplicate it.
        self.store.upsert(
            entity_type=Embedding.EntityType.CARD,
            entity_id=1,
            vector=[1.0, 0.0, 0.0],
            model="mock-embedding",
            version="1",
            dim=3,
        )
        assert Embedding.objects.count() == 2

    def test_search_returns_closest_first(self):
        hits = self.store.search_similar(
            [0.9, 0.1, 0.0],
            entity_type=Embedding.EntityType.CARD,
            top_k=2,
            model="mock-embedding",
        )
        assert len(hits) == 2
        # The query is much closer to entity 1 (cosine ~0.99) than entity 2 (~0.1).
        assert hits[0].entity_id == 1
        assert hits[0].score > hits[1].score

    def test_search_filters_by_entity_type(self):
        self.store.upsert(
            entity_type=Embedding.EntityType.DECK,
            entity_id=99,
            vector=[0.9, 0.1, 0.0],
            model="mock-embedding",
            version="1",
            dim=3,
        )
        hits = self.store.search_similar(
            [0.9, 0.1, 0.0],
            entity_type=Embedding.EntityType.CARD,
            top_k=5,
            model="mock-embedding",
        )
        assert all(h.entity_type == "card" for h in hits)

    def test_delete_removes_rows(self):
        n = self.store.delete(entity_type=Embedding.EntityType.CARD, entity_id=1)
        assert n == 1
        assert not Embedding.objects.filter(entity_id=1).exists()

    def test_top_k_limits_results(self):
        hits = self.store.search_similar(
            [1.0, 0.0, 0.0],
            entity_type=Embedding.EntityType.CARD,
            top_k=1,
            model="mock-embedding",
        )
        assert len(hits) == 1


def test_factory_uses_inmemory_on_sqlite():
    store = get_vector_store()
    assert isinstance(store, InMemoryVectorStore)
