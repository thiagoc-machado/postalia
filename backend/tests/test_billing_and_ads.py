from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import patch

import pytest
from django.test import override_settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.ads.models import RewardedAdEvent
from apps.credits.models import CreditTransaction
from apps.payments.models import PaymentCustomer, PaymentEvent, PaymentSubscription
from apps.subscriptions.services import assign_free_subscription


def auth_client(api_client, user):
    token = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@dataclass
class FakeCheckoutResult:
    checkout_url: str
    raw_response: dict[str, Any]


@dataclass
class FakePortalResult:
    customer_portal_link: str
    raw_response: dict[str, Any]


class FakeCreemProvider:
    def __init__(self, *, verify: bool = True, payload: dict[str, Any] | None = None):
        self.verify = verify
        self.payload = payload or {}

    def create_checkout_session(self, **kwargs):
        return FakeCheckoutResult(checkout_url="https://creem.test/checkout/session", raw_response={"ok": True, **kwargs})

    def create_customer_portal(self, customer_id: str, return_url: str | None = None):
        payload = {"customer_id": customer_id}
        if return_url:
            payload["return_url"] = return_url
        return FakePortalResult(customer_portal_link=f"https://creem.test/portal/{customer_id}", raw_response=payload)

    def verify_webhook_signature(self, raw_body: bytes, signature_header: str | None, timestamp_header: str | None = None, allowed_skew_seconds: int | None = None) -> bool:
        return self.verify

    def parse_json(self, raw_body: bytes) -> dict[str, Any]:
        return self.payload


def _webhook_payload(user: User, event_id: str, event_type: str, plan_code: str) -> dict[str, Any]:
    return {
        "id": event_id,
        "eventType": event_type,
        "object": {
            "id": f"sub_{event_id}",
            "subscription_id": f"sub_{event_id}",
            "status": event_type.split(".")[-1],
            "current_period_start": "2026-01-01T00:00:00Z",
            "current_period_end": "2026-02-01T00:00:00Z",
            "cancel_at_period_end": event_type == "subscription.canceled",
            "customer": {
                "id": f"cus_{event_id}",
                "email": user.email,
            },
            "metadata": {
                "userId": str(user.id),
                "planCode": plan_code,
            },
            "product": {"id": f"{plan_code}_product"},
        },
    }


@pytest.mark.django_db
@override_settings(CREEM_ENABLED=True)
@patch("apps.payments.services._provider", return_value=FakeCreemProvider())
def test_creem_checkout_returns_checkout_url(_provider, api_client):
    user = User.objects.create_user(email="checkout@example.com", password="Password123!", name="Checkout User")
    client = auth_client(api_client, user)

    response = client.post("/api/billing/checkout/", {"plan_code": "starter"}, format="json")

    assert response.status_code == 200
    assert response.data["checkout_url"] == "https://creem.test/checkout/session"


@pytest.mark.django_db
@override_settings(CREEM_ENABLED=True)
@patch("apps.payments.services._provider", return_value=FakeCreemProvider())
def test_creem_portal_returns_portal_url(_provider, api_client):
    user = User.objects.create_user(email="portal@example.com", password="Password123!", name="Portal User")
    PaymentCustomer.objects.create(user=user, provider="creem", email=user.email, external_customer_id="cus_123")
    client = auth_client(api_client, user)

    response = client.post("/api/billing/portal/", {}, format="json")

    assert response.status_code == 200
    assert response.data["portal_url"] == "https://creem.test/portal/cus_123"


@pytest.mark.django_db
def test_billing_checkout_requires_authentication(api_client):
    response = api_client.post("/api/billing/checkout/", {"plan_code": "starter"}, format="json")
    assert response.status_code == 401


@pytest.mark.django_db
@patch("apps.payments.services._provider", return_value=FakeCreemProvider(verify=False))
def test_creem_webhook_rejects_invalid_signature(_provider, api_client):
    response = api_client.generic("POST", "/api/webhooks/creem/", "{}", content_type="application/json", HTTP_CREEM_SIGNATURE="bad")
    assert response.status_code == 400
    assert PaymentEvent.objects.count() == 0


