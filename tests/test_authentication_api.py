"""Tests for authkit authentication APIs."""

from __future__ import annotations

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client() -> APIClient:
    """Return a DRF API client."""
    return APIClient()


@pytest.fixture
def user():
    """Return an active verified user."""
    return get_user_model().objects.create_user(
        email="user@example.com",
        password="current-password",
        first_name="Regular",
        is_verified=True,
    )


def test_register_creates_user_and_returns_tokens(api_client: APIClient):
    response = api_client.post(
        reverse("authkit-api:authentication:register"),
        {
            "email": "new@example.com",
            "password": "strong-register-password",
            "first_name": "New",
            "last_name": "User",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["user"]["email"] == "new@example.com"
    assert uuid.UUID(response.data["user"]["id"])
    assert response.data["tokens"]["access"]
    assert response.data["tokens"]["refresh"]
    created = get_user_model().objects.get(email="new@example.com")
    assert created.check_password("strong-register-password")


def test_login_returns_tokens(api_client: APIClient, user):
    response = api_client.post(
        reverse("authkit-api:authentication:login"),
        {"email": "user@example.com", "password": "current-password"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["user"]["email"] == "user@example.com"
    assert response.data["tokens"]["access"]
    assert response.data["tokens"]["refresh"]


def test_login_rejects_inactive_user(api_client: APIClient, user):
    user.is_active = False
    user.save(update_fields=["is_active"])

    response = api_client.post(
        reverse("authkit-api:authentication:login"),
        {"email": "user@example.com", "password": "current-password"},
        format="json",
    )

    assert response.status_code == 400


@override_settings(AUTHKIT={"REQUIRE_VERIFIED_LOGIN": True})
def test_login_can_require_verified_user(api_client: APIClient):
    get_user_model().objects.create_user(
        email="unverified@example.com",
        password="current-password",
        is_verified=False,
    )

    response = api_client.post(
        reverse("authkit-api:authentication:login"),
        {"email": "unverified@example.com", "password": "current-password"},
        format="json",
    )

    assert response.status_code == 400
    assert "not verified" in str(response.data).lower()


def test_refresh_returns_new_access_token(api_client: APIClient, user):
    login_response = api_client.post(
        reverse("authkit-api:authentication:login"),
        {"email": "user@example.com", "password": "current-password"},
        format="json",
    )

    response = api_client.post(
        reverse("authkit-api:authentication:refresh"),
        {"refresh": login_response.data["tokens"]["refresh"]},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["access"]


def test_logout_requires_authentication(api_client: APIClient):
    response = api_client.post(
        reverse("authkit-api:authentication:logout"),
        {"refresh": "not-a-token"},
        format="json",
    )

    assert response.status_code == 401


def test_logout_blacklists_refresh_token(api_client: APIClient, user):
    login_response = api_client.post(
        reverse("authkit-api:authentication:login"),
        {"email": "user@example.com", "password": "current-password"},
        format="json",
    )
    access = login_response.data["tokens"]["access"]
    refresh = login_response.data["tokens"]["refresh"]

    response = api_client.post(
        reverse("authkit-api:authentication:logout"),
        {"refresh": refresh},
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {access}",
    )

    assert response.status_code == 204

    refresh_response = api_client.post(
        reverse("authkit-api:authentication:refresh"),
        {"refresh": refresh},
        format="json",
    )
    assert refresh_response.status_code == 401


def test_change_password(api_client: APIClient, user):
    login_response = api_client.post(
        reverse("authkit-api:authentication:login"),
        {"email": "user@example.com", "password": "current-password"},
        format="json",
    )

    response = api_client.post(
        reverse("authkit-api:authentication:change-password"),
        {
            "current_password": "current-password",
            "new_password": "new-secure-password",
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {login_response.data['tokens']['access']}",
    )

    assert response.status_code == 204
    user.refresh_from_db()
    assert user.check_password("new-secure-password")


def test_change_password_rejects_wrong_current_password(
    api_client: APIClient,
    user,
):
    login_response = api_client.post(
        reverse("authkit-api:authentication:login"),
        {"email": "user@example.com", "password": "current-password"},
        format="json",
    )

    response = api_client.post(
        reverse("authkit-api:authentication:change-password"),
        {
            "current_password": "wrong-password",
            "new_password": "new-secure-password",
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {login_response.data['tokens']['access']}",
    )

    assert response.status_code == 400
