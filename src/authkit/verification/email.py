"""Email helpers for authkit email verification APIs."""

from __future__ import annotations

from authkit.conf import authkit_settings
from authkit.email import (
    AuthKitEmailMessage,
    build_action_url,
    render_authkit_email_body,
    send_authkit_email,
)
from authkit.verification.tokens import make_email_verification_token


def build_email_verification_url(token: str) -> str:
    """Build an optional frontend verification URL from package settings."""
    return build_action_url(
        str(authkit_settings.EMAIL_VERIFICATION_CONFIRM_URL),
        {"token": token},
    )


def build_email_verification_message(user, token: str) -> str:
    """Build the plain text email verification body."""
    verification_url = build_email_verification_url(token)
    fallback_body = "\n".join(
        [
            "Please verify your email address.",
            "",
            f"Token: {token}",
            *(
                ["", f"Verification URL: {verification_url}"]
                if verification_url
                else []
            ),
            "",
            "If you did not request this, you can ignore this email.",
        ]
    )
    return render_authkit_email_body(
        template_name=str(authkit_settings.EMAIL_VERIFICATION_EMAIL_TEMPLATE),
        context={
            "user": user,
            "token": token,
            "verification_url": verification_url,
        },
        fallback_body=fallback_body,
    )


def build_email_verification_email(user) -> AuthKitEmailMessage:
    """Build an email verification message for a user."""
    token = make_email_verification_token(user)
    return AuthKitEmailMessage(
        subject=str(authkit_settings.EMAIL_VERIFICATION_EMAIL_SUBJECT),
        body=build_email_verification_message(user, token),
        to=(user.email,),
    )


def send_email_verification_email(user) -> int:
    """Send an email verification message for a user."""
    return send_authkit_email(build_email_verification_email(user))
