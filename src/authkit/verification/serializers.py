"""Serializers for authkit email verification APIs."""

from __future__ import annotations

from django.core import signing
from rest_framework import serializers

from authkit.models import User
from authkit.verification.email import send_email_verification_email
from authkit.verification.tokens import load_email_verification_token


class VerificationRequestSerializer(serializers.Serializer):
    """Request a verification email without disclosing account existence."""

    email = serializers.EmailField()

    def save(self, **kwargs):
        """Send verification email for active unverified matching users only."""
        email = User.objects.normalize_email(self.validated_data["email"])
        users = User.objects.filter(
            email__iexact=email,
            is_active=True,
            is_verified=False,
        )
        for user in users:
            send_email_verification_email(user)
        return None


class VerificationConfirmSerializer(serializers.Serializer):
    """Verify a user's email address with a signed token."""

    token = serializers.CharField()

    def validate(self, attrs):
        """Validate the signed token and resolve the target user."""
        try:
            payload = load_email_verification_token(attrs["token"])
            user = User.objects.get(pk=payload["user_id"], is_active=True)
        except (
            KeyError,
            TypeError,
            ValueError,
            signing.BadSignature,
            signing.SignatureExpired,
            User.DoesNotExist,
        ):
            raise serializers.ValidationError("Invalid verification token.") from None

        if (
            payload.get("email") != user.email
            or payload.get("password") != user.password
        ):
            raise serializers.ValidationError("Invalid verification token.")

        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        """Mark the user email/account as verified."""
        user = self.validated_data["user"]
        if not user.is_verified:
            user.is_verified = True
            user.save(update_fields=["is_verified", "updated_at"])
        return user
