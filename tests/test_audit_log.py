"""Tests for authkit audit logging."""

from __future__ import annotations

import re
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

from authkit.models import AuditLog, SocialAccount
from authkit.password_reset.tokens import password_reset_token_generator
from authkit.social_auth.exceptions import InvalidSocialTokenError
from authkit.social_auth.providers.base import SocialIdentity
from authkit.social_auth.providers.registry import get_provider

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
        password="current-password",
        is_verified=True,
    )


@pytest.fixture
def audit_staff():
    """Return a staff user that can view audit logs."""
    staff = get_user_model().objects.create_user(
        email="audit@example.com",
        password="password",
        is_staff=True,
    )
    staff.user_permissions.add(Permission.objects.get(codename="view_auditlog"))
    return staff


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
            raw={"sub": f"google-{token}", "email": f"{token}@example.com"},
        )

    monkeypatch.setattr(provider, "verify_token", verify_token)
    return provider


def test_audit_log_is_append_only(user):
    audit_log = AuditLog.objects.create(
        event_type="test_event",
        target_user=user,
    )

    audit_log.message = "changed"
    with pytest.raises(ValueError, match="append-only"):
        audit_log.save()

    with pytest.raises(ValueError, match="append-only"):
        audit_log.delete()


def test_audit_log_api_is_read_only_and_admin_restricted(
    api_client: APIClient,
    audit_staff,
    user,
):
    AuditLog.objects.create(
        event_type="test_event",
        target_user=user,
        metadata={"ok": True},
    )
    audit_log = AuditLog.objects.first()
    assert audit_log is not None
    assert isinstance(audit_log.id, uuid.UUID)

    denied_response = api_client.get(reverse("authkit-api:audit_log:audit-log-list"))
    assert denied_response.status_code == 401

    api_client.force_authenticate(user=audit_staff)
    list_response = api_client.get(reverse("authkit-api:audit_log:audit-log-list"))
    detail_response = api_client.get(
        reverse(
            "authkit-api:audit_log:audit-log-detail",
            kwargs={"pk": audit_log.pk},
        )
    )
    post_response = api_client.post(
        reverse("authkit-api:audit_log:audit-log-list"),
        {"event_type": "blocked"},
        format="json",
    )

    assert list_response.status_code == 200
    assert list_response.data[0]["event_type"] == "test_event"
    assert detail_response.status_code == 200
    assert post_response.status_code == 405


def test_registration_login_failure_and_success_are_audited(api_client: APIClient):
    register_response = api_client.post(
        reverse("authkit-api:authentication:register"),
        {
            "email": "new@example.com",
            "password": "strong-register-password",
        },
        format="json",
        HTTP_USER_AGENT="pytest-agent",
        REMOTE_ADDR="127.0.0.1",
    )
    assert register_response.status_code == 201

    failed_login = api_client.post(
        reverse("authkit-api:authentication:login"),
        {"email": "new@example.com", "password": "wrong-password"},
        format="json",
    )
    assert failed_login.status_code == 400

    successful_login = api_client.post(
        reverse("authkit-api:authentication:login"),
        {"email": "new@example.com", "password": "strong-register-password"},
        format="json",
    )
    assert successful_login.status_code == 200

    event_types = set(AuditLog.objects.values_list("event_type", flat=True))
    assert {"registration", "login_failure", "login_success"} <= event_types
    registration_log = AuditLog.objects.get(event_type="registration")
    assert registration_log.ip_address == "127.0.0.1"
    assert registration_log.user_agent == "pytest-agent"


