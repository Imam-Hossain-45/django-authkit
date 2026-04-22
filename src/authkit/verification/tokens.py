"""Email verification token utilities for django-authkit."""

from __future__ import annotations

from django.core import signing

from authkit.conf import authkit_settings

EMAIL_VERIFICATION_SALT = "authkit.email_verification"


def make_email_verification_token(user) -> str:
    """Create a signed email verification token for a user."""
    return signing.dumps(
        {
            "user_id": str(user.pk),
            "email": user.email,
            "password": user.password,
        },
        salt=EMAIL_VERIFICATION_SALT,
    )


def load_email_verification_token(token: str) -> dict[str, object]:
    """Load a signed email verification token using authkit timeout settings."""
    return signing.loads(
        token,
        salt=EMAIL_VERIFICATION_SALT,
        max_age=int(authkit_settings.EMAIL_VERIFICATION_TIMEOUT),
    )
