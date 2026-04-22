"""Email helpers for authkit password reset APIs."""

from __future__ import annotations

from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from authkit.conf import authkit_settings
from authkit.email import (
    AuthKitEmailMessage,
    build_action_url,
    render_authkit_email_body,
    send_authkit_email,
)
from authkit.password_reset.tokens import password_reset_token_generator


def build_password_reset_url(uid: str, token: str) -> str:
    """Build an optional frontend reset URL from package settings."""
    return build_action_url(
        str(authkit_settings.PASSWORD_RESET_CONFIRM_URL),
        {"uid": uid, "token": token},
    )


def build_password_reset_message(user, uid: str, token: str) -> str:
    """Build the plain text password reset email body."""
    reset_url = build_password_reset_url(uid, token)
    fallback_body = "\n".join(
        [
            "A password reset was requested for your account.",
            "",
            f"UID: {uid}",
            f"Token: {token}",
            *(["", f"Reset URL: {reset_url}"] if reset_url else []),
            "",
            "If you did not request this, you can ignore this email.",
        ]
    )
    return render_authkit_email_body(
        template_name=str(authkit_settings.PASSWORD_RESET_EMAIL_TEMPLATE),
        context={
            "user": user,
            "uid": uid,
            "token": token,
            "reset_url": reset_url,
        },
        fallback_body=fallback_body,
    )


def build_password_reset_email(user) -> AuthKitEmailMessage:
    """Build a password reset email message for a user."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = password_reset_token_generator.make_token(user)
    return AuthKitEmailMessage(
        subject=str(authkit_settings.PASSWORD_RESET_EMAIL_SUBJECT),
        body=build_password_reset_message(user, uid, token),
        to=(user.email,),
    )


def send_password_reset_email(user) -> int:
    """Send a password reset email for a user."""
    return send_authkit_email(build_password_reset_email(user))
