"""
ASGI config for bugowl_websocket project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from websocket.routing import websocket_urlpatterns

from bugowl_websocket.middleware import JWTAuthMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bugowl_websocket.settings')

application = ProtocolTypeRouter(
	{
		'http': get_asgi_application(),
		'websocket': JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
	}
)
