"""Views for authkit role APIs backed by Django Group."""

from __future__ import annotations

from django.contrib.auth.models import Group
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from authkit.audit_log.services import create_audit_log
from authkit.roles.permissions import IsRoleAdminWithModelPermission
from authkit.roles.serializers import (
    RoleSerializer,
    RoleUserAssignmentSerializer,
    RoleUsersSerializer,
)
from authkit.users.serializers import AdminUserSerializer


@extend_schema_view(
    list=extend_schema(
        operation_id="authkit_roles_list",
        summary="List roles",
        tags=["roles"],
    ),
    retrieve=extend_schema(
        operation_id="authkit_roles_retrieve",
        summary="Get role detail",
        tags=["roles"],
    ),
    create=extend_schema(
        operation_id="authkit_roles_create",
        summary="Create role",
        tags=["roles"],
    ),
    update=extend_schema(
        operation_id="authkit_roles_update",
        summary="Update role",
        tags=["roles"],
    ),
    partial_update=extend_schema(
        operation_id="authkit_roles_partial_update",
        summary="Partially update role",
        tags=["roles"],
    ),
    destroy=extend_schema(
        operation_id="authkit_roles_destroy",
        summary="Delete role",
        tags=["roles"],
    ),
)
class RoleViewSet(viewsets.ModelViewSet):
    """Manage roles using Django's built-in Group model."""

    queryset = Group.objects.all().order_by("name")
    serializer_class = RoleSerializer
    permission_classes = [IsRoleAdminWithModelPermission]
    http_method_names = ["get", "post", "put", "patch", "delete", "options", "head"]

    @extend_schema(
        operation_id="authkit_roles_assign_users",
        summary="Assign users to role",
        request=RoleUserAssignmentSerializer,
        responses={200: RoleSerializer},
        tags=["roles"],
    )
    @action(detail=True, methods=["post"], url_path="assign-users")
    def assign_users(self, request, pk=None):
        """Assign users to the role."""
        role = self.get_object()
        serializer = RoleUserAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        users = serializer.validated_data["user_ids"]
        for user in users:
            user.groups.add(role)
            create_audit_log(
                event_type="role_assigned",
                message="User assigned to role.",
                actor=request.user,
                target_user=user,
                request=request,
                metadata={"role_id": role.pk, "role_name": role.name},
            )
        return Response(self.get_serializer(role).data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="authkit_roles_remove_users",
        summary="Remove users from role",
        request=RoleUserAssignmentSerializer,
        responses={200: RoleSerializer},
        tags=["roles"],
    )
    @action(detail=True, methods=["post"], url_path="remove-users")
    def remove_users(self, request, pk=None):
        """Remove users from the role."""
        role = self.get_object()
        serializer = RoleUserAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        users = serializer.validated_data["user_ids"]
        for user in users:
            user.groups.remove(role)
            create_audit_log(
                event_type="role_removed",
                message="User removed from role.",
                actor=request.user,
                target_user=user,
                request=request,
                metadata={"role_id": role.pk, "role_name": role.name},
            )
        return Response(self.get_serializer(role).data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="authkit_roles_users",
        summary="List users in role",
        responses={200: RoleUsersSerializer},
        tags=["roles"],
    )
    @action(detail=True, methods=["get"])
    def users(self, request, pk=None):
        """List users assigned to the role."""
        role = self.get_object()
        users = role.user_set.all().order_by("email")
        return Response({"users": AdminUserSerializer(users, many=True).data})
