"""Views for authkit authentication APIs."""

from __future__ import annotations

from django.contrib.auth import update_session_auth_hash
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenRefreshView

from authkit.api.permissions import AuthKitAuthenticated, AuthKitPublicEndpoint
from authkit.audit_log.services import create_audit_log
from authkit.authentication.serializers import (
    AuthenticatedUserTokenSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    RegisterSerializer,
)
from authkit.authentication.tokens import build_token_response
from authkit.conf import authkit_settings
from authkit.verification.email import send_email_verification_email


class RegisterView(APIView):
    """Register a new user and return JWT credentials."""

    authentication_classes: list[type] = []
    permission_classes = [AuthKitPublicEndpoint]

    @extend_schema(
        operation_id="authkit_auth_register",
        summary="Register a new user",
        request=RegisterSerializer,
        responses={201: AuthenticatedUserTokenSerializer},
        tags=["authentication"],
    )
    def post(self, request):
        """Create a new user with Django password hashing."""
        serializer = RegisterSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        create_audit_log(
            event_type="registration",
            message="User registered.",
            target_user=user,
            request=request,
            metadata={"email": user.email},
        )
        if authkit_settings.SEND_VERIFICATION_EMAIL_ON_REGISTER:
            send_email_verification_email(user)
        return Response(build_token_response(user), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Authenticate a user and return JWT credentials."""

    authentication_classes: list[type] = []
    permission_classes = [AuthKitPublicEndpoint]

    @extend_schema(
        operation_id="authkit_auth_login",
        summary="Log in with email and password",
        request=LoginSerializer,
        responses={200: AuthenticatedUserTokenSerializer},
        tags=["authentication"],
    )
    def post(self, request):
        """Authenticate through Django's auth backend chain."""
        serializer = LoginSerializer(data=request.data, context={"request": request})
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            create_audit_log(
                event_type="login_failure",
                message="Login failed.",
                request=request,
                metadata={"email": request.data.get("email", "")},
            )
            raise
        user = serializer.validated_data["user"]
        create_audit_log(
            event_type="login_success",
            message="User logged in.",
            actor=user,
            target_user=user,
            request=request,
            metadata={"email": user.email},
        )
        return Response(build_token_response(user))


class LogoutView(APIView):
    """Logout endpoint for refresh token invalidation or client token discard."""

    permission_classes = [AuthKitAuthenticated]

    @extend_schema(
        operation_id="authkit_auth_logout",
        summary="Log out by submitting a refresh token",
        request=LogoutSerializer,
        responses={204: OpenApiResponse(description="Logged out.")},
        tags=["authentication"],
    )
    def post(self, request):
        """Blacklist the refresh token when blacklist support is installed."""
        serializer = LogoutSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        create_audit_log(
            event_type="logout",
            message="User logged out.",
            actor=request.user,
            target_user=request.user,
            request=request,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class RefreshView(TokenRefreshView):
    """Refresh JWT access credentials using SimpleJWT."""

    permission_classes = [AuthKitPublicEndpoint]

    @extend_schema(
        operation_id="authkit_auth_refresh",
        summary="Refresh an access token",
        request=TokenRefreshSerializer,
        responses={200: OpenApiResponse(description="Access token refreshed.")},
        tags=["authentication"],
    )
    def post(self, request, *args, **kwargs):
        """Return a new access token for a valid refresh token."""
        return super().post(request, *args, **kwargs)


class ChangePasswordView(APIView):
    """Change the authenticated user's password."""

    permission_classes = [AuthKitAuthenticated]

    @extend_schema(
        operation_id="authkit_auth_change_password",
        summary="Change current user's password",
        request=ChangePasswordSerializer,
        responses={204: OpenApiResponse(description="Password changed.")},
        tags=["authentication"],
    )
    def post(self, request):
        """Change the current password using Django's password hasher."""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        update_session_auth_hash(request, user)
        create_audit_log(
            event_type="password_change",
            message="User changed password.",
            actor=user,
            target_user=user,
            request=request,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
