from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run migrate with --fake-initial for recovering a partially initialized database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default="default",
            help="Database alias to migrate.",
        )

    def handle(self, *args, **options):
        database = options["database"]
        self.stdout.write(
            self.style.WARNING(
                "Running migrate with --fake-initial. Use this only when the schema already exists but migrations were not recorded."
            )
        )
        call_command(
            "migrate",
            fake_initial=True,
            interactive=False,
            database=database,
            verbosity=options.get("verbosity", 1),
        )
