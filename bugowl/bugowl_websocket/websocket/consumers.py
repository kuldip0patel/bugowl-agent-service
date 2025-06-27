import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from rest_framework.authtoken.models import Token

logger = logging.getLogger(settings.ENV)


class AgentWebSocketConsumer(AsyncWebsocketConsumer):
	async def connect(self):
		headers = self.scope['headers']
		auth_header = dict(headers).get(b'authorization', None)

		if auth_header:
			try:
				token_key = auth_header.decode().split(' ')[1]
				token = Token.objects.get(key=token_key)
				self.scope['user'] = token.user
				logger.info(f'WebSocket connection established for user: {self.scope["user"].username}')
				await self.accept()
			except Token.DoesNotExist:
				await self.close(code=403)
		else:
			await self.close(code=401)

	async def disconnect(self, close_code):
		logger.info(f'WebSocket connection closed with code: {close_code}')
		print('WebSocket connection closed')

	async def receive(self, text_data):
		data = json.loads(text_data)
		logger.info(f'Received data: {data}')

		await self.send(text_data=json.dumps(data))
