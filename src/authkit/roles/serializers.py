"""Serializers for authkit role APIs backed by Django Group."""

from __future__ import annotations

from django.contrib.auth.models import Group, Permission
from rest_framework import serializers

from authkit.models import User
from authkit.users.serializers import AdminUserSerializer


class RoleSerializer(serializers.ModelSerializer):
    """Serializer that presents Django Group records as roles."""

    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        source="permissions",
        many=True,
        required=False,
        write_only=True,
    )
    permissions = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = (
            "id",
            "name",
            "permissions",
            "permission_ids",
            "user_count",
        )
        read_only_fields = ("id", "permissions", "user_count")

    def get_user_count(self, obj: Group) -> int:
        """Return the number of users assigned to the role."""
        return obj.user_set.count()


class RoleUserAssignmentSerializer(serializers.Serializer):
    """Serializer for assigning or removing users from a role."""

    user_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        allow_empty=False,
    )


class RoleUsersSerializer(serializers.Serializer):
    """Serializer for users assigned to a role."""

    users = AdminUserSerializer(many=True, read_only=True)
