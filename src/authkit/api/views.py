"""Foundation API views for django-authkit."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from authkit import __version__
from authkit.api.permissions import AuthKitPublicEndpoint


class AuthKitInfoView(APIView):
    """Expose package metadata to verify authkit API routing."""

    authentication_classes: list[type] = []
    permission_classes = [AuthKitPublicEndpoint]

    @extend_schema(
        operation_id="authkit_info",
        summary="Get django-authkit package information",
        tags=["authkit"],
    )
    def get(self, request):
        """Return package identity and version information."""
        return Response(
            {
                "name": "django-authkit",
                "package": "authkit",
                "version": __version__,
            }
        )
