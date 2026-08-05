from django.contrib import admin

from .models import Card, Deck, Review


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name", "description")


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "deck",
        "front",
        "srs_algorithm",
        "reps",
        "lapses",
        "due",
    )
    list_filter = ("srs_algorithm", "deck")
    search_fields = ("front", "back")
    readonly_fields = (
        "interval",
        "ease",
        "reps",
        "lapses",
        "due",
        "last_reviewed_at",
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "card", "user", "rating", "reviewed_at", "feedback_source")
    list_filter = ("rating", "feedback_source")
    readonly_fields = ("reviewed_at",)
