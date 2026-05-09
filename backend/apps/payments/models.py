from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class PaymentCustomer(models.Model):
    provider = models.CharField(max_length=50, default="creem")
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_customer")
    external_customer_id = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "external_customer_id"],
                condition=Q(external_customer_id__isnull=False),
                name="uniq_payment_customer_provider_external_customer_id",
            )
        ]


class PaymentSubscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        TRIALING = "trialing", "Trialing"
        PAST_DUE = "past_due", "Past due"
        CANCELED = "canceled", "Canceled"
        EXPIRED = "expired", "Expired"
        INCOMPLETE = "incomplete", "Incomplete"
        UNKNOWN = "unknown", "Unknown"

    provider = models.CharField(max_length=50, default="creem")
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_subscription")
    external_subscription_id = models.CharField(max_length=255, null=True, blank=True)
    external_customer_id = models.CharField(max_length=255, null=True, blank=True)
    plan_code = models.CharField(max_length=20, default="free")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNKNOWN)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "external_subscription_id"],
                condition=Q(external_subscription_id__isnull=False),
                name="uniq_payment_subscription_provider_external_subscription_id",
            )
        ]


class PaymentEvent(models.Model):
    provider = models.CharField(max_length=50, default="creem")
    external_event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=120)
    processed = models.BooleanField(default=False)
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
