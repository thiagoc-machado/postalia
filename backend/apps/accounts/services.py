from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from apps.credits.services import ensure_wallet, grant_points
from apps.subscriptions.services import assign_free_subscription

User = get_user_model()


@dataclass(frozen=True)
class AuthConfig:
    google_only: bool
    local_auth_enabled: bool
    registration_enabled: bool
    supported_languages: list[str]
    default_language: str


def get_auth_config() -> AuthConfig:
    return AuthConfig(
        google_only=settings.GOOGLE_ONLY,
        local_auth_enabled=not settings.GOOGLE_ONLY,
        registration_enabled=not settings.GOOGLE_ONLY,
        supported_languages=[code for code, _ in settings.LANGUAGES],
        default_language=settings.DEFAULT_LANGUAGE,
    )


def verify_google_credential(credential: str) -> dict:
    if not settings.GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID is not configured.")
    token = id_token.verify_oauth2_token(
        credential,
        google_requests.Request(),
        settings.GOOGLE_CLIENT_ID,
    )
    if token.get("email_verified") is not True:
        raise ValueError("Google email is not verified.")
    return token


def upsert_google_user(token_data: dict) -> User:
    email = token_data["email"]
    user = User.objects.filter(email=email).first()
    if user is None:
        user = User.objects.create_user(
            email=email,
            name=token_data.get("name") or token_data.get("given_name") or email.split("@")[0],
            auth_provider=User.AuthProvider.GOOGLE,
            google_sub=token_data["sub"],
            is_email_verified=True,
        )
        ensure_wallet(user)
        assign_free_subscription(user)
        grant_points(user, 10, "registration_bonus", "Registration bonus")
    else:
        user.auth_provider = User.AuthProvider.GOOGLE
        user.google_sub = token_data["sub"]
        user.is_email_verified = True
        user.save(update_fields=["auth_provider", "google_sub", "is_email_verified", "updated_at"])
    return user


def touch_daily_login_reward(user: User, ip_address: str | None, user_agent: str | None) -> None:
    from apps.credits.services import award_daily_login_reward
    from apps.risk.services import upsert_device_session

    upsert_device_session(user=user, ip_address=ip_address, user_agent=user_agent)
    award_daily_login_reward(user)
