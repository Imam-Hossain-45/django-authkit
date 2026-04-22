"""App config for the example pages app."""

from django.apps import AppConfig


class PagesConfig(AppConfig):
    """Configure the example pages app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "pages"
