from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class CreditWallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet")
    points_balance = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user_id}:{self.points_balance}"


class CreditTransaction(models.Model):
    class TransactionType(models.TextChoices):
        REGISTRATION_BONUS = "registration_bonus", "Registration bonus"
        DAILY_LOGIN = "daily_login", "Daily login"
        STREAK_BONUS = "streak_bonus", "Streak bonus"
        REFERRAL_BONUS = "referral_bonus", "Referral bonus"
        REWARDED_AD = "rewarded_ad", "Rewarded ad"
        GENERATION_SPEND = "generation_spend", "Generation spend"
        MANUAL = "manual", "Manual"

    wallet = models.ForeignKey(CreditWallet, on_delete=models.CASCADE, related_name="transactions")
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=50, choices=TransactionType.choices)
    reason = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at", "-id"]


class DailyLoginReward(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_login_rewards")
    date = models.DateField()
    streak_count = models.PositiveIntegerField(default=1)
    points_awarded = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = [("user", "date")]
        ordering = ["-date"]
