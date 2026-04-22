"""Reusable API URL routes for django-authkit."""

from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from authkit.api.views import AuthKitInfoView
from authkit.conf import authkit_settings

app_name = "authkit-api"

MODULE_ROUTES = (
    ("auth/", "authkit.authentication.urls"),
    ("password-reset/", "authkit.password_reset.urls"),
    ("verification/", "authkit.verification.urls"),
    ("users/", "authkit.users.urls"),
    ("roles/", "authkit.roles.urls"),
    ("permissions/", "authkit.permissions.urls"),
    ("social-auth/", "authkit.social_auth.urls"),
    ("audit-logs/", "authkit.audit_log.urls"),
)

schema_view = SpectacularAPIView.as_view(
    custom_settings={
        "TITLE": authkit_settings.OPENAPI_TITLE,
        "DESCRIPTION": authkit_settings.OPENAPI_DESCRIPTION,
        "VERSION": authkit_settings.OPENAPI_VERSION,
    }
)

urlpatterns = [
    path("", AuthKitInfoView.as_view(), name="info"),
    *[path(route, include(urlconf)) for route, urlconf in MODULE_ROUTES],
    path("schema/", schema_view, name="schema"),
    path(
        "docs/swagger/",
        SpectacularSwaggerView.as_view(url="../../schema/"),
        name="swagger-ui",
    ),
    path(
        "docs/redoc/",
        SpectacularRedocView.as_view(url="../../schema/"),
        name="redoc",
    ),
]
