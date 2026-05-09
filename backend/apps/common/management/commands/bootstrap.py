import os

from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.credits.services import ensure_wallet
from apps.subscriptions.services import seed_default_plans


class Command(BaseCommand):
    help = "Bootstrap plans and the initial staff user."

    def handle(self, *args, **options):
        seed_default_plans()
        email = os.getenv("INITIAL_STAFF_EMAIL", "")
        password = os.getenv("INITIAL_STAFF_PASSWORD", "")
        name = os.getenv("INITIAL_STAFF_NAME", "Postalia Staff")
        if email and password:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "name": name,
                    "is_staff": True,
                    "is_superuser": True,
                    "is_email_verified": True,
                },
            )
            if created:
                user.set_password(password)
                user.save(update_fields=["password"])
            else:
                user.name = name
                user.is_staff = True
                user.is_superuser = True
                user.is_email_verified = True
                user.set_password(password)
                user.save()
            ensure_wallet(user)
        self.stdout.write(self.style.SUCCESS("Bootstrap completed."))
