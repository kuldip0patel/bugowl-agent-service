from django.urls import path

from websocket import consumers

websocket_urlpatterns = [
	path('ws/agent-socket/', consumers.AgentWebSocketConsumer.as_asgi()),  # type: ignore
]
