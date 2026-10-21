"""DRF views backing the /api/v1/auth/ surface.

The JWT views live under MemorAI's central router (SDD 5.1). Each view
keeps the same SimpleJWT contract; we override only the token serializer
so the login response carries the user id and preferred language.
"""
from __future__ import annotations

from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .serializers import LoginTokenSerializer, RegisterSerializer


class LoginView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"
    serializer_class = LoginTokenSerializer


class RefreshView(TokenRefreshView):
    pass


class VerifyView(TokenVerifyView):
    pass


class RegisterView(generics.CreateAPIView):
    """POST /api/v1/auth/register/ creates the account and logs it in."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(serializer.to_representation(user), status=status.HTTP_201_CREATED)
