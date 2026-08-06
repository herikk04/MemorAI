"""Quota enforcement decorator for AI endpoints.

Use:
    class FeedbackView(APIView):
        @enforce_ai_quota
        def post(self, request):
            ...

Returns 429 with `{"detail": ..., "reason": ...}` if the authenticated user
has already burned their AI_DAILY_TOKEN_CAP_PER_USER or
AI_DAILY_COST_CAP_USD. Anonymous requests pass through; anonymous users
have no AIUsage rows so they skip the cap entirely.
"""
from __future__ import annotations

import logging
from functools import wraps

from rest_framework import status
from rest_framework.response import Response

from .services.orchestrator import quota_exceeded

logger = logging.getLogger("apps.ai.middleware")


def enforce_ai_quota(view_func):
    @wraps(view_func)
    def _wrapped(self, request, *args, **kwargs):
        exceeded, reason = quota_exceeded(request.user)
        if exceeded:
            logger.info(
                "ai quota exceeded for user=%s reason=%s",
                getattr(request.user, "pk", None),
                reason,
            )
            return Response(
                {"detail": "Daily AI quota exceeded.", "reason": reason},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        return view_func(self, request, *args, **kwargs)

    return _wrapped
