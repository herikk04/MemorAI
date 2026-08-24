"""DRF serializers for the AI endpoints (RAG additions).

Kept in the same module as the feedback serializers so callers can find
all the AI request/response contracts in one place.
"""
from rest_framework import serializers


class FeedbackRequestSerializer(serializers.Serializer):
    """Input contract for POST /api/v1/ai/feedback/."""
    front = serializers.CharField(required=True)
    back = serializers.CharField(required=True)
    rating = serializers.IntegerField(min_value=1, max_value=4, required=True)
    time_ms = serializers.IntegerField(min_value=0, default=0)
    reps = serializers.IntegerField(min_value=0, default=0)
    lapses = serializers.IntegerField(min_value=0, default=0)
    language = serializers.CharField(max_length=8, default="pt")


class FeedbackResponseSerializer(serializers.Serializer):
    text = serializers.CharField()
    tokens_in = serializers.IntegerField()
    tokens_out = serializers.IntegerField()
    model = serializers.CharField()
    provider = serializers.CharField()
    status = serializers.CharField()
    prompt_version = serializers.CharField()
    cost_usd = serializers.FloatField()


class SearchRequestSerializer(serializers.Serializer):
    """Input contract for POST /api/v1/ai/search/."""
    query = serializers.CharField(required=True)
    top_k = serializers.IntegerField(min_value=1, max_value=50, default=8)


class SearchHitSerializer(serializers.Serializer):
    card_id = serializers.IntegerField()
    front = serializers.CharField()
    back = serializers.CharField()
    deck_id = serializers.IntegerField()
    deck_name = serializers.CharField()
    score = serializers.FloatField()


class SearchResponseSerializer(serializers.Serializer):
    query = serializers.CharField()
    status = serializers.CharField()
    model = serializers.CharField()
    provider = serializers.CharField()
    tokens = serializers.IntegerField()
    hits = SearchHitSerializer(many=True)


class SuggestionRequestSerializer(serializers.Serializer):
    """Input contract for POST /api/v1/ai/suggestions/."""
    top_k = serializers.IntegerField(min_value=1, max_value=50, default=10)


class SuggestionHitSerializer(serializers.Serializer):
    card_id = serializers.IntegerField()
    deck_id = serializers.IntegerField()
    deck_name = serializers.CharField()
    front = serializers.CharField()
    reason = serializers.CharField()
    due_in_seconds = serializers.IntegerField()


class SuggestionResponseSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(allow_null=True)
    status = serializers.CharField()
    hits = SuggestionHitSerializer(many=True)


class ReportMetricsSerializer(serializers.Serializer):
    total_reviews = serializers.IntegerField()
    total_lapses = serializers.IntegerField()
    avg_reps = serializers.FloatField()
    last_review_at = serializers.CharField(allow_blank=True)


class ReportResponseSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(allow_null=True)
    metrics = ReportMetricsSerializer()
    text = serializers.CharField()
    status = serializers.CharField()
    prompt_version = serializers.CharField()
    model = serializers.CharField()
    provider = serializers.CharField()
    tokens_in = serializers.IntegerField()
    tokens_out = serializers.IntegerField()


class TaskResultSerializer(serializers.Serializer):
    """Polling envelope for async AI jobs (Sprint 4)."""
    task_id = serializers.CharField()
    status = serializers.CharField()
    result = serializers.JSONField(required=False, allow_null=True)
