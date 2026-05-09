from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.credits.services import ensure_wallet
from apps.subscriptions.services import assign_free_subscription

from .models import User


@receiver(post_save, sender=User)
def ensure_user_billing(sender, instance: User, created: bool, **kwargs):
    if created:
        ensure_wallet(instance)
        assign_free_subscription(instance)
