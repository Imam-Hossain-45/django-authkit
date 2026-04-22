"""Tests for authkit role management APIs."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
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
def second_user():
    """Return another regular user."""
    return get_user_model().objects.create_user(
        email="second@example.com",
        password="password",
    )


@pytest.fixture
def staff_user():
    """Return a staff user with role management permissions."""
    staff = get_user_model().objects.create_user(
        email="staff@example.com",
        password="password",
        is_staff=True,
    )
    permissions = Permission.objects.filter(
        content_type__app_label="auth",
        codename__in=("view_group", "add_group", "change_group", "delete_group"),
    )
    staff.user_permissions.set(permissions)
    return staff


def test_role_list_requires_staff_permission(api_client: APIClient, user):
    api_client.force_authenticate(user=user)

    response = api_client.get(reverse("authkit-api:roles:role-list"))

    assert response.status_code == 403


def test_role_list(api_client: APIClient, staff_user):
    Group.objects.create(name="Managers")
    api_client.force_authenticate(user=staff_user)

    response = api_client.get(reverse("authkit-api:roles:role-list"))

    assert response.status_code == 200
    assert response.data[0]["name"] == "Managers"


def test_role_create(api_client: APIClient, staff_user):
    api_client.force_authenticate(user=staff_user)

    response = api_client.post(
        reverse("authkit-api:roles:role-list"),
        {"name": "Editors"},
        format="json",
    )

    assert response.status_code == 201
    assert Group.objects.filter(name="Editors").exists()


def test_role_retrieve(api_client: APIClient, staff_user):
    role = Group.objects.create(name="Auditors")
    api_client.force_authenticate(user=staff_user)

    response = api_client.get(
        reverse("authkit-api:roles:role-detail", kwargs={"pk": role.pk})
    )

    assert response.status_code == 200
    assert response.data["name"] == "Auditors"


def test_role_update(api_client: APIClient, staff_user):
    role = Group.objects.create(name="Old name")
    api_client.force_authenticate(user=staff_user)

    response = api_client.patch(
        reverse("authkit-api:roles:role-detail", kwargs={"pk": role.pk}),
        {"name": "New name"},
        format="json",
    )

    assert response.status_code == 200
    role.refresh_from_db()
    assert role.name == "New name"


def test_role_delete(api_client: APIClient, staff_user):
    role = Group.objects.create(name="Temporary")
    api_client.force_authenticate(user=staff_user)

    response = api_client.delete(
        reverse("authkit-api:roles:role-detail", kwargs={"pk": role.pk})
    )

    assert response.status_code == 204
    assert not Group.objects.filter(pk=role.pk).exists()


def test_role_assign_users(api_client: APIClient, staff_user, user, second_user):
    role = Group.objects.create(name="Members")
    api_client.force_authenticate(user=staff_user)

    response = api_client.post(
        reverse("authkit-api:roles:role-assign-users", kwargs={"pk": role.pk}),
        {"user_ids": [user.pk, second_user.pk]},
        format="json",
    )

    assert response.status_code == 200
    assert user.groups.filter(pk=role.pk).exists()
    assert second_user.groups.filter(pk=role.pk).exists()
    assert response.data["user_count"] == 2


def test_role_remove_users(api_client: APIClient, staff_user, user, second_user):
    role = Group.objects.create(name="Members")
    user.groups.add(role)
    second_user.groups.add(role)
    api_client.force_authenticate(user=staff_user)

    response = api_client.post(
        reverse("authkit-api:roles:role-remove-users", kwargs={"pk": role.pk}),
        {"user_ids": [user.pk]},
        format="json",
    )

    assert response.status_code == 200
    assert not user.groups.filter(pk=role.pk).exists()
    assert second_user.groups.filter(pk=role.pk).exists()
    assert response.data["user_count"] == 1


def test_role_list_users(api_client: APIClient, staff_user, user):
    role = Group.objects.create(name="Members")
    user.groups.add(role)
    api_client.force_authenticate(user=staff_user)

    response = api_client.get(
        reverse("authkit-api:roles:role-users", kwargs={"pk": role.pk})
    )

    assert response.status_code == 200
    assert response.data["users"][0]["email"] == "user@example.com"
