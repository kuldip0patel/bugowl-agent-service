"""
ASGI config for bugowl_websocket project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from api.middleware import JWTAuthMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()
from websocket.routing import websocket_urlpatterns

application = ProtocolTypeRouter(
	{
		'http': get_asgi_application(),
		'websocket': JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
	}
)
