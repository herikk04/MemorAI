"""DRF views backing the /api/v1/auth/ surface.

The JWT views live under MemorAI's central router (SDD 5.1). Each view
keeps the same SimpleJWT contract; we override only the token serializer
so the login response carries the user id and preferred language.
"""
from __future__ import annotations

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .serializers import LoginTokenSerializer


class LoginView(TokenObtainPairView):
    serializer_class = LoginTokenSerializer


class RefreshView(TokenRefreshView):
    pass


class VerifyView(TokenVerifyView):
    pass
