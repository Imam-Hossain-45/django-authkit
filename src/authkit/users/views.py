"""Views for authkit user APIs."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.response import Response

from authkit.api.permissions import AuthKitVerifiedIfRequired
from authkit.models import User
from authkit.users.permissions import IsUserAdminWithModelPermission
from authkit.users.serializers import AdminUserSerializer, CurrentUserSerializer


@extend_schema_view(
    get=extend_schema(
        operation_id="authkit_users_me_retrieve",
        summary="Get current authenticated user",
        tags=["users"],
    ),
    patch=extend_schema(
        operation_id="authkit_users_me_partial_update",
        summary="Partially update current authenticated user",
        tags=["users"],
    ),
    put=extend_schema(
        operation_id="authkit_users_me_update",
        summary="Update current authenticated user",
        tags=["users"],
    ),
)
class CurrentUserView(RetrieveUpdateAPIView):
    """Retrieve and update the authenticated user's own profile fields."""

    serializer_class = CurrentUserSerializer
    permission_classes = [AuthKitVerifiedIfRequired]
    http_method_names = ["get", "put", "patch", "options", "head"]

    def get_object(self):
        """Return the authenticated user without a URL lookup."""
        return self.request.user


@extend_schema_view(
    list=extend_schema(
        operation_id="authkit_admin_users_list",
        summary="List users",
        tags=["users"],
    ),
    retrieve=extend_schema(
        operation_id="authkit_admin_users_retrieve",
        summary="Get user detail",
        tags=["users"],
    ),
    create=extend_schema(
        operation_id="authkit_admin_users_create",
        summary="Create user",
        tags=["users"],
    ),
    update=extend_schema(
        operation_id="authkit_admin_users_update",
        summary="Update user",
        tags=["users"],
    ),
    partial_update=extend_schema(
        operation_id="authkit_admin_users_partial_update",
        summary="Partially update user",
        tags=["users"],
    ),
)
class AdminUserViewSet(viewsets.ModelViewSet):
    """Staff-only user management backed by Django model permissions."""

    queryset = User.objects.all().order_by("email")
    serializer_class = AdminUserSerializer
    permission_classes = [IsUserAdminWithModelPermission]
    http_method_names = ["get", "post", "put", "patch", "options", "head"]

    @extend_schema(
        operation_id="authkit_admin_users_activate",
        summary="Activate user",
        request=None,
        responses=AdminUserSerializer,
        tags=["users"],
    )
    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Mark a user account as active."""
        user = self.get_object()
        user.is_active = True
        user.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(user).data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="authkit_admin_users_deactivate",
        summary="Deactivate user",
        request=None,
        responses=AdminUserSerializer,
        tags=["users"],
    )
    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """Mark a user account as inactive."""
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(user).data, status=status.HTTP_200_OK)
