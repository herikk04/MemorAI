from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


class AiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai"
    label = "ai"
    verbose_name = "AI core"

    def ready(self) -> None:
        # Imported here so the signals are registered when Django loads apps.
        # The lazy import also avoids importing flashcards at module import
        # time of this apps.py, which could create a circular dependency.
        from flashcards.models import Card

        from .services.rag_index import drop_card, reindex_card

        @receiver(post_save, sender=Card)
        def _on_card_saved(sender, instance, created, **kwargs):
            # Skip during raw saves (fixtures, migrations) to avoid spinning
            # the embeddings client on data already embedded.
            if kwargs.get("raw"):
                return
            # Re-embedding need not block the save call; for now we run it
            # synchronously since the mock client is cheap. Sprint 4 hands
            # this off to Celery when there's a queue configured.
            reindex_card(instance)

        @receiver(post_delete, sender=Card)
        def _on_card_deleted(sender, instance, **kwargs):
            if kwargs.get("raw"):
                return
            drop_card(instance)
