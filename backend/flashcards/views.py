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
        and returns the new card state + the created review.

        Body: {"rating": 1|2|3|4, "time_ms"?: int}
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

        # Audit history + pluggable slot for AI feedback (Sprint 2).
        review = Review.objects.create(
            card=card,
            user=request.user if request.user.is_authenticated else None,
            rating=rating,
            time_ms=time_ms,
            feedback_text="",            # populated by AI orchestrator in Sprint 2
            feedback_source="heuristic", # overwritten when AI feedback is attached
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
