"""Views for authkit email verification APIs."""

from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authkit.api.permissions import AuthKitPublicEndpoint
from authkit.audit_log.services import create_audit_log
from authkit.verification.serializers import (
    VerificationConfirmSerializer,
    VerificationRequestSerializer,
)


class VerificationRequestView(APIView):
    """Request an email verification message."""

    authentication_classes: list[type] = []
    permission_classes = [AuthKitPublicEndpoint]

    @extend_schema(
        operation_id="authkit_verification_request",
        summary="Request email verification",
        request=VerificationRequestSerializer,
        responses={202: OpenApiResponse(description="Verification requested.")},
        tags=["verification"],
    )
    def post(self, request):
        """Accept verification requests without disclosing account existence."""
        serializer = VerificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        create_audit_log(
            event_type="email_verification_requested",
            message="Email verification requested.",
            request=request,
            metadata={"email": serializer.validated_data["email"]},
        )
        return Response(status=status.HTTP_202_ACCEPTED)


class VerificationConfirmView(APIView):
    """Verify an email address with a signed token."""

    authentication_classes: list[type] = []
    permission_classes = [AuthKitPublicEndpoint]

    @extend_schema(
        operation_id="authkit_verification_confirm",
        summary="Verify email address",
        request=VerificationConfirmSerializer,
        responses={204: OpenApiResponse(description="Email verified.")},
        tags=["verification"],
    )
    def post(self, request):
        """Validate the verification token and mark the user as verified."""
        serializer = VerificationConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        create_audit_log(
            event_type="email_verification_completed",
            message="Email verification completed.",
            target_user=user,
            request=request,
            metadata={"email": user.email},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
