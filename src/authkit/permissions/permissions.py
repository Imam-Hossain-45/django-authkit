"""Permissions for authkit permission management APIs."""

from __future__ import annotations

from authkit.api.permissions import AuthKitActionPermission


class IsPermissionAdminWithModelPermission(AuthKitActionPermission):
    """Require staff access plus relevant Django model permissions."""

    permission_map = {
        "list": "auth.view_permission",
        "retrieve": "auth.view_permission",
        "role_permissions": "auth.view_group",
        "assign_to_role": "auth.change_group",
        "remove_from_role": "auth.change_group",
        "user_permissions": "authkit.view_user",
        "assign_to_user": "authkit.change_user",
        "remove_from_user": "authkit.change_user",
    }
