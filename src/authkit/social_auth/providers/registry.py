"""Provider registry for authkit social authentication."""

from __future__ import annotations

from authkit.social_auth.providers.base import SocialAuthProvider
from authkit.social_auth.providers.google import GoogleProvider

providers: dict[str, SocialAuthProvider] = {
    GoogleProvider.slug: GoogleProvider(),
}


def get_provider(slug: str) -> SocialAuthProvider | None:
    """Return a provider by slug."""
    return providers.get(slug)


def list_providers() -> list[SocialAuthProvider]:
    """Return registered providers."""
    return list(providers.values())


def register_provider(provider: SocialAuthProvider) -> None:
    """Register or replace a social authentication provider."""
    providers[provider.slug] = provider
