"""Permissions for authkit role management APIs."""

from __future__ import annotations

from authkit.api.permissions import AuthKitActionPermission


class IsRoleAdminWithModelPermission(AuthKitActionPermission):
    """Require configured admin access plus the relevant Group permission."""

    permission_map = {
        "list": "auth.view_group",
        "retrieve": "auth.view_group",
        "create": "auth.add_group",
        "update": "auth.change_group",
        "partial_update": "auth.change_group",
        "destroy": "auth.delete_group",
        "assign_users": "auth.change_group",
        "remove_users": "auth.change_group",
        "users": "auth.view_group",
    }
