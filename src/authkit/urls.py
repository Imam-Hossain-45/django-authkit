"""Package-level URL entrypoint for consumer Django projects."""

from django.urls import include, path

from authkit.conf import authkit_settings

app_name = "authkit"

urlpatterns = [
    path(
        authkit_settings.api_prefix,
        include("authkit.api.urls", namespace="authkit-api"),
    ),
]
