from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.accounts.models import User

from .models import CreditTransaction, CreditWallet, DailyLoginReward


def ensure_wallet(user: User) -> CreditWallet:
    wallet, _ = CreditWallet.objects.get_or_create(user=user)
    return wallet


@transaction.atomic
def grant_points(user: User, amount: int, transaction_type: str, reason: str, metadata: dict | None = None) -> CreditTransaction:
    if amount <= 0:
        raise ValueError("Amount must be positive.")
    wallet = CreditWallet.objects.select_for_update().get_or_create(user=user)[0]
    wallet.points_balance = F("points_balance") + amount
    wallet.save(update_fields=["points_balance", "updated_at"])
    wallet.refresh_from_db(fields=["points_balance"])
    return CreditTransaction.objects.create(
        wallet=wallet,
        amount=amount,
        transaction_type=transaction_type,
        reason=reason,
        metadata=metadata or {},
    )


@transaction.atomic
def spend_points(user: User, amount: int, transaction_type: str, reason: str, metadata: dict | None = None) -> CreditTransaction:
    if amount <= 0:
        raise ValueError("Amount must be positive.")
    wallet = CreditWallet.objects.select_for_update().get_or_create(user=user)[0]
    if wallet.points_balance < amount:
        raise ValueError("Insufficient points.")
    wallet.points_balance = F("points_balance") - amount
    wallet.save(update_fields=["points_balance", "updated_at"])
    wallet.refresh_from_db(fields=["points_balance"])
    return CreditTransaction.objects.create(
        wallet=wallet,
        amount=-amount,
        transaction_type=transaction_type,
        reason=reason,
        metadata=metadata or {},
    )


@transaction.atomic
def award_daily_login_reward(user: User) -> DailyLoginReward | None:
    today = timezone.localdate()
    if DailyLoginReward.objects.filter(user=user, date=today).exists():
        return None
    yesterday = today - timedelta(days=1)
    previous = DailyLoginReward.objects.filter(user=user, date=yesterday).first()
    streak = previous.streak_count + 1 if previous else 1
    reward = DailyLoginReward.objects.create(
        user=user,
        date=today,
        streak_count=streak,
        points_awarded=1,
    )
    grant_points(user, 1, CreditTransaction.TransactionType.DAILY_LOGIN, "Daily login reward", {"date": str(today)})
    if streak % 7 == 0:
        grant_points(user, 5, CreditTransaction.TransactionType.STREAK_BONUS, "7-day streak reward", {"streak_count": streak})
    return reward


def wallet_summary(user: User) -> dict:
    wallet = ensure_wallet(user)
    return {
        "points_balance": wallet.points_balance,
        "transactions_count": wallet.transactions.count(),
    }
