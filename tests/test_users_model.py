"""Tests for the authkit custom user model and manager."""

from __future__ import annotations

import uuid

import pytest
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db


def test_create_user_normalizes_email_and_hashes_password():
    user = get_user_model().objects.create_user(
        email="USER@EXAMPLE.COM",
        password="secure-password",
    )

    assert user.email == "USER@example.com"
    assert user.check_password("secure-password")
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.is_active is True
    assert isinstance(user.id, uuid.UUID)


def test_create_user_requires_email():
    with pytest.raises(ValueError, match="email address"):
        get_user_model().objects.create_user(email="", password="secure-password")


def test_create_superuser_sets_admin_flags():
    user = get_user_model().objects.create_superuser(
        email="admin@example.com",
        password="secure-password",
    )

    assert user.is_staff is True
    assert user.is_superuser is True
    assert user.is_active is True
    assert user.is_verified is True


@pytest.mark.parametrize(
    "field",
    ["is_staff", "is_superuser"],
)
def test_create_superuser_rejects_missing_admin_flags(field: str):
    with pytest.raises(ValueError, match="Superuser must have"):
        get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="secure-password",
            **{field: False},
        )
