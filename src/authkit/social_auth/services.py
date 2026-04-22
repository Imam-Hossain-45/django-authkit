"""Services for authkit social authentication."""

from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from rest_framework import serializers

from authkit.conf import authkit_settings
from authkit.models import SocialAccount, User
from authkit.social_auth.providers.base import SocialIdentity


@dataclass(frozen=True)
class SocialAuthResult:
    """Result of authenticating or linking a social identity."""

    user: User
    social_account: SocialAccount
    created_user: bool = False
    linked_account: bool = False


@transaction.atomic
def authenticate_social_identity(identity: SocialIdentity) -> SocialAuthResult:
    """Authenticate, create, or link a user from a verified social identity."""
    social_account = (
        SocialAccount.objects.select_for_update()
        .filter(
            provider=identity.provider,
            provider_user_id=identity.provider_user_id,
        )
        .select_related("user")
        .first()
    )

    if social_account is not None:
        user = social_account.user
        if not user.is_active:
            raise serializers.ValidationError("This user account is inactive.")
        update_social_account(social_account, identity)
        maybe_mark_user_verified(user, identity)
        return SocialAuthResult(user=user, social_account=social_account)

    user = User.objects.filter(email__iexact=identity.email).first()
    created_user = False
    linked_account = False

    if user is not None:
        if not user.is_active:
            raise serializers.ValidationError("This user account is inactive.")
        if not authkit_settings.SOCIAL_AUTH_ALLOW_ACCOUNT_LINKING:
            raise serializers.ValidationError("A user with this email already exists.")
        linked_account = True
    else:
        if not authkit_settings.SOCIAL_AUTH_ALLOW_SIGNUP:
            raise serializers.ValidationError("Social signup is disabled.")
        user = create_social_user(identity)
        created_user = True

    social_account = SocialAccount.objects.create(
        provider=identity.provider,
        provider_user_id=identity.provider_user_id,
        user=user,
        email=identity.email,
        extra_data=identity.raw,
    )
    maybe_mark_user_verified(user, identity)
    return SocialAuthResult(
        user=user,
        social_account=social_account,
        created_user=created_user,
        linked_account=linked_account,
    )


def create_social_user(identity: SocialIdentity) -> User:
    """Create a local authkit user for a first-time social login."""
    user = User.objects.create_user(
        email=identity.email,
        password=None,
        first_name=identity.first_name,
        last_name=identity.last_name,
        is_verified=(
            bool(identity.email_verified)
            and bool(authkit_settings.SOCIAL_AUTH_MARK_VERIFIED_EMAIL)
        ),
    )
    return user


def maybe_mark_user_verified(user: User, identity: SocialIdentity) -> None:
    """Mark the user verified when the provider verified the email."""
    if (
        identity.email_verified
        and authkit_settings.SOCIAL_AUTH_MARK_VERIFIED_EMAIL
        and not user.is_verified
    ):
        user.is_verified = True
        user.save(update_fields=["is_verified", "updated_at"])


def update_social_account(
    social_account: SocialAccount,
    identity: SocialIdentity,
) -> None:
    """Refresh stored provider email and raw profile data."""
    social_account.email = identity.email
    social_account.extra_data = identity.raw
    social_account.save(update_fields=["email", "extra_data", "updated_at"])
