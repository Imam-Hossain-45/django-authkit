"""Google social authentication provider."""

from __future__ import annotations

from typing import Any

from authkit.conf import authkit_settings
from authkit.social_auth.exceptions import (
    InvalidSocialTokenError,
    ProviderUnavailableError,
)
from authkit.social_auth.providers.base import SocialIdentity


class GoogleProvider:
    """Verify Google ID tokens and normalize Google profile data."""

    slug = "google"
    name = "Google"
    authorization_url = "https://accounts.google.com/o/oauth2/v2/auth"
    scopes = ("openid", "email", "profile")

    def get_metadata(self) -> dict[str, Any]:
        """Return public Google OAuth metadata for API clients."""
        return {
            "provider": self.slug,
            "name": self.name,
            "authorization_url": self.authorization_url,
            "client_id": authkit_settings.SOCIAL_AUTH_GOOGLE_CLIENT_ID,
            "scopes": list(self.scopes),
        }

    def verify_token(self, token: str) -> SocialIdentity:
        """Verify a Google ID token with google-auth."""
        try:
            from google.auth.transport import requests
            from google.oauth2 import id_token
        except ImportError as exc:
            raise ProviderUnavailableError(
                "Google social auth requires installing django-authkit-api[social]."
            ) from exc

        client_id = str(authkit_settings.SOCIAL_AUTH_GOOGLE_CLIENT_ID).strip()
        if not client_id:
            raise ProviderUnavailableError(
                "AUTHKIT['SOCIAL_AUTH_GOOGLE_CLIENT_ID'] must be configured."
            )

        try:
            payload = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                client_id,
            )
        except ValueError as exc:
            raise InvalidSocialTokenError("Invalid Google ID token.") from exc

        self.validate_payload(payload)
        return self.build_identity(payload)

    def validate_payload(self, payload: dict[str, Any]) -> None:
        """Validate Google payload fields beyond signature/audience checks."""
        issuer = payload.get("iss")
        if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
            raise InvalidSocialTokenError("Invalid Google token issuer.")

        hosted_domains = set(authkit_settings.SOCIAL_AUTH_GOOGLE_ALLOWED_DOMAINS)
        hosted_domain = payload.get("hd")
        if hosted_domains and hosted_domain not in hosted_domains:
            raise InvalidSocialTokenError("Google account domain is not allowed.")

    def build_identity(self, payload: dict[str, Any]) -> SocialIdentity:
        """Build a normalized social identity from a Google token payload."""
        provider_user_id = str(payload.get("sub") or "")
        email = str(payload.get("email") or "")
        if not provider_user_id or not email:
            raise InvalidSocialTokenError("Google token is missing required identity.")

        return SocialIdentity(
            provider=self.slug,
            provider_user_id=provider_user_id,
            email=email,
            email_verified=bool(payload.get("email_verified")),
            first_name=str(payload.get("given_name") or ""),
            last_name=str(payload.get("family_name") or ""),
            raw=payload,
        )
