"""User model for django-authkit."""

from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from authkit.users.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Email-first user model built on Django's auth primitives."""

    id = models.UUIDField("ID", primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        "email address",
        unique=True,
        help_text="Unique email address used as the login identifier.",
    )
    first_name = models.CharField("first name", max_length=150, blank=True)
    last_name = models.CharField("last name", max_length=150, blank=True)
    is_active = models.BooleanField(
        "active",
        default=True,
        help_text=(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    is_staff = models.BooleanField(
        "staff status",
        default=False,
        help_text="Designates whether the user can log into the admin site.",
    )
    is_verified = models.BooleanField(
        "verified",
        default=False,
        help_text="Designates whether the user's email/account is verified.",
    )
    date_joined = models.DateTimeField("date joined", default=timezone.now)
    updated_at = models.DateTimeField("updated at", auto_now=True)

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ["email"]

    def __str__(self) -> str:
        """Return the email address for admin and shell readability."""
        return self.email

    def get_full_name(self) -> str:
        """Return the user's first and last name with whitespace normalized."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return " ".join(full_name.split())

    def get_short_name(self) -> str:
        """Return the user's first name, falling back to email."""
        return self.first_name or self.email
