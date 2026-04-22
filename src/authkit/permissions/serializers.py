"""Serializers for authkit permission APIs."""

from __future__ import annotations

from django.contrib.auth.models import Group, Permission
from rest_framework import serializers

from authkit.models import User


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for Django Permission records."""

    app_label = serializers.CharField(source="content_type.app_label", read_only=True)
    model = serializers.CharField(source="content_type.model", read_only=True)
    content_type_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Permission
        fields = (
            "id",
            "name",
            "codename",
            "content_type_id",
            "app_label",
            "model",
        )
        read_only_fields = fields


class PermissionAssignmentSerializer(serializers.Serializer):
    """Serializer for assigning or removing permissions."""

    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        many=True,
        allow_empty=False,
    )


class PermissionListSerializer(serializers.Serializer):
    """Serializer for permission list responses."""

    permissions = PermissionSerializer(many=True, read_only=True)


class RolePermissionPathSerializer(serializers.Serializer):
    """Path parameters for role permission operations."""

    role_id = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all())


class UserPermissionPathSerializer(serializers.Serializer):
    """Path parameters for user permission operations."""

    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
