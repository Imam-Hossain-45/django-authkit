"""Password reset token utilities for django-authkit."""

from __future__ import annotations

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import base36_to_int

from authkit.conf import authkit_settings


class AuthKitPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    """Password reset token generator with authkit-configurable expiry."""

    def check_token(self, user, token: str | None) -> bool:
        """Validate token integrity and package-level timeout."""
        if not user or not token:
            return False

        try:
            timestamp_b36, _ = token.split("-")
            timestamp = base36_to_int(timestamp_b36)
        except ValueError:
            return False

        if not super().check_token(user, token):
            return False

        elapsed = self._num_seconds(self._now()) - timestamp
        return elapsed < int(authkit_settings.PASSWORD_RESET_TIMEOUT)


password_reset_token_generator = AuthKitPasswordResetTokenGenerator()
