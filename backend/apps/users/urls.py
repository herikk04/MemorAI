"""Auth URL surface: /api/v1/auth/{login,refresh,verify}/.

Permissions:
    login   -> AllowAny (anyone with valid credentials gets a token)
    refresh -> AllowAny (token itself is the proof; rotation + blacklist
                protects the rotation chain)
    verify  -> AllowAny (the token is the credential)

All other MemorAI endpoints default to IsAuthenticated via
REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] (see settings/base.py).
"""
from django.urls import path
from rest_framework.permissions import AllowAny

from .views import LoginView, RefreshView, VerifyView

urlpatterns = [
    path("login/", LoginView.as_view(permission_classes=[AllowAny]), name="login"),
    path("refresh/", RefreshView.as_view(permission_classes=[AllowAny]), name="refresh"),
    path("verify/", VerifyView.as_view(permission_classes=[AllowAny]), name="verify"),
]
