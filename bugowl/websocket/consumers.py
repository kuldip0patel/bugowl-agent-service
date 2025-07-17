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
			self.scope['user_business'] = user.get('business')

			self.group_name = f'BrowserStreaming_Business_{self.scope["user_business"]}'

			await self.channel_layer.group_add(  # type: ignore
				self.group_name, self.channel_name
			)
			await self.accept()
			logger.info(f'WebSocket connection established for user: {self.scope["user_email"]}')

		else:
			logger.error('WebSocket connection failed: Authorization header missing', exc_info=True)
			await self.close(code=401, reason='Authorization header missing')

	async def disconnect(self, close_code):
		if hasattr(self, 'group_name'):
			await self.channel_layer.group_discard(  # type: ignore
				self.group_name, self.channel_name
			)
		else:
			logger.warning('WebSocket disconnect called without group_name set')
		reason = self.scope.get('auth_error', 'Connection closed')
		logger.info(f'WebSocket connection closed with code: {close_code}, reason: {reason}')

	async def receive(self, text_data):
		data = json.loads(text_data)
		logger.info(f'Received data: {data}')

		await self.send(text_data=json.dumps(data))

	async def send_frame(self, event):
		frame_data = event.get('frame', None)
		job_uuid = event.get('job_uuid', None)
		if not frame_data:
			logger.warning('No frame to send')
			return

		if not job_uuid:
			logger.error('No job UUID provided for frame sending')
			return

		try:
			await self.send(text_data=json.dumps({'type': 'browser_frame', 'frame': frame_data, 'job_uuid': job_uuid}))
			# logger.info(f'Frame sent to websocket grp')
		except Exception as e:
			logger.error(f'Error sending frame: {e}', exc_info=True)
