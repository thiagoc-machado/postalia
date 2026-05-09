from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.credits.models import CreditTransaction
from apps.credits.services import grant_points

from .models import RewardedAdEvent


@dataclass(frozen=True)
class RewardedAdStatus:
    enabled: bool
    provider: str
    points_per_ad: int
    daily_limit: int
    watched_today: int
    remaining_today: int


class RewardedAdProvider:
    """Base class for rewarded ad callbacks and verification."""

    name = "base"

    def verify_callback(self, payload: dict) -> bool:
        return False

    def parse_callback(self, payload: dict) -> dict:
        return payload


class MockRewardedAdProvider(RewardedAdProvider):
    name = "mock"

    def verify_callback(self, payload: dict) -> bool:
        return True


def get_rewarded_ad_provider() -> RewardedAdProvider:
    if settings.REWARDED_AD_PROVIDER == "mock":
        return MockRewardedAdProvider()
    return RewardedAdProvider()


def rewarded_ad_status(user) -> RewardedAdStatus:
    today = timezone.localdate()
    watched_today = RewardedAdEvent.objects.filter(
        user=user,
        status=RewardedAdEvent.Status.COMPLETED,
        created_at__date=today,
    ).count()
    daily_limit = int(getattr(settings, "REWARDED_AD_DAILY_LIMIT", 2))
    return RewardedAdStatus(
        enabled=bool(getattr(settings, "ENABLE_REWARDED_ADS", False) or getattr(settings, "ENABLE_DEV_FAKE_AD_REWARDS", False)),
        provider=getattr(settings, "REWARDED_AD_PROVIDER", "mock"),
        points_per_ad=int(getattr(settings, "REWARDED_AD_POINTS", 5)),
        daily_limit=daily_limit,
        watched_today=watched_today,
        remaining_today=max(daily_limit - watched_today, 0),
    )


@transaction.atomic
def complete_rewarded_ad(
    user,
    external_event_id: str,
    ip_address: str | None,
    user_agent: str | None,
    metadata: dict | None = None,
    provider: str | None = None,
) -> RewardedAdEvent:
    if not settings.ENABLE_DEV_FAKE_AD_REWARDS:
        raise PermissionError("Rewarded ad simulation is disabled.")

    provider_name = provider or getattr(settings, "REWARDED_AD_PROVIDER", "mock")
    User.objects.select_for_update().get(pk=user.pk)
    if RewardedAdEvent.objects.filter(external_event_id=external_event_id).exists():
        raise ValueError("Duplicate rewarded ad event.")

    existing_today = RewardedAdEvent.objects.filter(
        user=user,
        status=RewardedAdEvent.Status.COMPLETED,
        created_at__date=timezone.localdate(),
    ).count()
    if existing_today >= int(getattr(settings, "REWARDED_AD_DAILY_LIMIT", 2)):
        raise ValueError("Daily rewarded ad limit reached.")

    points = int(getattr(settings, "REWARDED_AD_POINTS", 5))
    event = RewardedAdEvent.objects.create(
        user=user,
        provider=provider_name,
        external_event_id=external_event_id,
        status=RewardedAdEvent.Status.COMPLETED,
        points_awarded=points,
        ip_address=ip_address,
        user_agent=user_agent or "",
        metadata=metadata or {},
    )

    grant_points(
        user,
        points,
        CreditTransaction.TransactionType.REWARDED_AD,
        "Rewarded ad completion",
        {"provider": provider_name, "external_event_id": external_event_id, "event_id": event.id},
    )
    return event


def rewarded_ad_daily_limit_reached(user) -> bool:
    return rewarded_ad_status(user).remaining_today <= 0
