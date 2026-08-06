"""RAS flow: semantic search over cards and decks.

Given a natural-language query (e.g. "como iterar um dicionario em
Python"), embed it with the active EmbeddingClient, query the
VectorStore for the closest cards, and return hits with their decks so
the UI can render "decks parecidos com sua pergunta".

The flow always returns a RagResult, never raises. On embedding errors
or empty stores it returns an empty hits list with status degraded so
the API can fall back to a plain text search later without breaking.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ..models import AIEvent
from ..services.embeddings import get_embedding_client
from ..services.vector_store import SimilarityHit, get_vector_store

logger = logging.getLogger("apps.ai.flows.rag")


@dataclass
class RagCardHit:
    card_id: int
    front: str
    back: str
    deck_id: int
    deck_name: str
    score: float


@dataclass
class RagResult:
    query: str
    hits: list[RagCardHit] = field(default_factory=list)
    status: str = AIEvent.Status.SUCCESS
    error: str = ""
    model: str = ""
    provider: str = ""
    tokens: int = 0


def _hits_to_cards(hits: list[SimilarityHit]) -> list[RagCardHit]:
    """Resolve similarity hits into card + deck rows.

    Done with a single query per type to avoid N+1 reads. Falls back
    silently if a referenced entity no longer exists (the index might be
    stale while Sprint 4 backfills a re-embedding job).
    """
    if not hits:
        return []
    from flashcards.models import Card

    card_ids = [h.entity_id for h in hits if h.entity_type == "card"]
    if not card_ids:
        return []
    cards = Card.objects.select_related("deck").in_bulk(card_ids)
    out: list[RagCardHit] = []
    score_by_id = {h.entity_id: h.score for h in hits if h.entity_type == "card"}
    for cid, score in score_by_id.items():
        card = cards.get(cid)
        if card is None:
            continue
        out.append(
            RagCardHit(
                card_id=card.id,
                front=card.front,
                back=card.back,
                deck_id=card.deck_id,
                deck_name=card.deck.name,
                score=round(score, 4),
            )
        )
    return out


def run_rag(payload: dict[str, Any], *, language: str = "pt", user=None) -> RagResult:
    """Run the RAG flow.

    payload must contain "query" (str). Optional "top_k" (int, default 8).
    language is unused by the embedding model but kept for run_flow
    signature uniformity so the orchestrator can dispatch uniformly.
    Always returns a RagResult. Never raises.
    """
    query = str(payload.get("query", "")).strip()
    top_k = int(payload.get("top_k", 8) or 8)
    if not query:
        return RagResult(query="", status=AIEvent.Status.ERROR, error="empty query")

    try:
        client = get_embedding_client()
        emb = client.embed(query)
    except Exception as exc:  # noqa: BLE001
        logger.warning("rag embed failed: %s", exc)
        return RagResult(
            query=query,
            status=AIEvent.Status.ERROR,
            error=str(exc)[:256],
        )

    try:
        store = get_vector_store()
        hits = store.search_similar(
            emb.vector,
            entity_type="card",
            top_k=top_k,
            model=emb.model,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("rag search failed: %s", exc)
        return RagResult(
            query=query,
            status=AIEvent.Status.ERROR,
            error=str(exc)[:256],
            model=emb.model,
            provider=emb.provider,
            tokens=emb.tokens,
        )

    card_hits = _hits_to_cards(hits)

    # Audit hook: a single AIEvent summarises the RAG call. Sprint 4 may
    # use a dedicated "rag" flow registry for the prompt_versionerner;
    # for now we record the model as prompt_version so the admin filter
    # still works.
    AIEvent.objects.create(
        user=user if (user is not None and getattr(user, "is_authenticated", False)) else None,
        flow="rag",
        prompt_version=emb.model,
        model=emb.model,
        provider=emb.provider,
        tokens_in=emb.tokens,
        tokens_out=0,
        cost_usd=0,  # embeddings pricing is per-token; wire in S4 cost table
        latency_ms=0,
        status=AIEvent.Status.SUCCESS,
        error="",
    )

    return RagResult(
        query=query,
        hits=card_hits,
        status=AIEvent.Status.SUCCESS,
        model=emb.model,
        provider=emb.provider,
        tokens=emb.tokens,
    )
