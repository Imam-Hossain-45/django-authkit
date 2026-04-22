"""Views for authkit permission APIs."""

from __future__ import annotations

from django.contrib.auth.models import Group, Permission
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from authkit.audit_log.services import create_audit_log
from authkit.models import User
from authkit.permissions.permissions import IsPermissionAdminWithModelPermission
from authkit.permissions.serializers import (
    PermissionAssignmentSerializer,
    PermissionListSerializer,
    PermissionSerializer,
)


@extend_schema_view(
    list=extend_schema(
        operation_id="authkit_permissions_list",
        summary="List permissions",
        tags=["permissions"],
    ),
    retrieve=extend_schema(
        operation_id="authkit_permissions_retrieve",
        summary="Get permission detail",
        tags=["permissions"],
    ),
)
class PermissionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Read and manage Django permissions and assignments."""

    queryset = Permission.objects.select_related("content_type").order_by(
        "content_type__app_label",
        "content_type__model",
        "codename",
    )
    serializer_class = PermissionSerializer
    permission_classes = [IsPermissionAdminWithModelPermission]
    http_method_names = ["get", "post", "options", "head"]

    @extend_schema(
        operation_id="authkit_permissions_role_list",
        summary="List permissions of a role",
        parameters=[
            OpenApiParameter("role_id", int, OpenApiParameter.PATH),
        ],
        responses={200: PermissionListSerializer},
        tags=["permissions"],
    )
    @action(
        detail=False,
        methods=["get"],
        url_path=r"roles/(?P<role_id>[^/.]+)",
    )
    def role_permissions(self, request, role_id=None):
        """List permissions assigned to a role/group."""
        role = self.get_role(role_id)
        permissions = role.permissions.select_related("content_type").order_by(
            "content_type__app_label",
            "content_type__model",
            "codename",
        )
        return Response(
            {"permissions": PermissionSerializer(permissions, many=True).data}
        )

    @extend_schema(
        operation_id="authkit_permissions_role_assign",
        summary="Assign permissions to a role",
        parameters=[
            OpenApiParameter("role_id", int, OpenApiParameter.PATH),
        ],
        request=PermissionAssignmentSerializer,
        responses={200: PermissionListSerializer},
        tags=["permissions"],
    )
    @action(
        detail=False,
        methods=["post"],
        url_path=r"roles/(?P<role_id>[^/.]+)/assign",
    )
    def assign_to_role(self, request, role_id=None):
        """Assign permissions to a role/group."""
        role = self.get_role(role_id)
        serializer = PermissionAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        permissions = serializer.validated_data["permission_ids"]
        role.permissions.add(*permissions)
        for permission in permissions:
            permission_label = (
                f"{permission.content_type.app_label}.{permission.codename}"
            )
            create_audit_log(
                event_type="permission_assigned_to_role",
                message="Permission assigned to role.",
                actor=request.user,
                request=request,
                metadata={
                    "role_id": role.pk,
                    "role_name": role.name,
                    "permission_id": permission.pk,
                    "permission": permission_label,
                },
            )
        return self.role_permissions(request, role_id=role_id)

    @extend_schema(
        operation_id="authkit_permissions_role_remove",
        summary="Remove permissions from a role",
        parameters=[
            OpenApiParameter("role_id", int, OpenApiParameter.PATH),
        ],
        request=PermissionAssignmentSerializer,
        responses={200: PermissionListSerializer},
        tags=["permissions"],
    )
    @action(
        detail=False,
        methods=["post"],
        url_path=r"roles/(?P<role_id>[^/.]+)/remove",
    )
    def remove_from_role(self, request, role_id=None):
        """Remove permissions from a role/group."""
        role = self.get_role(role_id)
        serializer = PermissionAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        permissions = serializer.validated_data["permission_ids"]
        role.permissions.remove(*permissions)
        for permission in permissions:
            permission_label = (
                f"{permission.content_type.app_label}.{permission.codename}"
            )
            create_audit_log(
                event_type="permission_removed_from_role",
                message="Permission removed from role.",
                actor=request.user,
                request=request,
                metadata={
                    "role_id": role.pk,
                    "role_name": role.name,
                    "permission_id": permission.pk,
                    "permission": permission_label,
                },
            )
        return self.role_permissions(request, role_id=role_id)

    @extend_schema(
        operation_id="authkit_permissions_user_list",
        summary="List direct permissions of a user",
        parameters=[
            OpenApiParameter("user_id", OpenApiTypes.UUID, OpenApiParameter.PATH),
        ],
        responses={200: PermissionListSerializer},
        tags=["permissions"],
    )
    @action(
        detail=False,
        methods=["get"],
        url_path=r"users/(?P<user_id>[^/.]+)",
    )
    def user_permissions(self, request, user_id=None):
        """List direct permissions assigned to a user."""
        user = self.get_user(user_id)
        permissions = user.user_permissions.select_related("content_type").order_by(
            "content_type__app_label",
            "content_type__model",
            "codename",
        )
        return Response(
            {"permissions": PermissionSerializer(permissions, many=True).data}
        )

    @extend_schema(
        operation_id="authkit_permissions_user_assign",
        summary="Assign direct permissions to a user",
        parameters=[
            OpenApiParameter("user_id", OpenApiTypes.UUID, OpenApiParameter.PATH),
        ],
        request=PermissionAssignmentSerializer,
        responses={200: PermissionListSerializer},
        tags=["permissions"],
    )
    @action(
        detail=False,
        methods=["post"],
        url_path=r"users/(?P<user_id>[^/.]+)/assign",
    )
    def assign_to_user(self, request, user_id=None):
        """Assign direct permissions to a user."""
        user = self.get_user(user_id)
        serializer = PermissionAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        permissions = serializer.validated_data["permission_ids"]
        user.user_permissions.add(*permissions)
        for permission in permissions:
            permission_label = (
                f"{permission.content_type.app_label}.{permission.codename}"
            )
            create_audit_log(
                event_type="permission_assigned_to_user",
                message="Permission assigned to user.",
                actor=request.user,
                target_user=user,
                request=request,
                metadata={
                    "permission_id": permission.pk,
                    "permission": permission_label,
                },
            )
        return self.user_permissions(request, user_id=user_id)

    @extend_schema(
        operation_id="authkit_permissions_user_remove",
        summary="Remove direct permissions from a user",
        parameters=[
            OpenApiParameter("user_id", OpenApiTypes.UUID, OpenApiParameter.PATH),
        ],
        request=PermissionAssignmentSerializer,
        responses={200: PermissionListSerializer},
        tags=["permissions"],
    )
    @action(
        detail=False,
        methods=["post"],
        url_path=r"users/(?P<user_id>[^/.]+)/remove",
    )
    def remove_from_user(self, request, user_id=None):
        """Remove direct permissions from a user."""
        user = self.get_user(user_id)
        serializer = PermissionAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        permissions = serializer.validated_data["permission_ids"]
        user.user_permissions.remove(*permissions)
        for permission in permissions:
            permission_label = (
                f"{permission.content_type.app_label}.{permission.codename}"
            )
            create_audit_log(
                event_type="permission_removed_from_user",
                message="Permission removed from user.",
                actor=request.user,
                target_user=user,
                request=request,
                metadata={
                    "permission_id": permission.pk,
                    "permission": permission_label,
                },
            )
        return self.user_permissions(request, user_id=user_id)

    def get_role(self, role_id):
        """Return a role/group by primary key."""
        return get_object_or_404(Group, pk=role_id)

    def get_user(self, user_id):
        """Return a user by primary key."""
        return get_object_or_404(User, pk=user_id)
