"""Serializers for authkit audit log APIs."""

from __future__ import annotations

from rest_framework import serializers

from authkit.audit_log.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for audit log records."""

    actor_email = serializers.EmailField(source="actor.email", read_only=True)
    target_user_email = serializers.EmailField(
        source="target_user.email",
        read_only=True,
    )

    class Meta:
        model = AuditLog
        fields = (
            "id",
            "actor",
            "actor_email",
            "target_user",
            "target_user_email",
            "event_type",
            "message",
            "metadata",
            "ip_address",
            "user_agent",
            "created_at",
        )
        read_only_fields = fields
