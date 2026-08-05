from rest_framework import serializers

from .models import Card, Deck, Review


class CardSerializer(serializers.ModelSerializer):
    srs_algorithm = serializers.ChoiceField(
        choices=Card.SRSAlgorithm.choices, default=Card.SRSAlgorithm.FSRS
    )
    due = serializers.DateTimeField(read_only=True)
    last_reviewed_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Card
        fields = [
            "id",
            "deck",
            "front",
            "back",
            # SRS state is read-only via the serializer; mutations only happen
            # through the review endpoint so the scheduler is the single writer.
            "interval",
            "ease",
            "reps",
            "lapses",
            "due",
            "last_reviewed_at",
            "srs_algorithm",
        ]
        read_only_fields = ["interval", "ease", "reps", "lapses", "due", "last_reviewed_at"]


class DeckSerializer(serializers.ModelSerializer):
    cards = CardSerializer(many=True, read_only=True)

    class Meta:
        model = Deck
        fields = ["id", "name", "description", "cards"]


class ReviewCreateSerializer(serializers.Serializer):
    """Input contract for POST /cards/{id}/review/."""
    rating = serializers.ChoiceField(choices=Review.Rating.choices)
    time_ms = serializers.IntegerField(min_value=0, default=0)


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            "id",
            "card",
            "rating",
            "reviewed_at",
            "time_ms",
            "feedback_text",
            "feedback_source",
        ]
        read_only_fields = ["reviewed_at", "feedback_text", "feedback_source"]


class CardScheduleStateSerializer(serializers.ModelSerializer):
    """Read-only view of a card's SRS state after a review."""

    class Meta:
        model = Card
        fields = [
            "id",
            "interval",
            "ease",
            "reps",
            "lapses",
            "due",
            "last_reviewed_at",
            "srs_algorithm",
        ]
