"""Custom SimpleJWT serializer adding the user profile to the token pair.

SimpleJWT's default ``TokenObtainPairSerializer`` exposes only access /
refresh tokens. MemorAI's frontend needs the user id and preferred
language right after login so the SPA can pick i18n and route to the
dashboard; tacking them onto the response avoids an extra round-trip
to ``/me``.
"""
from __future__ import annotations

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class LoginTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Lightweight public claims; keep payload small and PII-free.
        token["username"] = user.get_username()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user_id"] = self.user.id
        data["username"] = self.user.get_username()
        # Profile row may not exist for legacy seeds; default to pt.
        language = "pt"
        profile = getattr(self.user, "profile", None)
        if profile is not None:
            language = profile.language
        data["language"] = language
        return data
