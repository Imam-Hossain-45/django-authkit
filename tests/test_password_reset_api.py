"""Tests for authkit password reset APIs."""

from __future__ import annotations

import re

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

from authkit.password_reset.tokens import password_reset_token_generator

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client() -> APIClient:
    """Return a DRF API client."""
    return APIClient()


@pytest.fixture
def user():
    """Return an active user."""
    return get_user_model().objects.create_user(
        email="user@example.com",
        password="current-password",
        is_verified=True,
    )


def extract_reset_credentials(body: str) -> tuple[str, str]:
    """Extract uid and token from the plain text reset email body."""
    uid = re.search(r"UID: (?P<uid>.+)", body)
    token = re.search(r"Token: (?P<token>.+)", body)
    assert uid is not None
    assert token is not None
    return uid.group("uid").strip(), token.group("token").strip()


def test_password_reset_request_sends_email(api_client: APIClient, user):
    response = api_client.post(
        reverse("authkit-api:password_reset:request"),
        {"email": "user@example.com"},
        format="json",
    )

    assert response.status_code == 202
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["user@example.com"]
    assert "UID:" in mail.outbox[0].body
    assert "Token:" in mail.outbox[0].body


def test_password_reset_request_does_not_leak_unknown_email(api_client: APIClient):
    response = api_client.post(
        reverse("authkit-api:password_reset:request"),
        {"email": "missing@example.com"},
        format="json",
    )

    assert response.status_code == 202
    assert len(mail.outbox) == 0


def test_password_reset_request_ignores_inactive_users(
    api_client: APIClient,
    user,
):
    user.is_active = False
    user.save(update_fields=["is_active"])

    response = api_client.post(
        reverse("authkit-api:password_reset:request"),
        {"email": "user@example.com"},
        format="json",
    )

    assert response.status_code == 202
    assert len(mail.outbox) == 0


def test_password_reset_confirm_changes_password(api_client: APIClient, user):
    api_client.post(
        reverse("authkit-api:password_reset:request"),
        {"email": "user@example.com"},
        format="json",
    )
    uid, token = extract_reset_credentials(mail.outbox[0].body)

    response = api_client.post(
        reverse("authkit-api:password_reset:confirm"),
        {
            "uid": uid,
            "token": token,
            "new_password": "new-secure-password",
        },
        format="json",
    )

    assert response.status_code == 204
    user.refresh_from_db()
    assert user.check_password("new-secure-password")


def test_password_reset_confirm_rejects_invalid_token(api_client: APIClient, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    response = api_client.post(
        reverse("authkit-api:password_reset:confirm"),
        {
            "uid": uid,
            "token": "invalid-token",
            "new_password": "new-secure-password",
        },
        format="json",
    )

    assert response.status_code == 400
    user.refresh_from_db()
    assert user.check_password("current-password")


@override_settings(AUTHKIT={"PASSWORD_RESET_TIMEOUT": 0})
def test_password_reset_confirm_respects_authkit_timeout(
    api_client: APIClient,
    user,
):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = password_reset_token_generator.make_token(user)

    response = api_client.post(
        reverse("authkit-api:password_reset:confirm"),
        {
            "uid": uid,
            "token": token,
            "new_password": "new-secure-password",
        },
        format="json",
    )

    assert response.status_code == 400


@override_settings(
    AUTHKIT={
        "PASSWORD_RESET_CONFIRM_URL": "https://example.com/reset-password",
    }
)
def test_password_reset_email_can_include_frontend_url(
    api_client: APIClient,
    user,
):
    response = api_client.post(
        reverse("authkit-api:password_reset:request"),
        {"email": "user@example.com"},
        format="json",
    )

    assert response.status_code == 202
    assert "https://example.com/reset-password?uid=" in mail.outbox[0].body


@override_settings(
    AUTHKIT={
        "PASSWORD_RESET_EMAIL_TEMPLATE": "authkit/password_reset_email.txt",
    },
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "APP_DIRS": False,
            "OPTIONS": {
                "loaders": [
                    (
                        "django.template.loaders.locmem.Loader",
                        {
                            "authkit/password_reset_email.txt": (
                                "Reset for {{ user.email }} with "
                                "{{ uid }} and {{ token }}"
                            ),
                        },
                    ),
                ],
            },
        },
    ],
)
def test_password_reset_email_can_use_custom_template(
    api_client: APIClient,
    user,
):
    response = api_client.post(
        reverse("authkit-api:password_reset:request"),
        {"email": "user@example.com"},
        format="json",
    )

    assert response.status_code == 202
    assert mail.outbox[0].body.startswith("Reset for user@example.com with ")
