import logging

from django.conf import settings

logger = logging.getLogger(settings.ENV)

# Create your views here.
logger.info('Testask views module loaded')
