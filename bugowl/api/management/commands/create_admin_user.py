import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

logger = logging.getLogger(settings.ENV)


class Command(BaseCommand):
    """
    Create a superuser if none exist
    Example:
        manage.py create_admin_user --user=admin --password=changeme
    """

    # def add_arguments(self, parser):
    #     parser.add_argument("--user", required=True)
    #     parser.add_argument("--password", required=True)
    #     parser.add_argument("--email", default="kuldip@baya.biz")

    def handle(self, *args, **options):
        if User.objects.filter(username=settings.DJANGO_SUPER_USER).exists():
            self.stdout.write(self.style.SUCCESS("Superuser already exists"))
            return

        User.objects.create_superuser(
            username=settings.DJANGO_SUPER_USER,
            email=settings.DJANGO_SUPER_USER_EMAIL,
            password=settings.DJANGO_SUPER_USER_PASSWORD,
        )
        self.stdout.write(self.style.SUCCESS("Superuser created successfully"))
