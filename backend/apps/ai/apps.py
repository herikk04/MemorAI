from django.apps import AppConfig


class AiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai"
    label = "ai"
    verbose_name = "AI core"

    def ready(self) -> None:
        # Importing the signals module wires the receivers at import time
        # AND keeps a strong reference (module-level) so Django's Signal
        # doesn't drop them via weakref, which was happening when the
        # receivers were nested functions inside ready().
        from . import signals  # noqa: F401
