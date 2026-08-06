"""DRF views for the AI app endpoints (Sprint 2 + RAG additions).

All endpoints sit under /api/v1/ai/ and delegate to the orchestrator.
No LLM client or prompt is imported here, so the boundary the SDD
defines (sec 3.3) is respected: views only talk to run_flow().
"""
from rest_framework import status
from rest_framework.permissions import AllowAny  # tightened in Sprint 1.5
from rest_framework.response import Response
from rest_framework.views import APIView

from .middleware import enforce_ai_quota
from .serializers import (
    FeedbackRequestSerializer,
    FeedbackResponseSerializer,
    ReportResponseSerializer,
    SearchHitSerializer,
    SearchRequestSerializer,
    SuggestionRequestSerializer,
    SuggestionResponseSerializer,
    TaskResultSerializer,
)
from .services.orchestrator import run_flow


class FeedbackView(APIView):
    permission_classes = [AllowAny]

    @enforce_ai_quota
    def post(self, request):
        in_s = FeedbackRequestSerializer(data=request.data)
        in_s.is_valid(raise_exception=True)
        data = in_s.validated_data
        language = data.pop("language")

        result = run_flow(
            "feedback",
            data,
            language=language,
            user=request.user if request.user.is_authenticated else None,
        )
        out_s = FeedbackResponseSerializer(result)
        return Response(out_s.data, status=status.HTTP_200_OK)


class SearchView(APIView):
    """POST /api/v1/ai/search/ — semantic search over flashcards."""

    permission_classes = [AllowAny]

    @enforce_ai_quota
    def post(self, request):
        in_s = SearchRequestSerializer(data=request.data)
        in_s.is_valid(raise_exception=True)
        data = in_s.validated_data

        result = run_flow(
            "rag",
            {"query": data["query"], "top_k": data["top_k"]},
            language="pt",
            user=request.user if request.user.is_authenticated else None,
        )
        # SearchResponseSerializer is a plain DictSerializer; build it directly.
        hits = SearchHitSerializer(result.hits, many=True).data
        return Response(
            {
                "query": result.query,
                "status": result.status,
                "model": result.model,
                "provider": result.provider,
                "tokens": result.tokens,
                "hits": hits,
            },
            status=status.HTTP_200_OK,
        )


class ReportView(APIView):
    """GET /api/v1/ai/report/ — personalized evolution report (async job).

    Dispatches the Celery job and returns the finished report in eager
    mode (dev/test). In async mode it returns a task_id the client polls
    via GET /api/v1/ai/tasks/{task_id}/.
    """

    permission_classes = [AllowAny]

    @enforce_ai_quota
    def get(self, request):
        from .tasks import generate_report_task

        language = request.query_params.get("language", "pt")
        user = request.user if request.user.is_authenticated else None

        task = generate_report_task.delay(user.id if user else None, language)
        if not task.successful():
            out_s = TaskResultSerializer(
                {"task_id": task.id, "status": task.status}
            )
            return Response(out_s.data, status=status.HTTP_202_ACCEPTED)

        out_s = ReportResponseSerializer(task.result)
        return Response(out_s.data, status=status.HTTP_200_OK)


class SuggestionView(APIView):
    """POST /api/v1/ai/suggestions/ — ranked cards to review next.

    Heuristic flow (no LLM). Returns the list directly in eager mode and
    a task_id for polling in async mode.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        from .tasks import generate_suggestions_task

        in_s = SuggestionRequestSerializer(data=request.data)
        in_s.is_valid(raise_exception=True)
        top_k = in_s.validated_data["top_k"]
        user = request.user if request.user.is_authenticated else None

        task = generate_suggestions_task.delay(user.id if user else None, top_k)
        if not task.successful():
            out_s = TaskResultSerializer(
                {"task_id": task.id, "status": task.status}
            )
            return Response(out_s.data, status=status.HTTP_202_ACCEPTED)

        out_s = SuggestionResponseSerializer(task.result)
        return Response(out_s.data, status=status.HTTP_200_OK)


class TaskResultView(APIView):
    """GET /api/v1/ai/tasks/{task_id}/ — poll an async AI job's result."""

    permission_classes = [AllowAny]

    def get(self, request, task_id):
        from .tasks import generate_report_task, generate_suggestions_task

        async_result = generate_report_task.AsyncResult(task_id)
        if async_result.successful():
            out_s = TaskResultSerializer(
                {
                    "task_id": task_id,
                    "status": async_result.status,
                    "result": async_result.result,
                }
            )
            return Response(out_s.data, status=status.HTTP_200_OK)
        if async_result.failed():
            out_s = TaskResultSerializer(
                {"task_id": task_id, "status": async_result.status}
            )
            return Response(out_s.data, status=status.HTTP_200_OK)

        # Not found via report task: try the suggestion task.
        async_result = generate_suggestions_task.AsyncResult(task_id)
        out_s = TaskResultSerializer(
            {
                "task_id": task_id,
                "status": async_result.status,
                "result": async_result.result if async_result.successful() else None,
            }
        )
        http_status = (
            status.HTTP_200_OK if async_result.successful() else status.HTTP_202_ACCEPTED
        )
        return Response(out_s.data, status=http_status)
