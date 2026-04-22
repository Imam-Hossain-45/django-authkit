"""Helpers for writing authkit audit log events."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from django.contrib.auth.models import AnonymousUser
from django.db import models

from authkit.audit_log.models import AuditLog


def create_audit_log(
    *,
    event_type: str,
    message: str = "",
    actor=None,
    target_user=None,
    request=None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Create an append-only audit log entry."""
    return AuditLog.objects.create(
        actor=normalize_user(actor),
        target_user=normalize_user(target_user),
        event_type=event_type,
        message=message,
        metadata=make_json_safe(metadata or {}),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )


def normalize_user(user):
    """Return a persisted authenticated user or None."""
    if user is None or isinstance(user, AnonymousUser):
        return None
    if not getattr(user, "is_authenticated", False):
        return None
    return user


def get_client_ip(request) -> str | None:
    """Extract a client IP address from a request."""
    if request is None:
        return None
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip() or None
    return request.META.get("REMOTE_ADDR")


def get_user_agent(request) -> str:
    """Extract a user agent from a request."""
    if request is None:
        return ""
    return request.META.get("HTTP_USER_AGENT", "")


def make_json_safe(value):
    """Convert common Django/Python objects to JSON-safe metadata values."""
    if isinstance(value, dict):
        return {str(key): make_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [make_json_safe(item) for item in value]
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, models.Model):
        return str(value.pk)
    return value
