"""Serializers for authkit password reset APIs."""

from __future__ import annotations

from django.contrib.auth import password_validation
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

from authkit.models import User
from authkit.password_reset.email import send_password_reset_email
from authkit.password_reset.tokens import password_reset_token_generator


class PasswordResetRequestSerializer(serializers.Serializer):
    """Request a password reset email without disclosing account existence."""

    email = serializers.EmailField()

    def save(self, **kwargs):
        """Send reset email for active matching users only."""
        email = User.objects.normalize_email(self.validated_data["email"])
        users = User.objects.filter(email__iexact=email, is_active=True)
        for user in users:
            if user.has_usable_password():
                send_password_reset_email(user)
        return None


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Confirm password reset using uid, token, and a new password."""

    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        """Validate uid, token, active user state, and new password strength."""
        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid password reset link.") from None

        if not password_reset_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError("Invalid password reset link.")

        password_validation.validate_password(attrs["new_password"], user=user)
        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        """Set the new password using Django's password hasher."""
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        return user
