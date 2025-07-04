from django.urls import path

from websocket import consumers

websocket_urlpatterns = [
	path('agent/websocket/', consumers.AgentWebSocketConsumer.as_asgi()),  # type: ignore
]
