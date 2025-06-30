import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

logger = logging.getLogger(settings.ENV)


class AgentWebSocketConsumer(AsyncWebsocketConsumer):
	async def connect(self):
		user = self.scope.get('user')
		error = self.scope.get('auth_error')

		if error:
			logger.warning(f'WebSocket connection failed: {error}', exc_info=True)
			await self.close(code=403, reason=error)
		elif user:
			self.scope['user_id'] = user.get('user_id')
			self.scope['user_email'] = user.get('user_email')
			self.scope['user_first_name'] = user.get('first_name')
			self.scope['user_last_name'] = user.get('last_name')
			logger.info(f'WebSocket connection established for user: {self.scope["user_email"]}')
			await self.accept()
			await self.send(text_data=json.dumps({'message': 'Connection established', 'user_email': self.scope['user_email']}))
		else:
			logger.error('WebSocket connection failed: Authorization header missing', exc_info=True)
			await self.close(code=401, reason='Authorization header missing')

	async def disconnect(self, close_code):
		reason = self.scope.get('auth_error', 'Connection closed')
		logger.info(f'WebSocket connection closed with code: {close_code}, reason: {reason}')

	async def receive(self, text_data):
		data = json.loads(text_data)
		logger.info(f'Received data: {data}')

		await self.send(text_data=json.dumps(data))
