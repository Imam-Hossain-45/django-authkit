"""Runtime settings for django-authkit."""

from __future__ import annotations

from typing import Any

from django.conf import settings

DEFAULTS: dict[str, Any] = {
    "API_PREFIX": "authkit/",
    "OPENAPI_TITLE": "django-authkit API",
    "OPENAPI_DESCRIPTION": "Reusable authentication API layer for Django projects.",
    "OPENAPI_VERSION": "0.1.0",
    "ADMIN_API_REQUIRE_STAFF": True,
    "ADMIN_API_REQUIRE_SUPERUSER": False,
    "REQUIRE_VERIFIED_LOGIN": False,
    "PASSWORD_RESET_TIMEOUT": 60 * 60 * 24,
    "PASSWORD_RESET_CONFIRM_URL": "",
    "PASSWORD_RESET_EMAIL_SUBJECT": "Reset your password",
    "PASSWORD_RESET_EMAIL_TEMPLATE": "",
    "EMAIL_VERIFICATION_TIMEOUT": 60 * 60 * 24,
    "EMAIL_VERIFICATION_CONFIRM_URL": "",
    "EMAIL_VERIFICATION_EMAIL_SUBJECT": "Verify your email address",
    "EMAIL_VERIFICATION_EMAIL_TEMPLATE": "",
    "SEND_VERIFICATION_EMAIL_ON_REGISTER": False,
    "SOCIAL_AUTH_ALLOW_SIGNUP": True,
    "SOCIAL_AUTH_ALLOW_ACCOUNT_LINKING": True,
    "SOCIAL_AUTH_MARK_VERIFIED_EMAIL": True,
    "SOCIAL_AUTH_GOOGLE_CLIENT_ID": "",
    "SOCIAL_AUTH_GOOGLE_ALLOWED_DOMAINS": [],
}


class AuthKitSettings:
    """Small settings wrapper for package-level configuration."""

    setting_name = "AUTHKIT"

    def __getattr__(self, name: str) -> Any:
        if name not in DEFAULTS:
            raise AttributeError(f"Invalid authkit setting: {name}")
        return self.user_settings.get(name, DEFAULTS[name])

    @property
    def user_settings(self) -> dict[str, Any]:
        configured = getattr(settings, self.setting_name, {})
        if configured is None:
            return {}
        if not isinstance(configured, dict):
            raise TypeError("AUTHKIT settings must be a dictionary.")
        return configured

    @property
    def api_prefix(self) -> str:
        """Return the normalized package URL prefix."""
        prefix = str(self.API_PREFIX).strip("/")
        return f"{prefix}/" if prefix else ""


authkit_settings = AuthKitSettings()
