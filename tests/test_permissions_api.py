"""Tests for authkit permission management APIs."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
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
    """Return a regular user."""
    return get_user_model().objects.create_user(
        email="user@example.com",
        password="password",
    )


@pytest.fixture
def staff_user():
    """Return a staff user with permission management permissions."""
    staff = get_user_model().objects.create_user(
        email="staff@example.com",
        password="password",
        is_staff=True,
    )
    permissions = Permission.objects.filter(
        codename__in=(
            "view_permission",
            "view_group",
            "change_group",
            "view_user",
            "change_user",
        )
    )
    staff.user_permissions.set(permissions)
    return staff


@pytest.fixture
def sample_permission():
    """Return a stable built-in permission."""
    return Permission.objects.select_related("content_type").get(codename="view_group")


def test_permission_list_requires_staff_permission(api_client: APIClient, user):
    api_client.force_authenticate(user=user)

    response = api_client.get(reverse("authkit-api:permissions:permission-list"))

    assert response.status_code == 403


def test_permission_list(api_client: APIClient, staff_user):
    api_client.force_authenticate(user=staff_user)

    response = api_client.get(reverse("authkit-api:permissions:permission-list"))

    assert response.status_code == 200
    assert response.data
    assert {"id", "name", "codename", "content_type_id", "app_label", "model"} <= set(
        response.data[0]
    )


@override_settings(AUTHKIT={"ADMIN_API_REQUIRE_STAFF": False})
def test_permission_list_can_allow_permission_only_access(api_client: APIClient):
    manager = get_user_model().objects.create_user(
        email="manager@example.com",
        password="password",
        is_staff=False,
    )
    manager.user_permissions.add(Permission.objects.get(codename="view_permission"))
    api_client.force_authenticate(user=manager)

    response = api_client.get(reverse("authkit-api:permissions:permission-list"))

    assert response.status_code == 200
    assert response.data


def test_permission_retrieve(api_client: APIClient, staff_user, sample_permission):
    api_client.force_authenticate(user=staff_user)

    response = api_client.get(
        reverse(
            "authkit-api:permissions:permission-detail",
            kwargs={"pk": sample_permission.pk},
        )
    )

    assert response.status_code == 200
    assert response.data["codename"] == "view_group"
    assert response.data["app_label"] == "auth"
    assert response.data["model"] == "group"


def test_role_permission_assignment_flow(
    api_client: APIClient,
    staff_user,
    sample_permission,
):
    role = Group.objects.create(name="Managers")
    api_client.force_authenticate(user=staff_user)

    assign_response = api_client.post(
        reverse(
            "authkit-api:permissions:permission-assign-to-role",
            kwargs={"role_id": role.pk},
        ),
        {"permission_ids": [sample_permission.pk]},
        format="json",
    )

    assert assign_response.status_code == 200
    assert assign_response.data["permissions"][0]["id"] == sample_permission.pk
    assert role.permissions.filter(pk=sample_permission.pk).exists()

    list_response = api_client.get(
        reverse(
            "authkit-api:permissions:permission-role-permissions",
            kwargs={"role_id": role.pk},
        )
    )
    assert list_response.status_code == 200
    assert list_response.data["permissions"][0]["codename"] == "view_group"

    remove_response = api_client.post(
        reverse(
            "authkit-api:permissions:permission-remove-from-role",
            kwargs={"role_id": role.pk},
        ),
        {"permission_ids": [sample_permission.pk]},
        format="json",
    )

    assert remove_response.status_code == 200
    assert remove_response.data["permissions"] == []
    assert not role.permissions.filter(pk=sample_permission.pk).exists()


def test_user_direct_permission_assignment_flow(
    api_client: APIClient,
    staff_user,
    user,
    sample_permission,
):
    api_client.force_authenticate(user=staff_user)

    assign_response = api_client.post(
        reverse(
            "authkit-api:permissions:permission-assign-to-user",
            kwargs={"user_id": user.pk},
        ),
        {"permission_ids": [sample_permission.pk]},
        format="json",
    )

    assert assign_response.status_code == 200
    assert assign_response.data["permissions"][0]["id"] == sample_permission.pk
    assert user.user_permissions.filter(pk=sample_permission.pk).exists()

    list_response = api_client.get(
        reverse(
            "authkit-api:permissions:permission-user-permissions",
            kwargs={"user_id": user.pk},
        )
    )
    assert list_response.status_code == 200
    assert list_response.data["permissions"][0]["codename"] == "view_group"

    remove_response = api_client.post(
        reverse(
            "authkit-api:permissions:permission-remove-from-user",
            kwargs={"user_id": user.pk},
        ),
        {"permission_ids": [sample_permission.pk]},
        format="json",
    )

    assert remove_response.status_code == 200
    assert remove_response.data["permissions"] == []
    assert not user.user_permissions.filter(pk=sample_permission.pk).exists()
