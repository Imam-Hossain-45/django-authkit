"""Tests for authkit user management APIs."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
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
    """Return a regular active user."""
    return get_user_model().objects.create_user(
        email="user@example.com",
        password="password",
        first_name="Regular",
        last_name="User",
    )


@pytest.fixture
def staff_user():
    """Return a staff user with user management permissions."""
    staff = get_user_model().objects.create_user(
        email="staff@example.com",
        password="password",
        is_staff=True,
    )
    permissions = Permission.objects.filter(
        content_type__app_label="authkit",
        codename__in=("view_user", "add_user", "change_user"),
    )
    staff.user_permissions.set(permissions)
    return staff


def test_current_user_detail_requires_authentication(api_client: APIClient):
    response = api_client.get(reverse("authkit-api:users:me"))

    assert response.status_code == 401


def test_current_user_detail(api_client: APIClient, user):
    api_client.force_authenticate(user=user)

    response = api_client.get(reverse("authkit-api:users:me"))

    assert response.status_code == 200
    assert response.data["email"] == "user@example.com"
    assert response.data["first_name"] == "Regular"


def test_current_user_update_only_self_service_fields(api_client: APIClient, user):
    api_client.force_authenticate(user=user)

    response = api_client.patch(
        reverse("authkit-api:users:me"),
        {
            "first_name": "Updated",
            "is_staff": True,
            "is_superuser": True,
        },
        format="json",
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.first_name == "Updated"
    assert user.is_staff is False
    assert user.is_superuser is False


@override_settings(AUTHKIT={"REQUIRE_VERIFIED_LOGIN": True})
def test_current_user_detail_can_require_verified_user(api_client: APIClient):
    user = get_user_model().objects.create_user(
        email="unverified@example.com",
        password="password",
        is_verified=False,
    )
    api_client.force_authenticate(user=user)

    response = api_client.get(reverse("authkit-api:users:me"))

    assert response.status_code == 403


def test_admin_user_list_requires_staff_permission(api_client: APIClient, user):
    api_client.force_authenticate(user=user)

    response = api_client.get(reverse("authkit-api:users:user-list"))

    assert response.status_code == 403


def test_admin_user_list(api_client: APIClient, user, staff_user):
    api_client.force_authenticate(user=staff_user)

    response = api_client.get(reverse("authkit-api:users:user-list"))

    assert response.status_code == 200
    emails = {item["email"] for item in response.data}
    assert {"staff@example.com", "user@example.com"} <= emails


@override_settings(AUTHKIT={"ADMIN_API_REQUIRE_STAFF": False})
def test_admin_user_list_can_allow_permission_only_access(
    api_client: APIClient,
    user,
):
    manager = get_user_model().objects.create_user(
        email="manager@example.com",
        password="password",
        is_staff=False,
    )
    manager.user_permissions.add(Permission.objects.get(codename="view_user"))
    api_client.force_authenticate(user=manager)

    response = api_client.get(reverse("authkit-api:users:user-list"))

    assert response.status_code == 200
    emails = {item["email"] for item in response.data}
    assert {"manager@example.com", "user@example.com"} <= emails


@override_settings(
    AUTHKIT={
        "ADMIN_API_REQUIRE_STAFF": False,
        "ADMIN_API_REQUIRE_SUPERUSER": True,
    }
)
def test_admin_user_list_can_require_superuser_even_with_permissions(
    api_client: APIClient,
    user,
):
    manager = get_user_model().objects.create_user(
        email="manager@example.com",
        password="password",
        is_staff=False,
    )
    manager.user_permissions.add(Permission.objects.get(codename="view_user"))
    api_client.force_authenticate(user=manager)

    response = api_client.get(reverse("authkit-api:users:user-list"))

    assert response.status_code == 403


def test_admin_create_user(api_client: APIClient, staff_user):
    api_client.force_authenticate(user=staff_user)

    response = api_client.post(
        reverse("authkit-api:users:user-list"),
        {
            "email": "created@example.com",
            "password": "secure-password",
            "first_name": "Created",
            "is_active": True,
        },
        format="json",
    )

    assert response.status_code == 201
    created = get_user_model().objects.get(email="created@example.com")
    assert created.first_name == "Created"
    assert created.check_password("secure-password")


def test_admin_update_user(api_client: APIClient, staff_user, user):
    api_client.force_authenticate(user=staff_user)

    response = api_client.patch(
        reverse("authkit-api:users:user-detail", kwargs={"pk": user.pk}),
        {"last_name": "Changed", "is_verified": True},
        format="json",
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.last_name == "Changed"
    assert user.is_verified is True


def test_admin_activate_and_deactivate_user(api_client: APIClient, staff_user, user):
    api_client.force_authenticate(user=staff_user)

    deactivate_response = api_client.post(
        reverse("authkit-api:users:user-deactivate", kwargs={"pk": user.pk})
    )
    user.refresh_from_db()

    assert deactivate_response.status_code == 200
    assert user.is_active is False

    activate_response = api_client.post(
        reverse("authkit-api:users:user-activate", kwargs={"pk": user.pk})
    )
    user.refresh_from_db()

    assert activate_response.status_code == 200
    assert user.is_active is True
