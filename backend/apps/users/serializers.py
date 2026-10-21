"""Custom SimpleJWT serializer adding the user profile to the token pair.

SimpleJWT's default ``TokenObtainPairSerializer`` exposes only access /
refresh tokens. MemorAI's frontend needs the user id and preferred
language right after login so the SPA can pick i18n and route to the
dashboard; tacking them onto the response avoids an extra round-trip
to ``/me``.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Profile


class LoginTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Lightweight public claims; keep payload small and PII-free.
        token["username"] = user.get_username()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data.update(profile_payload(self.user))
        return data


def profile_payload(user) -> dict:
    """Public identity fields returned alongside the token pair."""
    # Profile row may not exist for legacy seeds; default to pt.
    profile = getattr(user, "profile", None)
    return {
        "user_id": user.id,
        "username": user.get_username(),
        "language": profile.language if profile is not None else "pt",
    }


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    language = serializers.ChoiceField(
        choices=Profile.Language.choices, default=Profile.Language.PT
    )

    def validate_username(self, value):
        if get_user_model().objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Username already taken.")
        return value

    def validate(self, attrs):
        user = get_user_model()(username=attrs["username"], email=attrs["email"])
        validate_password(attrs["password"], user=user)
        return attrs

    def create(self, validated_data):
        user = get_user_model().objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        Profile.objects.create(user=user, language=validated_data["language"])
        return user

    def to_representation(self, user):
        """Auto-login payload: same shape as the login response."""
        refresh = LoginTokenSerializer.get_token(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            **profile_payload(user),
        }
