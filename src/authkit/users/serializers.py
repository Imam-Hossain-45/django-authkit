"""Serializers for authkit user APIs."""

from __future__ import annotations

from django.contrib.auth import password_validation
from django.contrib.auth.models import Group, Permission
from rest_framework import serializers

from authkit.models import User


class CurrentUserSerializer(serializers.ModelSerializer):
    """Serializer for authenticated users managing their own account data."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "is_verified",
            "date_joined",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "is_active",
            "is_staff",
            "is_superuser",
            "is_verified",
            "date_joined",
            "updated_at",
        )


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for staff-managed user records."""

    password = serializers.CharField(
        required=False,
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )
    group_ids = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        source="groups",
        many=True,
        required=False,
        write_only=True,
    )
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        source="user_permissions",
        many=True,
        required=False,
        write_only=True,
    )
    groups = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    user_permissions = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "is_verified",
            "date_joined",
            "updated_at",
            "groups",
            "user_permissions",
            "group_ids",
            "permission_ids",
        )
        read_only_fields = ("id", "date_joined", "updated_at")
        extra_kwargs = {
            "email": {"required": True},
            "is_active": {"required": False},
            "is_staff": {"required": False},
            "is_superuser": {"required": False},
            "is_verified": {"required": False},
        }

    def validate_email(self, value: str) -> str:
        """Normalize and enforce case-insensitive email uniqueness."""
        email = User.objects.normalize_email(value)
        queryset = User.objects.filter(email__iexact=email)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate(self, attrs):
        """Run Django password validators for staff-created passwords."""
        password = attrs.get("password")
        if password:
            candidate = self.instance or User(email=attrs.get("email", ""))
            password_validation.validate_password(password, user=candidate)
        return attrs

    def create(self, validated_data):
        """Create a user through the custom manager and set M2M fields."""
        groups = validated_data.pop("groups", [])
        user_permissions = validated_data.pop("user_permissions", [])
        password = validated_data.pop("password", None)
        user = User.objects.create_user(password=password, **validated_data)
        user.groups.set(groups)
        user.user_permissions.set(user_permissions)
        return user

    def update(self, instance, validated_data):
        """Update user fields, handling password hashing and M2M fields."""
        groups = validated_data.pop("groups", None)
        user_permissions = validated_data.pop("user_permissions", None)
        password = validated_data.pop("password", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password is not None:
            instance.set_password(password)
        instance.save()

        if groups is not None:
            instance.groups.set(groups)
        if user_permissions is not None:
            instance.user_permissions.set(user_permissions)

        return instance
