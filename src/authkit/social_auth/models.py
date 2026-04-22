"""Models for authkit social authentication."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class SocialAccount(models.Model):
    """Link a Django user to an external social identity provider."""

    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField("provider", max_length=50)
    provider_user_id = models.CharField("provider user id", max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="social_accounts",
        verbose_name="user",
    )
    email = models.EmailField("email address", blank=True)
    extra_data = models.JSONField("extra data", default=dict, blank=True)
    created_at = models.DateTimeField("created at", auto_now_add=True)
    updated_at = models.DateTimeField("updated at", auto_now=True)

    class Meta:
        verbose_name = "social account"
        verbose_name_plural = "social accounts"
        ordering = ["provider", "email"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_user_id"],
                name="authkit_unique_social_account",
            )
        ]

    def __str__(self) -> str:
        """Return a readable provider identity."""
        return f"{self.provider}:{self.provider_user_id}"
