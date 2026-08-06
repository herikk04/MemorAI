from django.contrib import admin

from .models import AIEvent, AIUsage


@admin.register(AIEvent)
class AIEventAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "flow", "model", "status", "tokens_in", "tokens_out", "cost_usd", "latency_ms", "created_at")
    list_filter = ("status", "flow", "provider")
    search_fields = ("flow", "error", "prompt_hash")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"


@admin.register(AIUsage)
class AIUsageAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "day", "calls", "tokens_in", "tokens_out", "cost_usd")
    list_filter = ("day",)
    date_hierarchy = "day"
