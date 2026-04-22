"""Serializers for authkit authentication APIs."""

from __future__ import annotations

from typing import Any, cast

from django.contrib.auth import authenticate, password_validation
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from authkit.conf import authkit_settings
from authkit.models import User
from authkit.users.serializers import CurrentUserSerializer


class TokenPairSerializer(serializers.Serializer):
    """Serializer for JWT access and refresh token pairs."""

    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)


class AuthenticatedUserTokenSerializer(serializers.Serializer):
    """Serializer for responses that include a user and JWT token pair."""

    user = CurrentUserSerializer(read_only=True)
    tokens = TokenPairSerializer(read_only=True)


class RegisterSerializer(serializers.ModelSerializer):
    """Register a new authkit user with a Django-hashed password."""

    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name")
        extra_kwargs = {
            "first_name": {"required": False},
            "last_name": {"required": False},
        }

    def validate_email(self, value: str) -> str:
        """Normalize and enforce case-insensitive email uniqueness."""
        email = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate(self, attrs):
        """Run Django's configured password validators."""
        candidate = User(email=attrs.get("email", ""))
        password_validation.validate_password(attrs["password"], user=candidate)
        return attrs

    def create(self, validated_data):
        """Create a new user through the custom user manager."""
        password = validated_data.pop("password")
        try:
            return User.objects.create_user(password=password, **validated_data)
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            ) from exc


class LoginSerializer(serializers.Serializer):
    """Authenticate an active user with email and password."""

    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        """Authenticate credentials through Django's auth backend chain."""
        request = self.context.get("request")
        email = User.objects.normalize_email(attrs["email"])
        user = authenticate(request=request, username=email, password=attrs["password"])

        if user is None:
            raise serializers.ValidationError(
                "Unable to log in with the provided credentials.",
                code="authorization",
            )
        if not user.is_active:
            raise serializers.ValidationError(
                "This user account is inactive.",
                code="inactive",
            )
        if authkit_settings.REQUIRE_VERIFIED_LOGIN and not user.is_verified:
            raise serializers.ValidationError(
                "This user account is not verified.",
                code="unverified",
            )

        attrs["user"] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    """Validate a refresh token for logout handling."""

    refresh = serializers.CharField(write_only=True)

    def validate_refresh(self, value: str) -> str:
        """Ensure the provided refresh token is structurally valid."""
        RefreshToken(cast(Any, value))
        return value

    def save(self, **kwargs):
        """Blacklist the refresh token when blacklist support is installed."""
        token = RefreshToken(cast(Any, self.validated_data["refresh"]))
        blacklist = getattr(token, "blacklist", None)
        if callable(blacklist):
            blacklist()
        return None


class ChangePasswordSerializer(serializers.Serializer):
    """Change the authenticated user's password."""

    current_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )
    new_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    def validate_current_password(self, value: str) -> str:
        """Verify the current password before allowing a password change."""
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        """Run Django's configured password validators for the new password."""
        password_validation.validate_password(
            attrs["new_password"],
            user=self.context["request"].user,
        )
        return attrs

    def save(self, **kwargs):
        """Persist the new password using Django's password hasher."""
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        return user
