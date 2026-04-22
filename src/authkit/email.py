"""Reusable email delivery primitives for authkit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


@dataclass(frozen=True)
class AuthKitEmailMessage:
    """Plain authkit email payload sent through Django's email backend."""

    subject: str
    body: str
    to: tuple[str, ...]
    from_email: str | None = None
    html_body: str | None = None


class AuthKitEmailService:
    """Small delivery service backed by Django's configured email backend."""

    def send(self, message: AuthKitEmailMessage) -> int:
        """Send an authkit email message."""
        return send_mail(
            subject=message.subject,
            message=message.body,
            from_email=message.from_email
            or getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=list(message.to),
            fail_silently=False,
            html_message=message.html_body,
        )


def get_email_service() -> AuthKitEmailService:
    """Return the email service used by authkit modules."""
    return AuthKitEmailService()


def send_authkit_email(message: AuthKitEmailMessage) -> int:
    """Send an authkit email through the configured service."""
    return get_email_service().send(message)


def build_action_url(base_url: str, params: dict[str, Any]) -> str:
    """Build a URL with query parameters, preserving existing query strings."""
    normalized_base_url = str(base_url).strip()
    if not normalized_base_url:
        return ""
    separator = "&" if "?" in normalized_base_url else "?"
    return f"{normalized_base_url}{separator}{urlencode(params)}"


def render_authkit_email_body(
    *,
    template_name: str,
    context: dict[str, Any],
    fallback_body: str,
) -> str:
    """Render a configured text template or return the fallback body."""
    if not template_name:
        return fallback_body
    return render_to_string(template_name, context).strip()
