"""Views for authkit social authentication APIs."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authkit.api.permissions import AuthKitPublicEndpoint
from authkit.audit_log.services import create_audit_log
from authkit.social_auth.providers import get_provider
from authkit.social_auth.serializers import (
    SocialAuthResponseSerializer,
    SocialProviderSerializer,
    SocialTokenExchangeSerializer,
    get_provider_metadata,
)


class SocialProviderListView(APIView):
    """List configured social authentication providers."""

    authentication_classes: list[type] = []
    permission_classes = [AuthKitPublicEndpoint]

    @extend_schema(
        operation_id="authkit_social_auth_providers_list",
        summary="List social auth providers",
        responses={200: SocialProviderSerializer(many=True)},
        tags=["social_auth"],
    )
    def get(self, request):
        """Return public provider metadata."""
        return Response(get_provider_metadata())


class SocialProviderDetailView(APIView):
    """Return metadata for a single social authentication provider."""

    authentication_classes: list[type] = []
    permission_classes = [AuthKitPublicEndpoint]

    @extend_schema(
        operation_id="authkit_social_auth_provider_retrieve",
        summary="Get social auth provider metadata",
        responses={200: SocialProviderSerializer},
        tags=["social_auth"],
    )
    def get(self, request, provider: str):
        """Return provider metadata by slug."""
        social_provider = get_provider(provider)
        if social_provider is None:
            return Response(
                {"detail": "Unsupported social auth provider."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(social_provider.get_metadata())


class SocialTokenExchangeView(APIView):
    """Exchange a social provider token for authkit JWT credentials."""

    authentication_classes: list[type] = []
    permission_classes = [AuthKitPublicEndpoint]

    @extend_schema(
        operation_id="authkit_social_auth_token_exchange",
        summary="Exchange social provider token",
        request=SocialTokenExchangeSerializer,
        responses={200: SocialAuthResponseSerializer},
        tags=["social_auth"],
    )
    def post(self, request, provider: str):
        """Verify provider token and return local auth credentials."""
        serializer = SocialTokenExchangeSerializer(
            data=request.data,
            context={"request": request, "provider": provider},
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.validated_data["result"]
        event_type = (
            "social_auth_link" if result.linked_account else "social_auth_login"
        )
        create_audit_log(
            event_type=event_type,
            message="Social authentication completed.",
            actor=result.user,
            target_user=result.user,
            request=request,
            metadata={
                "provider": result.social_account.provider,
                "social_account_id": str(result.social_account.pk),
                "created_user": result.created_user,
                "linked_account": result.linked_account,
            },
        )
        return Response(serializer.data)
