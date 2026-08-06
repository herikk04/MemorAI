"""Signal receivers wiring Card <-> Embedding.

Receivers are module-level functions decorated with @receiver, holding
strong references so Django's Signal doesn't drop them via weakref
(which is what was happening when they were nested inside AppConfig.ready()).
"""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from flashcards.models import Card

from .services.rag_index import drop_card, reindex_card


@receiver(post_save, sender=Card)
def _on_card_saved(sender, instance, created, **kwargs):
    # Skip fixture/loaddata raw imports to keep embedding cost off data loads.
    if kwargs.get("raw"):
        return
    reindex_card(instance)


@receiver(post_delete, sender=Card)
def _on_card_deleted(sender, instance, **kwargs):
    if kwargs.get("raw"):
        return
    drop_card(instance)
