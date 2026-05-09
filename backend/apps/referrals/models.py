from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class Referral(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        REWARDED = "rewarded", "Rewarded"
        PAID_CONFIRMED = "paid_confirmed", "Paid confirmed"
        REJECTED = "rejected", "Rejected"

    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referrals_sent"
    )
    referred_user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referral_received"
    )
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    reward_points = models.PositiveIntegerField(default=15)
    created_at = models.DateTimeField(default=timezone.now)
    validated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
