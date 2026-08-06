"""DRF views for the AI app endpoints (Sprint 2).

All endpoints sit under /api/v1/ai/ and delegate to the orchestrator.
No LLM client or prompt is imported here, so the boundary the SDD
defines (sec 3.3) is respected: views only talk to run_flow().
"""
from rest_framework import status
from rest_framework.permissions import AllowAny  # tightened in Sprint 1.5
from rest_framework.response import Response
from rest_framework.views import APIView

from .middleware import enforce_ai_quota
from .serializers import FeedbackRequestSerializer, FeedbackResponseSerializer
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
