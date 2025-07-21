from django.urls import re_path

from .consumers import AgentLiveStreamingSocketConsumer, AgentPlayGroundSocketConsumer

websocket_urlpatterns = [
	re_path(r'agent/LiveStreaming/$', AgentLiveStreamingSocketConsumer.as_asgi()),  # type: ignore
	re_path(r'agent/PlayGround/$', AgentPlayGroundSocketConsumer.as_asgi()),  # type: ignore
]
