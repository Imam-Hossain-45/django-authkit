"""Permissions for authkit user management APIs."""

from __future__ import annotations

from authkit.api.permissions import AuthKitActionPermission


class IsUserAdminWithModelPermission(AuthKitActionPermission):
    """Require configured admin access plus the relevant user model permission."""

    permission_map = {
        "list": "authkit.view_user",
        "retrieve": "authkit.view_user",
        "create": "authkit.add_user",
        "update": "authkit.change_user",
        "partial_update": "authkit.change_user",
        "activate": "authkit.change_user",
        "deactivate": "authkit.change_user",
    }
