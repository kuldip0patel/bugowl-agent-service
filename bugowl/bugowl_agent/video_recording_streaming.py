import asyncio
import base64
import os

import redis.asyncio as redis
from channels.layers import get_channel_layer
from dotenv import load_dotenv
from playwright._impl._errors import TargetClosedError


class LiveStreaming:
	def __init__(self, agent_manager, group_name=None, channel_name=None, fps=8):
		# Load environment variables from .env
		load_dotenv()

		self.agent_manager = agent_manager
		self.logger = agent_manager.logger
		self.browser_session = agent_manager.browser_session
		self.fps = fps
		self.recording = False
		self.paused = False
		self.redis = None
		if agent_manager.job_instance:
			self.business_id = agent_manager.job_instance.business
			self.job_instance = agent_manager.job_instance
			self.testtask_run = agent_manager.testtask_run
			self.test_case_run = agent_manager.test_case_run

		if bool(channel_name) == bool(group_name):
			raise ValueError('Exactly one of channel_name or group_name must be provided.')

		self.channel_name = channel_name
		self.group_name = group_name

		self.channel_layer = get_channel_layer()  # Get the channel layer for WebSocket communication
		if self.logger:
			self.logger.info(f'VideoRecording initialized with fps={fps}')

	async def _capture_frame(self):
		"""
		Capture a frame using the browser session's screenshot method.
		"""
		try:
			page = await self.browser_session.get_current_page()
			# Taking a viewport screenshot is much faster than a full-page one.
			screenshot = await page.screenshot()
			frame_b64 = base64.b64encode(screenshot).decode('utf-8')
			current_url = page.url if page else None
			# self.logger.info(f'Captured frame for URL: {current_url}')
			return frame_b64, current_url
		except TargetClosedError:
			if self.logger:
				self.logger.error('Browser closed while capturing frame. Skipping frame capture.')
			return None, None
		except Exception as e:
			if self.logger:
				self.logger.error(f'Failed to capture frame: {e}', exc_info=True)
			return None, None

	async def _stream_frames(self):
		"""
		Stream frames to the WebSocket consumer's group by capturing them in a loop.
		"""
		if self.logger:
			self.logger.info('Started streaming frames by capturing in a loop.')

		group_name = self.group_name
		group_key = f'asgi:group:{group_name}'
		try:
			while self.recording:
				if group_name:
					# Check the key type to prevent WRONGTYPE errors
					key_type = await self.redis.type(group_key)  # type:ignore
					if key_type.decode('utf-8') not in ['set', 'zset', 'none']:
						self.logger.warning(f"Deleting key '{group_key}' with wrong type '{key_type.decode('utf-8')}'.")
						await self.redis.delete(group_key)  # type:ignore

					# Use SCARD to efficiently check the number of active connections
					active_connection_count = (
						await self.redis.scard(group_key)  # type:ignore
						if key_type.decode('utf-8') == 'set'
						else await self.redis.zcard(group_key)  # type:ignore
					)  # type:ignore
					if active_connection_count == 0:
						# self.logger.warning(f'No active connections in group {group_name}. Pausing frame capture.')
						await asyncio.sleep(1)  # Sleep for a second if no one is watching
						continue

				if self.paused:
					await asyncio.sleep(0.1)
					continue

				start_time = asyncio.get_event_loop().time()
				frame_b64, current_url = await self._capture_frame()
				if frame_b64 and self.channel_layer:
					payload = {
						'type': 'send_frame',
						'frame': frame_b64,
						'current_url': current_url,
						'job_uuid': (
							str(self.job_instance.job_uuid) if hasattr(self, 'job_instance') and self.job_instance else None
						),
						'job_status': (self.job_instance.status if hasattr(self, 'job_instance') and self.job_instance else None),
						'task_uuid': (
							str(self.testtask_run.test_task_uuid) if hasattr(self, 'testtask_run') and self.testtask_run else None
						),
						'task_status': (
							self.testtask_run.status if hasattr(self, 'testtask_run') and self.testtask_run else None
						),
						'case_uuid': (
							str(self.test_case_run.test_case_uuid)
							if hasattr(self, 'test_case_run') and self.test_case_run
							else None
						),
						'case_status': (
							self.test_case_run.status if hasattr(self, 'test_case_run') and self.test_case_run else None
						),
					}
					if group_name:
						await self.channel_layer.group_send(
							group_name,
							payload,
						)
					elif self.channel_name:
						await self.channel_layer.send(
							self.channel_name,
							payload,
						)
				# Adjust sleep time to maintain the target FPS
				elapsed_time = asyncio.get_event_loop().time() - start_time
				sleep_duration = (1 / self.fps) - elapsed_time
				if sleep_duration > 0:
					await asyncio.sleep(sleep_duration)
		except Exception as e:
			if self.logger:
				self.logger.error(f'Error during frame streaming loop: {e}', exc_info=True)
		finally:
			if self.redis:
				await self.redis.close()

	async def start(self):
		"""
		Start streaming frames.
		"""
		if self.recording:
			if self.logger:
				self.logger.warning('Streaming already in progress.')
			return
		try:
			if (hasattr(self, 'redis') and self.redis is None) and (hasattr(self, 'group_name') and self.group_name):
				# Initialize Redis connection if not already done
				redis_url = os.getenv('DJANGO_CACHE_LOCATION', 'redis://redis-agent:6381/1')
				self.redis = redis.from_url(redis_url)
		except Exception as e:
			if self.logger:
				self.logger.error(f'Failed to connect to Redis: {e}', exc_info=True)
			return
		self.recording = True
		self.paused = False
		if self.logger:
			self.logger.info('Starting frame streaming.')
		asyncio.create_task(self._stream_frames())

	async def pause(self):
		"""
		Pause streaming.
		"""
		self.paused = True
		if self.logger:
			self.logger.info('Frame streaming paused.')

	async def resume(self):
		"""
		Resume streaming.
		"""
		self.paused = False
		if self.logger:
			self.logger.info('Frame streaming resumed.')

	async def stop(self):
		"""
		Stop streaming.
		"""
		self.recording = False
		if hasattr(self, 'redis') and self.redis:
			await self.redis.close()
			self.redis = None
			self.logger.info('Redis connection for streaming closed.')
		if self.logger:
			self.logger.info('Stopping frame streaming.')
