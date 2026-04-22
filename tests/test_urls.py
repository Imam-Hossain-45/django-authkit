"""Tests for the unified authkit API URL entrypoint."""

from __future__ import annotations

from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient


def test_unified_authkit_routes_are_available():
    """Package URL entrypoint exposes every module under the API prefix."""
    route_names = {
        "info": "authkit-api:info",
        "register": "authkit-api:authentication:register",
        "password_reset": "authkit-api:password_reset:request",
        "verification": "authkit-api:verification:request",
        "current_user": "authkit-api:users:me",
        "roles": "authkit-api:roles:role-list",
        "permissions": "authkit-api:permissions:permission-list",
        "social_auth": "authkit-api:social_auth:provider-list",
        "audit_logs": "authkit-api:audit_log:audit-log-list",
        "schema": "authkit-api:schema",
        "swagger": "authkit-api:swagger-ui",
        "redoc": "authkit-api:redoc",
    }

    resolved = {name: reverse(route_name) for name, route_name in route_names.items()}

    assert resolved == {
        "info": "/authkit/",
        "register": "/authkit/auth/register/",
        "password_reset": "/authkit/password-reset/request/",
        "verification": "/authkit/verification/request/",
        "current_user": "/authkit/users/me/",
        "roles": "/authkit/roles/",
        "permissions": "/authkit/permissions/",
        "social_auth": "/authkit/social-auth/providers/",
        "audit_logs": "/authkit/audit-logs/",
        "schema": "/authkit/schema/",
        "swagger": "/authkit/docs/swagger/",
        "redoc": "/authkit/docs/redoc/",
    }


@override_settings(ROOT_URLCONF="tests.included_urls")
def test_docs_work_when_authkit_urls_are_included_by_consumer_project():
    """Swagger and Redoc should not depend on root-level authkit-api namespace."""
    client = APIClient()

    swagger_response = client.get("/authkit/docs/swagger/")
    redoc_response = client.get("/authkit/docs/redoc/")

    assert swagger_response.status_code == 200
    assert b"../../schema/" in swagger_response.content
    assert redoc_response.status_code == 200
    assert b"../../schema/" in redoc_response.content
