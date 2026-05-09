from __future__ import annotations

from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from apps.accounts.models import User

from .models import SubscriptionPlan, UserSubscription


DEFAULT_PLANS = [
    {
        "code": "free",
        "name": "Free",
        "monthly_price": 0,
        "text_limit": 3,
        "image_limit": 0,
        "brand_limit": 1,
        "has_watermark": True,
        "has_calendar": False,
        "has_batch_generation": False,
    },
    {
        "code": "starter",
        "name": "Starter",
        "monthly_price": 5,
        "text_limit": 50,
        "image_limit": 10,
        "brand_limit": 1,
        "has_watermark": False,
        "has_calendar": False,
        "has_batch_generation": False,
    },
    {
        "code": "pro",
        "name": "Pro",
        "monthly_price": 12,
        "text_limit": 200,
        "image_limit": 40,
        "brand_limit": 3,
        "has_watermark": False,
        "has_calendar": True,
        "has_batch_generation": False,
    },
    {
        "code": "agency",
        "name": "Agency",
        "monthly_price": 29,
        "text_limit": 800,
        "image_limit": 150,
        "brand_limit": 999,
        "has_watermark": False,
        "has_calendar": True,
        "has_batch_generation": True,
    },
]


def seed_default_plans() -> None:
    for plan in DEFAULT_PLANS:
        SubscriptionPlan.objects.get_or_create(code=plan["code"], defaults=plan)


def get_plan_by_code(plan_code: str) -> SubscriptionPlan:
    seed_default_plans()
    return SubscriptionPlan.objects.get(code=plan_code)


def get_free_plan() -> SubscriptionPlan:
    return get_plan_by_code("free")


def assign_free_subscription(user: User) -> UserSubscription:
    plan = get_free_plan()
    subscription, _ = UserSubscription.objects.get_or_create(
        user=user,
        defaults={
            "plan": plan,
            "status": UserSubscription.Status.ACTIVE,
            "current_period_start": timezone.now(),
            "current_period_end": timezone.now() + timedelta(days=30),
        },
    )
    if subscription.plan_id != plan.id and subscription.plan.code == "free":
        subscription.plan = plan
        subscription.save(update_fields=["plan", "updated_at"])
    return subscription


def set_user_subscription_plan(
    user: User,
    plan_code: str,
    *,
    status: str | None = None,
    current_period_start=None,
    current_period_end=None,
) -> UserSubscription:
    plan = get_plan_by_code(plan_code)
    subscription = get_user_subscription(user)
    subscription.plan = plan
    if status:
        subscription.status = status
    if current_period_start is not None:
        subscription.current_period_start = current_period_start
    if current_period_end is not None:
        subscription.current_period_end = current_period_end
    subscription.save()
    return subscription


def downgrade_user_to_free(user: User) -> UserSubscription:
    from django.utils import timezone

    return set_user_subscription_plan(
        user,
        "free",
        status=UserSubscription.Status.ACTIVE,
        current_period_start=timezone.now(),
        current_period_end=timezone.now() + timedelta(days=30),
    )


def get_user_subscription(user: User) -> UserSubscription:
    try:
        return user.subscription
    except ObjectDoesNotExist:
        return assign_free_subscription(user)


def get_plan_limits(user: User) -> dict:
    subscription = get_user_subscription(user)
    return {
        "plan_code": subscription.plan.code,
        "plan_name": subscription.plan.name,
        "text_limit": subscription.plan.text_limit,
        "image_limit": subscription.plan.image_limit,
        "brand_limit": subscription.plan.brand_limit,
        "has_watermark": subscription.plan.has_watermark,
        "has_calendar": subscription.plan.has_calendar,
        "has_batch_generation": subscription.plan.has_batch_generation,
        "status": subscription.status,
        "period_start": subscription.current_period_start,
        "period_end": subscription.current_period_end,
    }


def count_generations_in_period(user: User, generation_type: str) -> int:
    from apps.generations.models import GenerationRequest

    subscription = get_user_subscription(user)
    return GenerationRequest.objects.filter(
        user=user,
        generation_type=generation_type,
        created_at__gte=subscription.current_period_start,
        status=GenerationRequest.Status.COMPLETED,
    ).count()


def count_image_generations_in_period(user: User) -> int:
    from apps.generations.models import GenerationRequest

    subscription = get_user_subscription(user)
    return GenerationRequest.objects.filter(
        user=user,
        generation_type__in=[
            GenerationRequest.GenerationType.IMAGE,
            GenerationRequest.GenerationType.FULL_POST,
        ],
        created_at__gte=subscription.current_period_start,
        status=GenerationRequest.Status.COMPLETED,
    ).count()
