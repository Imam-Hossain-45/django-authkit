"""Exceptions for authkit social authentication."""

from __future__ import annotations


class SocialAuthError(Exception):
    """Base exception for social authentication failures."""


class ProviderUnavailableError(SocialAuthError):
    """Raised when provider dependencies or configuration are unavailable."""


class InvalidSocialTokenError(SocialAuthError):
    """Raised when a provider token cannot be verified."""
