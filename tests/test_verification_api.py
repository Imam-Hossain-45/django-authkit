"""Tests for authkit email verification APIs."""

from __future__ import annotations

import re

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from authkit.verification.tokens import make_email_verification_token

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client() -> APIClient:
    """Return a DRF API client."""
    return APIClient()


@pytest.fixture
def user():
    """Return an active unverified user."""
    return get_user_model().objects.create_user(
        email="user@example.com",
        password="current-password",
        is_verified=False,
    )


def extract_verification_token(body: str) -> str:
    """Extract verification token from the plain text email body."""
    token = re.search(r"Token: (?P<token>.+)", body)
    assert token is not None
    return token.group("token").strip()


def test_verification_request_sends_email(api_client: APIClient, user):
    response = api_client.post(
        reverse("authkit-api:verification:request"),
        {"email": "user@example.com"},
        format="json",
    )

    assert response.status_code == 202
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["user@example.com"]
    assert "Token:" in mail.outbox[0].body


def test_verification_request_does_not_leak_unknown_email(api_client: APIClient):
    response = api_client.post(
        reverse("authkit-api:verification:request"),
        {"email": "missing@example.com"},
        format="json",
    )

    assert response.status_code == 202
    assert len(mail.outbox) == 0


def test_verification_request_ignores_verified_users(
    api_client: APIClient,
    user,
):
    user.is_verified = True
    user.save(update_fields=["is_verified"])

    response = api_client.post(
        reverse("authkit-api:verification:request"),
        {"email": "user@example.com"},
        format="json",
    )

    assert response.status_code == 202
    assert len(mail.outbox) == 0


def test_verification_confirm_marks_user_verified(api_client: APIClient, user):
    api_client.post(
        reverse("authkit-api:verification:request"),
        {"email": "user@example.com"},
        format="json",
    )
    token = extract_verification_token(mail.outbox[0].body)

    response = api_client.post(
        reverse("authkit-api:verification:confirm"),
        {"token": token},
        format="json",
    )

    assert response.status_code == 204
    user.refresh_from_db()
    assert user.is_verified is True


def test_verification_confirm_rejects_invalid_token(api_client: APIClient, user):
    response = api_client.post(
        reverse("authkit-api:verification:confirm"),
        {"token": "invalid-token"},
        format="json",
    )

    assert response.status_code == 400
    user.refresh_from_db()
    assert user.is_verified is False


@override_settings(AUTHKIT={"EMAIL_VERIFICATION_TIMEOUT": 0})
def test_verification_confirm_respects_timeout(api_client: APIClient, user):
    token = make_email_verification_token(user)

    response = api_client.post(
        reverse("authkit-api:verification:confirm"),
        {"token": token},
        format="json",
    )

    assert response.status_code == 400
    user.refresh_from_db()
    assert user.is_verified is False


@override_settings(
    AUTHKIT={
        "EMAIL_VERIFICATION_CONFIRM_URL": "https://example.com/verify-email",
    }
)
def test_verification_email_can_include_frontend_url(
    api_client: APIClient,
    user,
):
    response = api_client.post(
        reverse("authkit-api:verification:request"),
        {"email": "user@example.com"},
        format="json",
    )

    assert response.status_code == 202
    assert "https://example.com/verify-email?token=" in mail.outbox[0].body


@override_settings(
    AUTHKIT={
        "EMAIL_VERIFICATION_EMAIL_TEMPLATE": "authkit/verification_email.txt",
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
                            "authkit/verification_email.txt": (
                                "Verify {{ user.email }} with {{ token }}"
                            ),
                        },
                    ),
                ],
            },
        },
    ],
)
def test_verification_email_can_use_custom_template(
    api_client: APIClient,
    user,
):
    response = api_client.post(
        reverse("authkit-api:verification:request"),
        {"email": "user@example.com"},
        format="json",
    )

    assert response.status_code == 202
    assert mail.outbox[0].body.startswith("Verify user@example.com with ")


@override_settings(AUTHKIT={"SEND_VERIFICATION_EMAIL_ON_REGISTER": True})
def test_registration_can_trigger_verification_email(api_client: APIClient):
    response = api_client.post(
        reverse("authkit-api:authentication:register"),
        {
            "email": "new@example.com",
            "password": "strong-register-password",
        },
        format="json",
    )

    assert response.status_code == 201
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["new@example.com"]
