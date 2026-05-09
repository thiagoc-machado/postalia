from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.credits.services import grant_points
from apps.subscriptions.models import SubscriptionPlan, UserSubscription
from apps.subscriptions.services import assign_free_subscription, get_free_plan, seed_default_plans

from .models import PaymentCustomer, PaymentEvent, PaymentSubscription
from .providers.creem import CreemProvider


PAID_PLAN_CODES = ("starter", "pro", "agency")
GRANT_EVENT_TYPES = {
    "checkout.completed",
    "subscription.active",
    "subscription.paid",
    "subscription.trialing",
}
REVOKE_EVENT_TYPES = {
    "subscription.canceled",
    "subscription.expired",
    "subscription.past_due",
}


@dataclass(frozen=True)
class BillingSubscriptionSnapshot:
    plan_code: str
    status: str
    current_period_start: str | None
    current_period_end: str | None
    cancel_at_period_end: bool
    payment_provider: str = "creem"


def _provider() -> CreemProvider:
    from .config import get_creem_base_url

    return CreemProvider(
        api_key=settings.CREEM_API_KEY,
        base_url=get_creem_base_url(settings),
        webhook_secret=settings.CREEM_WEBHOOK_SECRET,
    )


def _product_id_for(plan_code: str) -> str:
    mapping = {
        "starter": settings.CREEM_STARTER_PRODUCT_ID,
        "pro": settings.CREEM_PRO_PRODUCT_ID,
        "agency": settings.CREEM_AGENCY_PRODUCT_ID,
    }
    try:
        return mapping[plan_code]
    except KeyError as exc:
        raise ValueError("Unsupported paid plan.") from exc


def _parse_iso_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000, tz=dt_timezone.utc)
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt_timezone.utc)
    return None


