"""Base provider contracts for authkit social authentication."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class SocialIdentity:
    """Verified identity returned by a social authentication provider."""

    provider: str
    provider_user_id: str
    email: str
    email_verified: bool = False
    first_name: str = ""
    last_name: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


class SocialAuthProvider(Protocol):
    """Provider interface for social authentication implementations."""

    slug: str
    name: str

    def get_metadata(self) -> dict[str, Any]:
        """Return public metadata needed by clients."""
        ...

    def verify_token(self, token: str) -> SocialIdentity:
        """Verify a provider token and return a normalized identity."""
        ...
