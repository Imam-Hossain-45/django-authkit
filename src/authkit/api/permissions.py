"""Reusable DRF permission policies for authkit APIs."""

from __future__ import annotations

from collections.abc import Iterable

from rest_framework.permissions import AllowAny, BasePermission

from authkit.conf import authkit_settings


class AuthKitPublicEndpoint(AllowAny):
    """Explicit marker for endpoints intentionally open to anonymous clients."""


class AuthKitAuthenticated(BasePermission):
    """Require a logged-in Django user."""

    def has_permission(self, request, view) -> bool:
        """Return whether the request has an authenticated user."""
        user = request.user
        return bool(user and user.is_authenticated)


class AuthKitVerifiedIfRequired(AuthKitAuthenticated):
    """Require verification only when AUTHKIT requires verified API users."""

    def has_permission(self, request, view) -> bool:
        """Return whether the user is authenticated and verified if configured."""
        if not super().has_permission(request, view):
            return False
        if not authkit_settings.REQUIRE_VERIFIED_LOGIN:
            return True
        return bool(getattr(request.user, "is_verified", False))


class AuthKitSuperuserOnly(AuthKitAuthenticated):
    """Require a Django superuser."""

    def has_permission(self, request, view) -> bool:
        """Return whether the authenticated user is a superuser."""
        return super().has_permission(request, view) and bool(request.user.is_superuser)


class AuthKitAdminManager(AuthKitAuthenticated):
    """Require administrative API access according to authkit settings."""

    def has_permission(self, request, view) -> bool:
        """Return whether the authenticated user can access admin APIs."""
        if not super().has_permission(request, view):
            return False
        return self.user_matches_admin_policy(request.user)

    def user_matches_admin_policy(self, user) -> bool:
        """Return whether the given user satisfies the configured admin policy."""
        if authkit_settings.ADMIN_API_REQUIRE_SUPERUSER and not bool(
            getattr(user, "is_superuser", False)
        ):
            return False
        if authkit_settings.ADMIN_API_REQUIRE_STAFF and not bool(
            getattr(user, "is_staff", False)
        ):
            return False
        return True


class AuthKitActionPermission(AuthKitAdminManager):
    """Require configured admin access plus Django permissions by view action."""

    default_permission: str | Iterable[str] | None = None
    permission_map: dict[str, str | Iterable[str]] = {}

    def has_permission(self, request, view) -> bool:
        """Return whether the user has every permission required by the action."""
        if not super().has_permission(request, view):
            return False

        required_permissions = self.get_required_permissions(view)
        if required_permissions is None:
            return False
        if not required_permissions:
            return True

        return request.user.has_perms(required_permissions)

    def get_required_permissions(self, view) -> list[str] | None:
        """Return Django permissions required for the current view action."""
        action = getattr(view, "action", "")
        permissions = self.permission_map.get(action, self.default_permission)
        if permissions is None:
            return None
        if isinstance(permissions, str):
            return [permissions]
        return list(permissions)


class AuthKitSelfOrAdmin(AuthKitAuthenticated):
    """Allow users to access themselves, or admins with the configured permission."""

    admin_permission: str = "authkit.view_user"

    def has_object_permission(self, request, view, obj) -> bool:
        """Return whether the object is the current user or admin-accessible."""
        if not self.has_permission(request, view):
            return False
        if obj == request.user or getattr(obj, "pk", None) == request.user.pk:
            return True
        admin_policy = AuthKitAdminManager()
        return bool(
            admin_policy.user_matches_admin_policy(request.user)
            and request.user.has_perm(self.admin_permission)
        )
