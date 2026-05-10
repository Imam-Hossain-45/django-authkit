"""Permissions for authkit audit log APIs."""

from __future__ import annotations

from authkit.api.permissions import AuthKitActionPermission


class CanViewAuditLogs(AuthKitActionPermission):
    """Require configured admin access with audit log view permission."""

    default_permission = "authkit.view_auditlog"
    permission_map = {
        "list": "authkit.view_auditlog",
        "retrieve": "authkit.view_auditlog",
    }
