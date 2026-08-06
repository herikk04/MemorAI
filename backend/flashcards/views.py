import logging

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Card, Deck, Review
from .serializers import (
    CardSerializer,
    DeckSerializer,
    ReviewCreateSerializer,
    ReviewSerializer,
)
from .services.scheduler import schedule_review

logger = logging.getLogger("flashcards.review")


class DeckViewSet(viewsets.ModelViewSet):
    queryset = Deck.objects.all()
    serializer_class = DeckSerializer


class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer

    @action(detail=True, methods=["post"], url_path="review")
    def review(self, request, pk=None):
        """POST /api/v1/cards/{id}/review/

        Records a Review, advances the card's SRS state via the scheduler,
        attaches an AI-generated explanation to the Review (Sprint 2) and
        returns the new card state + the created review.

        Body: {"rating": 1|2|3|4, "time_ms"?: int}

        The AI feedback is best-effort. Per the SDD (sec 3.2) the AI never
        blocks the UX: if the LLM is unavailable or fails, the response
        still carries the new SRS state plus a heuristic explanation, and
        the Review.feedback_source records where the text came from.
        """
        card = self.get_object()
        in_serializer = ReviewCreateSerializer(data=request.data)
        in_serializer.is_valid(raise_exception=True)
        rating = in_serializer.validated_data["rating"]
        time_ms = in_serializer.validated_data["time_ms"]

        update = schedule_review(card=card, rating=rating, now=timezone.now())

        # Persist the scheduler's new state on the card.
        card.interval = update.interval
        card.ease = update.ease
        card.reps = update.reps
        card.lapses = update.lapses
        card.due = update.due
        card.last_reviewed_at = update.last_reviewed_at
        card.save(
            update_fields=[
                "interval",
                "ease",
                "reps",
                "lapses",
                "due",
                "last_reviewed_at",
            ]
        )

        # AI feedback (best-effort). Lazy import keeps the boundary one-way:
        # flashcards depends on orchestrator, never on prompts or clients.
        feedback_text = ""
        feedback_source = "heuristic"
        try:
            from apps.ai.services.orchestrator import run_flow

            result = run_flow(
                "feedback",
                {
                    "front": card.front,
                    "back": card.back,
                    "rating": rating,
                    "time_ms": time_ms,
                    "reps": update.reps,
                    "lapses": update.lapses,
                },
                language="pt",
                user=request.user if request.user.is_authenticated else None,
            )
            feedback_text = result.text
            feedback_source = (
                "ai:feedback"
                if result.status == "success"
                else f"ai:{result.status}"
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("AI feedback failed; falling back to heuristic: %s", exc)

        review = Review.objects.create(
            card=card,
            user=request.user if request.user.is_authenticated else None,
            rating=rating,
            time_ms=time_ms,
            feedback_text=feedback_text,
            feedback_source=feedback_source,
        )

        return Response(
            {
                "card": CardSerializer(card).data,
                "review": ReviewSerializer(review).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="due")
    def due(self, request):
        """GET /api/v1/cards/due/ — cards whose next review is now overdue."""
        now = timezone.now()
        cards = self.get_queryset().filter(due__lte=now)
        page = self.paginate_queryset(cards)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(cards, many=True)
        return Response(serializer.data)
