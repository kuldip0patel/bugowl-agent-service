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
        admin_user = None
        try:
            admin_user = User.objects.get(username=settings.DJANGO_SUPER_USER)
        except Exception as e:
            logger.error(e)
        logger.info(admin_user)
        if admin_user:
            logger.info(admin_user)
            logger.info(admin_user.username)
            logger.info(admin_user.email)
            logger.info(admin_user.password)
            admin_user.set_password(settings.DJANGO_SUPER_USER_PASSWORD)
            admin_user.save()
            logger.info('Adming user was updated !!')
        else:
            User.objects.create_superuser(
                username=settings.DJANGO_SUPER_USER,
                email=settings.DJANGO_SUPER_USER_EMAIL,
                password=settings.DJANGO_SUPER_USER_PASSWORD,
            )
            logger.info('Admin user was created !!')
            logger.info('username:'+ settings.DJANGO_SUPER_USER)
            logger.info('password: <Whatever You have set in config/env file OR default=admin>')