@pytest.mark.django_db
@patch("apps.payments.services._provider")
def test_creem_webhook_activates_subscription_idempotently(mock_provider, api_client):
    user = User.objects.create_user(email="creem-active@example.com", password="Password123!", name="Creem Active")
    assign_free_subscription(user)
    payload = _webhook_payload(user, "evt-active-1", "subscription.active", "pro")
    mock_provider.return_value = FakeCreemProvider(verify=True, payload=payload)

    first = api_client.generic("POST", "/api/webhooks/creem/", "{}", content_type="application/json", HTTP_CREEM_SIGNATURE="sig")
    second = api_client.generic("POST", "/api/webhooks/creem/", "{}", content_type="application/json", HTTP_CREEM_SIGNATURE="sig")

    assert first.status_code == 200
    assert first.data["status"] == "activated"
    assert second.status_code == 200
    assert second.data["status"] == "duplicate"
    assert PaymentEvent.objects.filter(external_event_id="evt-active-1").count() == 1

    user.subscription.refresh_from_db()
    payment_subscription = PaymentSubscription.objects.get(user=user)
    assert user.subscription.plan.code == "pro"
    assert payment_subscription.plan_code == "pro"
    assert payment_subscription.status == PaymentSubscription.Status.ACTIVE


@pytest.mark.django_db
@patch("apps.payments.services._provider")
def test_creem_webhook_cancels_subscription_and_downgrades_to_free(mock_provider, api_client):
    user = User.objects.create_user(email="creem-cancel@example.com", password="Password123!", name="Creem Cancel")
    assign_free_subscription(user)

    activation_payload = _webhook_payload(user, "evt-active-2", "subscription.active", "starter")
    cancel_payload = _webhook_payload(user, "evt-cancel-1", "subscription.canceled", "starter")

    def provider_factory(*args, **kwargs):
        return FakeCreemProvider(verify=True, payload=provider_factory.payload)

    provider_factory.payload = activation_payload
    mock_provider.side_effect = provider_factory
    activation = api_client.generic("POST", "/api/webhooks/creem/", "{}", content_type="application/json", HTTP_CREEM_SIGNATURE="sig")
    assert activation.status_code == 200
    assert activation.data["status"] == "activated"

    provider_factory.payload = cancel_payload
    cancel = api_client.generic("POST", "/api/webhooks/creem/", "{}", content_type="application/json", HTTP_CREEM_SIGNATURE="sig")
    assert cancel.status_code == 200
    assert cancel.data["status"] == "revoked"

    user.subscription.refresh_from_db()
    payment_subscription = PaymentSubscription.objects.get(user=user)
    assert user.subscription.plan.code == "free"
    assert payment_subscription.plan_code == "free"
    assert payment_subscription.status == PaymentSubscription.Status.CANCELED


@pytest.mark.django_db
@override_settings(ENABLE_DEV_FAKE_AD_REWARDS=True, REWARDED_AD_DAILY_LIMIT=2, REWARDED_AD_POINTS=5)
def test_rewarded_ads_daily_limit_and_transaction_integrity(api_client):
    user = User.objects.create_user(email="ads-new@example.com", password="Password123!", name="Ads New")
    client = auth_client(api_client, user)

    first = client.post("/api/rewards/ads/complete/", {"external_event_id": "reward-1"}, format="json")
    second = client.post("/api/rewards/ads/complete/", {"external_event_id": "reward-2"}, format="json")
    third = client.post("/api/rewards/ads/complete/", {"external_event_id": "reward-3"}, format="json")

    assert first.status_code == 201
    assert second.status_code == 201
    assert third.status_code == 400
    assert RewardedAdEvent.objects.filter(user=user, status=RewardedAdEvent.Status.COMPLETED).count() == 2
    assert CreditTransaction.objects.filter(wallet=user.wallet).count() == 2

    user.wallet.refresh_from_db()
    assert user.wallet.points_balance == 10
