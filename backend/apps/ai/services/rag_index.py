"""Service helpers for keeping Embedding rows in sync with flashcards.

We keep embedding generation out of Card.save() directly so bulk operations
admin imports, and tests can save without calling the LLM/embeddings. A
Django post_save signal (in apps.py:ready()) triggers reindex_card when
front/back change; the service itself is also callable from the admin and
from Sprint 4 Celery jobs.
"""
from __future__ import annotations

import logging

from django.db import transaction

from ..models import Embedding
from .embeddings import get_embedding_client
from .vector_store import get_vector_store

logger = logging.getLogger("apps.ai.embeddings")


_EMBEDDABLE_VERSION = "1"  # bump when the embedding logic changes meaningfully


def _card_text(card) -> str:
    """Compose the text that gets embedded for a card.

    We embed a concatenation of front and back so semantic search can find
    cards by either the question or its answer. Keep it deterministic.
    """
    return f"{card.front}\n\n{card.back}"


@transaction.atomic
def reindex_card(card) -> Embedding | None:
    """(Re)embed a Card and persist its latest Embedding.

    Returns the Embedding row on success or None when embedding fails.
    Failures are logged but not raised so callers (post_save signal,
    admin action, future Celery job) don't abort the save chain.
    """
    try:
        client = get_embedding_client()
        emb = client.embed(_card_text(card))
    except Exception as exc:  # noqa: BLE001
        logger.warning("reindex_card %s failed to embed: %s", card.id, exc)
        return None
    try:
        store = get_vector_store()
        return store.upsert(
            entity_type=Embedding.EntityType.CARD,
            entity_id=card.id,
            vector=emb.vector,
            model=emb.model,
            version=_EMBEDDABLE_VERSION,
            dim=len(emb.vector),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("reindex_card %s failed to store: %s", card.id, exc)
        return None


def drop_card(card) -> int:
    """Remove all Embedding rows for a card (used by post_delete signal)."""
    store = get_vector_store()
    return store.delete(entity_type=Embedding.EntityType.CARD, entity_id=card.id)