def test_logout_and_password_change_are_audited(api_client: APIClient, user):
    login_response = api_client.post(
        reverse("authkit-api:authentication:login"),
        {"email": "user@example.com", "password": "current-password"},
        format="json",
    )
    access = login_response.data["tokens"]["access"]
    refresh = login_response.data["tokens"]["refresh"]

    change_response = api_client.post(
        reverse("authkit-api:authentication:change-password"),
        {
            "current_password": "current-password",
            "new_password": "new-secure-password",
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {access}",
    )
    assert change_response.status_code == 204

    logout_response = api_client.post(
        reverse("authkit-api:authentication:logout"),
        {"refresh": refresh},
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {access}",
    )
    assert logout_response.status_code == 204

    event_types = set(AuditLog.objects.values_list("event_type", flat=True))
    assert {"password_change", "logout"} <= event_types


def test_password_reset_events_are_audited(api_client: APIClient, user):
    request_response = api_client.post(
        reverse("authkit-api:password_reset:request"),
        {"email": "user@example.com"},
        format="json",
    )
    assert request_response.status_code == 202

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = password_reset_token_generator.make_token(user)
    confirm_response = api_client.post(
        reverse("authkit-api:password_reset:confirm"),
        {
            "uid": uid,
            "token": token,
            "new_password": "new-secure-password",
        },
        format="json",
    )
    assert confirm_response.status_code == 204

    event_types = set(AuditLog.objects.values_list("event_type", flat=True))
    assert {"password_reset_requested", "password_reset_completed"} <= event_types


def test_email_verification_events_are_audited(api_client: APIClient, user):
    user.is_verified = False
    user.save(update_fields=["is_verified"])

    request_response = api_client.post(
        reverse("authkit-api:verification:request"),
        {"email": "user@example.com"},
        format="json",
    )
    assert request_response.status_code == 202

    token = re.search(r"Token: (?P<token>.+)", mail.outbox[0].body)
    assert token is not None
    confirm_response = api_client.post(
        reverse("authkit-api:verification:confirm"),
        {"token": token.group("token").strip()},
        format="json",
    )
    assert confirm_response.status_code == 204

    event_types = set(AuditLog.objects.values_list("event_type", flat=True))
    assert {
        "email_verification_requested",
        "email_verification_completed",
    } <= event_types


def test_role_and_permission_assignment_events_are_audited(
    api_client: APIClient,
    user,
):
    staff = get_user_model().objects.create_user(
        email="staff@example.com",
        password="password",
        is_staff=True,
    )
    staff.user_permissions.set(
        Permission.objects.filter(
            codename__in=(
                "view_group",
                "change_group",
                "view_permission",
                "view_user",
                "change_user",
            )
        )
    )
    role = Group.objects.create(name="Members")
    permission = Permission.objects.get(codename="view_group")
    api_client.force_authenticate(user=staff)

    role_assign_response = api_client.post(
        reverse("authkit-api:roles:role-assign-users", kwargs={"pk": role.pk}),
        {"user_ids": [user.pk]},
        format="json",
    )
    permission_assign_response = api_client.post(
        reverse(
            "authkit-api:permissions:permission-assign-to-role",
            kwargs={"role_id": role.pk},
        ),
        {"permission_ids": [permission.pk]},
        format="json",
    )
    permission_remove_response = api_client.post(
        reverse(
            "authkit-api:permissions:permission-remove-from-role",
            kwargs={"role_id": role.pk},
        ),
        {"permission_ids": [permission.pk]},
        format="json",
    )
    role_remove_response = api_client.post(
        reverse("authkit-api:roles:role-remove-users", kwargs={"pk": role.pk}),
        {"user_ids": [user.pk]},
        format="json",
    )
    user_permission_assign_response = api_client.post(
        reverse(
            "authkit-api:permissions:permission-assign-to-user",
            kwargs={"user_id": user.pk},
        ),
        {"permission_ids": [permission.pk]},
        format="json",
    )
    user_permission_remove_response = api_client.post(
        reverse(
            "authkit-api:permissions:permission-remove-from-user",
            kwargs={"user_id": user.pk},
        ),
        {"permission_ids": [permission.pk]},
        format="json",
    )

    assert role_assign_response.status_code == 200
    assert permission_assign_response.status_code == 200
    assert permission_remove_response.status_code == 200
    assert role_remove_response.status_code == 200
    assert user_permission_assign_response.status_code == 200
    assert user_permission_remove_response.status_code == 200
    event_types = set(AuditLog.objects.values_list("event_type", flat=True))
    assert {
        "role_assigned",
        "role_removed",
        "permission_assigned_to_role",
        "permission_removed_from_role",
        "permission_assigned_to_user",
        "permission_removed_from_user",
    } <= event_types


@override_settings(AUTHKIT={"SOCIAL_AUTH_ALLOW_ACCOUNT_LINKING": True})
def test_social_auth_login_and_link_events_are_audited(api_client: APIClient):
    signup_response = api_client.post(
        reverse(
            "authkit-api:social_auth:token-exchange",
            kwargs={"provider": "google"},
        ),
        {"id_token": "new"},
        format="json",
    )
    assert signup_response.status_code == 200

    user = get_user_model().objects.create_user(
        email="linked@example.com",
        password="password",
    )
    link_response = api_client.post(
        reverse(
            "authkit-api:social_auth:token-exchange",
            kwargs={"provider": "google"},
        ),
        {"id_token": "linked"},
        format="json",
    )
    assert link_response.status_code == 200
    assert SocialAccount.objects.filter(user=user, provider="google").exists()

    event_types = set(AuditLog.objects.values_list("event_type", flat=True))
    assert {"social_auth_login", "social_auth_link"} <= event_types
