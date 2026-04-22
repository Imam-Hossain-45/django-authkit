"""Serializers for authkit social authentication APIs."""

from __future__ import annotations

from rest_framework import serializers

from authkit.authentication.serializers import TokenPairSerializer
from authkit.authentication.tokens import build_token_response
from authkit.social_auth.exceptions import (
    InvalidSocialTokenError,
    ProviderUnavailableError,
)
from authkit.social_auth.providers import get_provider, list_providers
from authkit.social_auth.services import authenticate_social_identity
from authkit.users.serializers import CurrentUserSerializer


class SocialProviderSerializer(serializers.Serializer):
    """Serializer for public social provider metadata."""

    provider = serializers.CharField()
    name = serializers.CharField()
    authorization_url = serializers.URLField()
    client_id = serializers.CharField(allow_blank=True)
    scopes = serializers.ListField(child=serializers.CharField())


class SocialTokenExchangeSerializer(serializers.Serializer):
    """Exchange a provider token for local authkit credentials."""

    id_token = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Verify provider token and authenticate or link a local user."""
        provider_slug = self.context["provider"]
        provider = get_provider(provider_slug)
        if provider is None:
            raise serializers.ValidationError("Unsupported social auth provider.")

        try:
            identity = provider.verify_token(attrs["id_token"])
            result = authenticate_social_identity(identity)
        except (InvalidSocialTokenError, ProviderUnavailableError) as exc:
            raise serializers.ValidationError(str(exc)) from exc

        attrs["result"] = result
        return attrs

    def to_representation(self, instance):
        """Return user, tokens, and social account metadata."""
        result = instance["result"]
        payload = build_token_response(result.user)
        payload["social_account"] = {
            "id": str(result.social_account.pk),
            "provider": result.social_account.provider,
            "email": result.social_account.email,
            "created_user": result.created_user,
            "linked_account": result.linked_account,
        }
        return payload


class SocialAuthResponseSerializer(serializers.Serializer):
    """Serializer for social authentication responses."""

    user = CurrentUserSerializer(read_only=True)
    tokens = TokenPairSerializer(read_only=True)
    social_account = serializers.DictField(read_only=True)


def get_provider_metadata() -> list[dict[str, object]]:
    """Return metadata for all registered providers."""
    return [provider.get_metadata() for provider in list_providers()]
