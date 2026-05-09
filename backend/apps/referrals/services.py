from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.credits.models import CreditTransaction
from apps.credits.services import grant_points

from .models import Referral


def register_referral(referred_user, referral_code: str) -> Referral | None:
    from apps.accounts.models import User

    if not referral_code:
        return None
    if referred_user.referral_code == referral_code:
        raise ValueError("Self-referral is not allowed.")
    referrer = User.objects.filter(referral_code=referral_code).first()
    if not referrer:
        return None
    referral, created = Referral.objects.get_or_create(
        referred_user=referred_user,
        defaults={"referrer": referrer, "reward_points": 15},
    )
    if not created and referral.referrer_id != referrer.id:
        raise ValueError("Referral already exists.")
    return referral


@transaction.atomic
def maybe_reward_referral_on_first_generation(user) -> Referral | None:
    referral = Referral.objects.select_for_update().filter(referred_user=user).first()
    if not referral or referral.status != Referral.Status.PENDING:
        return referral
    from apps.generations.models import GenerationRequest

    if not GenerationRequest.objects.filter(user=user, status=GenerationRequest.Status.COMPLETED).exists():
        return referral
    grant_points(
        referral.referrer,
        referral.reward_points,
        CreditTransaction.TransactionType.REFERRAL_BONUS,
        "Referral reward",
        {"referred_user_id": user.id, "referral_id": referral.id},
    )
    referral.status = Referral.Status.REWARDED
    referral.validated_at = timezone.now()
    referral.save(update_fields=["status", "validated_at"])
    return referral


@transaction.atomic
def confirm_paid_referral(referral: Referral) -> Referral:
    if referral.status == Referral.Status.REWARDED:
        return referral
    referral.reward_points = 100
    grant_points(
        referral.referrer,
        100,
        CreditTransaction.TransactionType.REFERRAL_BONUS,
        "Paid referral reward",
        {"referred_user_id": referral.referred_user_id, "referral_id": referral.id},
    )
    referral.status = Referral.Status.PAID_CONFIRMED
    referral.validated_at = timezone.now()
    referral.save(update_fields=["status", "reward_points", "validated_at"])
    return referral
