"""Token response helpers for authkit authentication flows."""

from __future__ import annotations

from rest_framework_simplejwt.tokens import RefreshToken

from authkit.users.serializers import CurrentUserSerializer


def build_token_response(user) -> dict[str, object]:
    """Build a reusable auth response payload for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "user": CurrentUserSerializer(user).data,
        "tokens": {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        },
    }
