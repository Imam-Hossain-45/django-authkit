"""Views for authkit password reset APIs."""

from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authkit.api.permissions import AuthKitPublicEndpoint
from authkit.audit_log.services import create_audit_log
from authkit.password_reset.serializers import (
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
)


class PasswordResetRequestView(APIView):
    """Request a password reset email."""

    authentication_classes: list[type] = []
    permission_classes = [AuthKitPublicEndpoint]

    @extend_schema(
        operation_id="authkit_password_reset_request",
        summary="Request password reset",
        request=PasswordResetRequestSerializer,
        responses={202: OpenApiResponse(description="Password reset requested.")},
        tags=["password_reset"],
    )
    def post(self, request):
        """Accept reset requests without disclosing whether the email exists."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        create_audit_log(
            event_type="password_reset_requested",
            message="Password reset requested.",
            request=request,
            metadata={"email": serializer.validated_data["email"]},
        )
        return Response(status=status.HTTP_202_ACCEPTED)


class PasswordResetConfirmView(APIView):
    """Confirm a password reset with uid and token."""

    authentication_classes: list[type] = []
    permission_classes = [AuthKitPublicEndpoint]

    @extend_schema(
        operation_id="authkit_password_reset_confirm",
        summary="Confirm password reset",
        request=PasswordResetConfirmSerializer,
        responses={204: OpenApiResponse(description="Password reset confirmed.")},
        tags=["password_reset"],
    )
    def post(self, request):
        """Validate the reset token and set the new password."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        create_audit_log(
            event_type="password_reset_completed",
            message="Password reset completed.",
            target_user=user,
            request=request,
            metadata={"email": user.email},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
