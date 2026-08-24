from django.db import models


class Deck(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    # Sprint 1.5: decks are owned by a user. Nullable so existing
    # seeded decks keep working; the API layer (views + serializer) sets
    # owner=request.user on create and scopes the queryset accordingly.
    owner = models.ForeignKey(
        "auth.User",
        related_name="decks",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Card(models.Model):
    class SRSAlgorithm(models.TextChoices):
        FSRS = "fsrs", "FSRS"
        SM2 = "sm2", "SM-2"
        ANKI = "anki", "Anki"

    deck = models.ForeignKey(
        Deck, related_name="cards", on_delete=models.CASCADE
    )
    front = models.TextField()
    back = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- Spaced repetition state (Sprint 1) ---
    # interval is in days (FloatField to support sub-day intervals early on).
    interval = models.FloatField(default=0.0)
    ease = models.FloatField(default=2.5)
    reps = models.PositiveIntegerField(default=0)
    lapses = models.PositiveIntegerField(default=0)
    due = models.DateTimeField(null=True, blank=True)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    srs_algorithm = models.CharField(
        max_length=8,
        choices=SRSAlgorithm.choices,
        default=SRSAlgorithm.FSRS,
    )

    def __str__(self):
        return f"Card: {self.front[:50]}..."


class Review(models.Model):
    class Rating(models.IntegerChoices):
        AGAIN = 1, "Again"
        HARD = 2, "Hard"
        GOOD = 3, "Good"
        EASY = 4, "Easy"

    # Redundant FK to user kept nullable for now: auth is wired in Sprint 1.5
    # so existing cards/tests keep working without a logged-in user.
    user = models.ForeignKey(
        "auth.User",
        related_name="reviews",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    card = models.ForeignKey(
        Card, related_name="reviews", on_delete=models.CASCADE
    )
    rating = models.IntegerField(choices=Rating.choices)
    reviewed_at = models.DateTimeField(auto_now_add=True)
    time_ms = models.PositiveIntegerField(default=0)
    # Filled by the AI orchestrator (Sprint 2); stored here for history.
    feedback_text = models.TextField(blank=True, default="")
    feedback_source = models.CharField(
        max_length=16,
        blank=True,
        default="",
        help_text="Where the feedback came from (e.g. 'ai:feedback', 'heuristic').",
    )

    class Meta:
        ordering = ["-reviewed_at"]
        indexes = [
            models.Index(fields=["card", "-reviewed_at"]),
            models.Index(fields=["user", "-reviewed_at"]),
        ]

    def __str__(self):
        return f"Review({self.card_id}, {self.get_rating_display()})"
