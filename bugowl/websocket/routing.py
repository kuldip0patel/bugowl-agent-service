from django.urls import re_path

from websocket import consumers

websocket_urlpatterns = [
	re_path(r'agent/LiveStreaming/$', consumers.AgentWebSocketConsumer.as_asgi()),  # type: ignore
]
