"""Audit log model for authkit."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Append-only record of important authentication and authorization events."""

    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="authkit_actor_audit_logs",
        verbose_name="actor",
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="authkit_target_audit_logs",
        verbose_name="target user",
    )
    event_type = models.CharField("event type", max_length=100, db_index=True)
    message = models.TextField("message", blank=True)
    metadata = models.JSONField("metadata", default=dict, blank=True)
    ip_address = models.GenericIPAddressField("IP address", blank=True, null=True)
    user_agent = models.TextField("user agent", blank=True)
    created_at = models.DateTimeField("created at", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "audit log"
        verbose_name_plural = "audit logs"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return a readable audit event label."""
        return f"{self.event_type} at {self.created_at:%Y-%m-%d %H:%M:%S}"

    def save(self, *args, **kwargs):
        """Prevent updates to existing audit log rows."""
        if not self._state.adding:
            raise ValueError("Audit logs are append-only and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deleting individual audit log rows."""
        raise ValueError("Audit logs are append-only and cannot be deleted.")
