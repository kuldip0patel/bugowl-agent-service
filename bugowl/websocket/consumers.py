import asyncio
import json
import logging
import uuid

from bugowl_agent.agent import PlayGroundAgentManager
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

from .helpers import COMMAND_HANDLER
from .utils import PLAYCOMMANDS, get_job_streaming_group_name

logger = logging.getLogger(settings.ENV)


class AgentLiveStreamingSocketConsumer(AsyncWebsocketConsumer):
	async def connect(self):
		logger.info('WebSocket connection attempt received')
		logger.info('WebSocket scope path: %s', self.scope.get('path', 'unknown'))
		logger.info('WebSocket scope query_string: %s', self.scope.get('query_string', b'').decode('utf-8'))

		user = self.scope.get('user')
		error = self.scope.get('auth_error')

		logger.info('WebSocket auth - user: %s, error: %s', user, error)

		if error:
			logger.warning('WebSocket connection failed: %s', error)
			await self.close(code=403, reason=error)
		elif user:
			self.scope['user_id'] = user.get('user_id')
			self.scope['user_email'] = user.get('user_email')
			self.scope['user_first_name'] = user.get('first_name')
			self.scope['user_last_name'] = user.get('last_name')
			self.scope['user_business'] = user.get('business')

			self.group_name = None
			await self.accept()
			logger.info('WebSocket connection established for user: %s', self.scope['user_email'])

		else:
			logger.error('WebSocket connection failed: Authorization header missing')
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

		if data.get('COMMAND') != PLAYCOMMANDS.C2S_CONNECT.value:
			logger.error(f'Invalid command received: {data.get("COMMAND")}')
			await self.send(text_data=json.dumps({'ACK': PLAYCOMMANDS.S2C_ERROR.value, 'error': 'Invalid command'}))
			return
		if not data.get('JOB_UUID'):
			logger.error('Job UUID is required')
			await self.send(text_data=json.dumps({'ACK': PLAYCOMMANDS.S2C_ERROR.value, 'error': 'Job UUID is required'}))
			return

		if data.get('COMMAND') == PLAYCOMMANDS.C2S_CONNECT.value:
			self.job_uuid = data.get('JOB_UUID')
			group_name = get_job_streaming_group_name(self.job_uuid)

			if self.group_name != group_name:
				if self.group_name:
					await self.channel_layer.group_discard(self.group_name, self.channel_name)  # type: ignore
				self.group_name = group_name
				await self.channel_layer.group_add(self.group_name, self.channel_name)  # type: ignore
			else:
				logger.info(f'Already connected to group {self.group_name}, skipping group add')

			await self.send(text_data=json.dumps({'ACK': PLAYCOMMANDS.S2C_CONNECT.value, 'job_uuid': self.job_uuid}))

	async def send_frame(self, event):
		frame_data = event.get('frame', None)
		job_uuid = event.get('job_uuid', None)
		job_status = event.get('job_status', None)
		case_uuid = event.get('case_uuid', None)
		case_status = event.get('case_status', None)
		task_uuid = event.get('task_uuid', None)
		task_status = event.get('task_status', None)
		current_url = event.get('current_url', None)
		if not frame_data:
			logger.warning('No frame to send')
			return

		if not job_uuid:
			logger.error('No job UUID provided for frame sending')
			return

		try:
			await self.send(
				text_data=json.dumps(
					{
						'type': 'browser_frame',
						'frame': frame_data,
						'job_uuid': job_uuid,
						'job_status': job_status,
						'current_url': current_url,
						'case_uuid': case_uuid,
						'case_status': case_status,
						'task_uuid': task_uuid,
						'task_status': task_status,
					}
				)
			)
		except Exception as e:
			logger.error(f'Error sending frame: {e}', exc_info=True)


class AgentPlayGroundSocketConsumer(AsyncWebsocketConsumer):
	async def connect(self):
		try:
			logger.info('WebSocket connection attempt received')
			logger.info('WebSocket scope path: %s', self.scope.get('path', 'unknown'))
			logger.info('WebSocket scope query_string: %s', self.scope.get('query_string', b'').decode('utf-8'))

			user = self.scope.get('user')
			error = self.scope.get('auth_error')

			logger.info('WebSocket auth - user: %s, error: %s', user, error)

			if error:
				logger.warning('WebSocket connection failed: %s', error)
				await self.close(code=403, reason=error)
			elif user:
				self.scope['user_id'] = user.get('user_id')
				self.scope['user_email'] = user.get('user_email')
				self.scope['user_first_name'] = user.get('first_name')
				self.scope['user_last_name'] = user.get('last_name')
				self.scope['user_business'] = user.get('business')

				await self.accept()
				self.playground_agent = PlayGroundAgentManager(
					task_id=str(uuid.uuid4()),
					channel_name=self.channel_name,
					save_conversation_path='logs/playground/conversation',
					record_video_dir=None,
				)
				await self.playground_agent.start_browser_session()
				logger.info('WebSocket connection established for user: %s', self.scope['user_email'])
				await self.send(
					text_data=json.dumps(
						{
							'ACK': PLAYCOMMANDS.S2C_CONNECT.value,
						}
					)
				)
			else:
				logger.error('WebSocket connection failed: Authorization header missing')
				await self.close(code=401, reason='Authorization header missing')
		except Exception as e:
			logger.error(f'Error during WebSocket connection: {e}', exc_info=True)
			await self.close(code=500, reason='Internal Server Error')

	async def disconnect(self, close_code):
		try:
			if hasattr(self, 'playground_agent'):
				if self.playground_agent:
					if self.playground_agent.agent:
						self.playground_agent.agent.stop()  # type:ignore
					await self.playground_agent.stop_browser_session()
				logger.info('Browser session stopped successfully.')
			else:
				logger.warning('WebSocket disconnect called without playground_agent set')
			reason = self.scope.get('auth_error', 'Connection closed')
			logger.info(f'WebSocket connection closed with code: {close_code}, reason: {reason}')
		except Exception as e:
			logger.error(f'Error stopping browser session: {e}', exc_info=True)

	async def receive(self, text_data):
		try:
			data = json.loads(text_data)

			logger.info(f'Received data: {data}')

			asyncio.create_task(COMMAND_HANDLER(self, data))

		except Exception as e:
			logger.error(f'Error processing received data: {e}', exc_info=True)
			await self.send(
				text_data=json.dumps({'ACK': PLAYCOMMANDS.S2C_ERROR.value, 'error': f'Error processing received data: {e}'})
			)

	async def send_frame(self, event):
		frame_data = event.get('frame', None)
		job_uuid = event.get('job_uuid', None)
		job_status = event.get('job_status', None)
		case_uuid = event.get('case_uuid', None)
		case_status = event.get('case_status', None)
		task_uuid = event.get('task_uuid', None)
		task_title = event.get('task_title', None)
		task_status = event.get('task_status', None)
		current_url = event.get('current_url', None)
		if not frame_data:
			logger.warning('No frame to send')
			return

		try:
			await self.send(
				text_data=json.dumps(
					{
						'type': 'browser_frame',
						'frame': frame_data,
						'job_uuid': job_uuid,
						'job_status': job_status,
						'current_url': current_url,
						'case_uuid': case_uuid,
						'case_status': case_status,
						'task_uuid': task_uuid,
						'task_title': task_title,
						'task_status': task_status,
					}
				)
			)
		except Exception as e:
			logger.error(f'Error sending frame: {e}', exc_info=True)
