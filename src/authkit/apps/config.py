"""Django application configuration for authkit."""

from django.apps import AppConfig


class AuthKitConfig(AppConfig):
    """Minimal app config for the reusable authkit Django app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "authkit"
    label = "authkit"
    verbose_name = "AuthKit"
