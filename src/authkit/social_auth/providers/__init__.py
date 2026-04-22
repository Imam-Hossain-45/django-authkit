"""Social authentication provider implementations."""

from authkit.social_auth.providers.registry import (
    get_provider,
    list_providers,
    register_provider,
)

__all__ = ["get_provider", "list_providers", "register_provider"]