def _payload_object(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("object") or payload.get("data") or payload


def _event_type(payload: dict[str, Any]) -> str:
    return str(payload.get("eventType") or payload.get("event_type") or payload.get("type") or "").strip().lower()


def _payment_subscription_status_from_event(event_type: str, object_payload: dict[str, Any]) -> str:
    raw_status = str(object_payload.get("status") or "").strip().lower()
    if raw_status in {choice for choice, _ in PaymentSubscription.Status.choices}:
        return raw_status
    if event_type == "subscription.trialing":
        return PaymentSubscription.Status.TRIALING
    if event_type in GRANT_EVENT_TYPES:
        return PaymentSubscription.Status.ACTIVE
    if event_type == "subscription.past_due":
        return PaymentSubscription.Status.PAST_DUE
    if event_type == "subscription.canceled":
        return PaymentSubscription.Status.CANCELED
    if event_type == "subscription.expired":
        return PaymentSubscription.Status.EXPIRED
    if event_type == "subscription.incomplete":
        return PaymentSubscription.Status.INCOMPLETE
    return PaymentSubscription.Status.UNKNOWN


def _plan_code_from_product_id(product_id: str | None) -> str | None:
    if not product_id:
        return None
    mapping = {
        settings.CREEM_STARTER_PRODUCT_ID: "starter",
        settings.CREEM_PRO_PRODUCT_ID: "pro",
        settings.CREEM_AGENCY_PRODUCT_ID: "agency",
    }
    return mapping.get(product_id)


def _extract_user_and_plan(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    object_payload = _payload_object(payload)
    metadata = object_payload.get("metadata") or payload.get("metadata") or {}
    user_id = metadata.get("userId") or metadata.get("user_id") or metadata.get("referenceId")
    plan_code = metadata.get("planCode") or metadata.get("plan_code")

    customer = object_payload.get("customer") or {}
    if not user_id and isinstance(customer, dict):
        email = customer.get("email")
        if email:
            from apps.accounts.models import User

            user = User.objects.filter(email__iexact=email).first()
            if user:
                user_id = str(user.id)

    if not plan_code:
        product = object_payload.get("product") or {}
        product_id = None
        if isinstance(product, dict):
            product_id = product.get("id") or product.get("product_id")
        product_id = product_id or object_payload.get("product_id") or payload.get("product_id")
        plan_code = _plan_code_from_product_id(product_id)

    return (str(user_id) if user_id is not None else None, plan_code)


class BillingService:
    def __init__(self, provider: CreemProvider | None = None):
        self.provider = provider or _provider()

    def create_checkout(self, user, plan_code: str) -> str:
        if plan_code not in PAID_PLAN_CODES:
            raise ValueError("Unsupported plan.")
        seed_default_plans()
        plan = SubscriptionPlan.objects.get(code=plan_code)
        if not plan.is_active:
            raise ValueError("Selected plan is not active.")

        customer = self._get_or_create_customer(user)
        result = self.provider.create_checkout_session(
            product_id=_product_id_for(plan_code),
            success_url=settings.CREEM_SUCCESS_URL,
            cancel_url=settings.CREEM_CANCEL_URL,
            customer_email=user.email,
            metadata={
                "userId": str(user.id),
                "userEmail": user.email,
                "planCode": plan_code,
            },
            request_id=f"postalia-{user.id}-{plan_code}-{uuid.uuid4().hex}",
        )
        if customer.external_customer_id:
            self._attach_customer_metadata(customer, user.email)
        return result.checkout_url

    def create_portal(self, user) -> str | None:
        customer = PaymentCustomer.objects.filter(user=user, provider="creem").first()
        if not customer or not customer.external_customer_id:
            return None
        result = self.provider.create_customer_portal(customer.external_customer_id, settings.CREEM_PORTAL_RETURN_URL)
        return result.customer_portal_link

    def get_subscription_snapshot(self, user) -> BillingSubscriptionSnapshot:
        payment_subscription = PaymentSubscription.objects.filter(user=user, provider="creem").first()
        if payment_subscription:
            return BillingSubscriptionSnapshot(
                plan_code=payment_subscription.plan_code,
                status=payment_subscription.status,
                current_period_start=payment_subscription.current_period_start.isoformat() if payment_subscription.current_period_start else None,
                current_period_end=payment_subscription.current_period_end.isoformat() if payment_subscription.current_period_end else None,
                cancel_at_period_end=payment_subscription.cancel_at_period_end,
            )

        subscription = assign_free_subscription(user)
        return BillingSubscriptionSnapshot(
            plan_code=subscription.plan.code,
            status=subscription.status,
            current_period_start=subscription.current_period_start.isoformat() if subscription.current_period_start else None,
            current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            cancel_at_period_end=False,
        )

    @transaction.atomic
    def process_webhook(self, raw_body: bytes, signature: str | None, timestamp: str | None = None) -> tuple[PaymentEvent, str]:
        allowed_skew = getattr(settings, "PAYMENT_WEBHOOK_ALLOWED_SKEW_SECONDS", 300)
        if not self.provider.verify_webhook_signature(raw_body, signature, timestamp, allowed_skew):
            raise ValueError("Invalid Creem webhook signature.")

        payload = self.provider.parse_json(raw_body)
        event_id = str(payload.get("id") or payload.get("event_id") or "").strip()
        event_type = _event_type(payload)
        if not event_id or not event_type:
            raise ValueError("Malformed webhook payload.")

        event, created = PaymentEvent.objects.select_for_update().get_or_create(
            external_event_id=event_id,
            defaults={
                "provider": "creem",
                "event_type": event_type,
                "raw_payload": payload,
                "processed": False,
            },
        )
        if not created and event.processed:
            return event, "duplicate"

        if event.event_type != event_type or event.raw_payload != payload:
            event.event_type = event_type
            event.raw_payload = payload
            event.save(update_fields=["event_type", "raw_payload"])

        user_id, plan_code = _extract_user_and_plan(payload)
        if not user_id:
            raise ValueError("Webhook payload does not reference a user.")

        from apps.accounts.models import User

        user = User.objects.select_for_update().get(pk=user_id)
        object_payload = _payload_object(payload)
        customer = object_payload.get("customer") or {}
        customer_id = None
        if isinstance(customer, dict):
            customer_id = customer.get("id") or customer.get("customer_id")
        customer_id = customer_id or object_payload.get("customer_id")
        subscription_id = (
            object_payload.get("subscription_id")
            or object_payload.get("subscription", {}).get("id")
            or object_payload.get("id")
        )
        period_start = _parse_iso_datetime(object_payload.get("current_period_start") or object_payload.get("period_start"))
        period_end = _parse_iso_datetime(object_payload.get("current_period_end") or object_payload.get("period_end"))
        cancel_at_period_end = bool(object_payload.get("cancel_at_period_end") or object_payload.get("scheduled_cancel") or event_type == "subscription.scheduled_cancel")
        status = _payment_subscription_status_from_event(event_type, object_payload)

        payment_customer = self._get_or_create_customer(user)
        if customer_id:
            payment_customer.external_customer_id = customer_id
        payment_customer.email = getattr(user, "email", payment_customer.email)
        payment_customer.save(update_fields=["external_customer_id", "email", "updated_at"])

        payment_subscription = self._get_or_create_payment_subscription(user)
        if not plan_code and payment_subscription.plan_code:
            plan_code = payment_subscription.plan_code
        if event_type in GRANT_EVENT_TYPES and plan_code not in PAID_PLAN_CODES:
            raise ValueError("Webhook payload does not identify a paid plan.")
        payment_subscription.external_subscription_id = subscription_id or payment_subscription.external_subscription_id
        payment_subscription.external_customer_id = customer_id or payment_subscription.external_customer_id
        payment_subscription.raw_payload = payload
        payment_subscription.cancel_at_period_end = cancel_at_period_end
        payment_subscription.status = status
        if plan_code:
            payment_subscription.plan_code = plan_code
        if period_start:
            payment_subscription.current_period_start = period_start
        if period_end:
            payment_subscription.current_period_end = period_end

        if event_type in GRANT_EVENT_TYPES and plan_code in PAID_PLAN_CODES:
            self._apply_paid_access(user, plan_code, period_start, period_end, status)
            event.processed = True
            event.processed_at = timezone.now()
            event.save(update_fields=["processed", "processed_at"])
            payment_subscription.save()
            return event, "activated"

        if event_type in REVOKE_EVENT_TYPES or event_type == "subscription.scheduled_cancel":
            self._apply_free_access(user)
            payment_subscription.plan_code = "free"
            payment_subscription.save()
            event.processed = True
            event.processed_at = timezone.now()
            event.save(update_fields=["processed", "processed_at"])
            return event, "revoked"

        payment_subscription.save()
        event.processed = True
        event.processed_at = timezone.now()
        event.save(update_fields=["processed", "processed_at"])
        return event, "processed"

    def _get_or_create_customer(self, user):
        customer, _ = PaymentCustomer.objects.get_or_create(
            user=user,
            provider="creem",
            defaults={"email": user.email},
        )
        return customer

    def _get_or_create_payment_subscription(self, user):
        subscription, _ = PaymentSubscription.objects.get_or_create(
            user=user,
            provider="creem",
            defaults={
                "plan_code": "free",
                "status": PaymentSubscription.Status.UNKNOWN,
                "raw_payload": {},
            },
        )
        return subscription

    def _apply_paid_access(self, user, plan_code: str, period_start: datetime | None, period_end: datetime | None, status: str) -> None:
        seed_default_plans()
        plan = SubscriptionPlan.objects.get(code=plan_code)
        subscription = UserSubscription.objects.select_for_update().filter(user=user).first()
        if subscription is None:
            subscription = assign_free_subscription(user)
        subscription.plan = plan
        subscription.status = status if status in UserSubscription.Status.values else UserSubscription.Status.ACTIVE
        if period_start:
            subscription.current_period_start = period_start
        if period_end:
            subscription.current_period_end = period_end
        subscription.save()

    def _apply_free_access(self, user) -> None:
        free_plan = get_free_plan()
        subscription = UserSubscription.objects.select_for_update().filter(user=user).first()
        if subscription is None:
            subscription = assign_free_subscription(user)
        subscription.plan = free_plan
        subscription.status = UserSubscription.Status.ACTIVE
        subscription.current_period_start = timezone.now()
        subscription.current_period_end = timezone.now() + timedelta(days=30)
        subscription.save(update_fields=["plan", "status", "current_period_start", "current_period_end", "updated_at"])

    def _attach_customer_metadata(self, customer, email: str) -> None:
        customer.email = email
        customer.save(update_fields=["email", "updated_at"])


def billing_service() -> BillingService:
    return BillingService()


def subscription_snapshot(user) -> dict[str, Any]:
    snapshot = billing_service().get_subscription_snapshot(user)
    return {
        "plan_code": snapshot.plan_code,
        "status": snapshot.status,
        "current_period_start": snapshot.current_period_start,
        "current_period_end": snapshot.current_period_end,
        "cancel_at_period_end": snapshot.cancel_at_period_end,
        "payment_provider": snapshot.payment_provider,
    }
