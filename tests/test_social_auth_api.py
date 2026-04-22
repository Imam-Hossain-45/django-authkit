"""Tests for authkit social authentication APIs."""

from __future__ import annotations

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from authkit.models import SocialAccount
from authkit.social_auth.exceptions import InvalidSocialTokenError
from authkit.social_auth.providers.base import SocialIdentity
from authkit.social_auth.providers.registry import get_provider

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client() -> APIClient:
    """Return a DRF API client."""
    return APIClient()


@pytest.fixture(autouse=True)
def google_provider(monkeypatch):
    """Patch Google token verification to avoid external network calls."""
    provider = get_provider("google")
    assert provider is not None

    def verify_token(token: str) -> SocialIdentity:
        if token == "invalid":
            raise InvalidSocialTokenError("Invalid Google ID token.")
        return SocialIdentity(
            provider="google",
            provider_user_id=f"google-{token}",
            email=f"{token}@example.com",
            email_verified=True,
            first_name="Google",
            last_name="User",
            raw={"sub": f"google-{token}", "email": f"{token}@example.com"},
        )

    monkeypatch.setattr(provider, "verify_token", verify_token)
    return provider


def test_provider_list(api_client: APIClient):
    response = api_client.get(reverse("authkit-api:social_auth:provider-list"))

    assert response.status_code == 200
    assert response.data[0]["provider"] == "google"


def test_provider_detail(api_client: APIClient):
    response = api_client.get(
        reverse(
            "authkit-api:social_auth:provider-detail",
            kwargs={"provider": "google"},
        )
    )

    assert response.status_code == 200
    assert response.data["provider"] == "google"


def test_provider_detail_unknown(api_client: APIClient):
    response = api_client.get(
        reverse(
            "authkit-api:social_auth:provider-detail",
            kwargs={"provider": "unknown"},
        )
    )

    assert response.status_code == 404


def test_google_social_signup_creates_user_and_social_account(api_client: APIClient):
    response = api_client.post(
        reverse(
            "authkit-api:social_auth:token-exchange",
            kwargs={"provider": "google"},
        ),
        {"id_token": "new"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["user"]["email"] == "new@example.com"
    assert uuid.UUID(response.data["user"]["id"])
    assert response.data["tokens"]["access"]
    assert response.data["tokens"]["refresh"]
    assert response.data["social_account"]["created_user"] is True
    user = get_user_model().objects.get(email="new@example.com")
    assert user.has_usable_password() is False
    assert user.is_verified is True
    social_account = SocialAccount.objects.get(user=user, provider="google")
    assert isinstance(social_account.id, uuid.UUID)


def test_google_social_login_existing_social_account(api_client: APIClient):
    user = get_user_model().objects.create_user(
        email="existing@example.com",
        password=None,
        is_verified=True,
    )
    SocialAccount.objects.create(
        provider="google",
        provider_user_id="google-existing",
        user=user,
        email="existing@example.com",
    )

    response = api_client.post(
        reverse(
            "authkit-api:social_auth:token-exchange",
            kwargs={"provider": "google"},
        ),
        {"id_token": "existing"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["user"]["email"] == "existing@example.com"
    assert response.data["social_account"]["created_user"] is False
    assert response.data["social_account"]["linked_account"] is False


def test_google_social_login_links_existing_email(api_client: APIClient):
    user = get_user_model().objects.create_user(
        email="linked@example.com",
        password="password",
        is_verified=False,
    )

    response = api_client.post(
        reverse(
            "authkit-api:social_auth:token-exchange",
            kwargs={"provider": "google"},
        ),
        {"id_token": "linked"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["social_account"]["linked_account"] is True
    user.refresh_from_db()
    assert user.is_verified is True
    assert SocialAccount.objects.filter(user=user, provider="google").exists()


@override_settings(AUTHKIT={"SOCIAL_AUTH_ALLOW_ACCOUNT_LINKING": False})
def test_google_social_login_can_disable_existing_email_linking(api_client: APIClient):
    get_user_model().objects.create_user(
        email="linked@example.com",
        password="password",
    )

    response = api_client.post(
        reverse(
            "authkit-api:social_auth:token-exchange",
            kwargs={"provider": "google"},
        ),
        {"id_token": "linked"},
        format="json",
    )

    assert response.status_code == 400
    assert not SocialAccount.objects.filter(provider="google").exists()


@override_settings(AUTHKIT={"SOCIAL_AUTH_ALLOW_SIGNUP": False})
def test_google_social_login_can_disable_signup(api_client: APIClient):
    response = api_client.post(
        reverse(
            "authkit-api:social_auth:token-exchange",
            kwargs={"provider": "google"},
        ),
        {"id_token": "new"},
        format="json",
    )

    assert response.status_code == 400


def test_google_social_login_rejects_invalid_token(api_client: APIClient):
    response = api_client.post(
        reverse(
            "authkit-api:social_auth:token-exchange",
            kwargs={"provider": "google"},
        ),
        {"id_token": "invalid"},
        format="json",
    )

    assert response.status_code == 400


def test_google_social_login_unknown_provider(api_client: APIClient):
    response = api_client.post(
        reverse(
            "authkit-api:social_auth:token-exchange",
            kwargs={"provider": "unknown"},
        ),
        {"id_token": "new"},
        format="json",
    )

    assert response.status_code == 400
