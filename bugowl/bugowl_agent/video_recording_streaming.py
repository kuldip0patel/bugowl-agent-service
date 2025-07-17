import asyncio
import base64

from channels.layers import get_channel_layer
from dotenv import load_dotenv


class LiveStreaming:
	def __init__(self, agent_manager, fps=8):
		# Load environment variables from .env
		load_dotenv()

		self.agent_manager = agent_manager
		self.logger = agent_manager.logger
		self.browser_session = agent_manager.browser_session
		self.fps = fps
		self.recording = False
		self.paused = False
		self.business_id = agent_manager.job_instance.business
		self.job_uuid = agent_manager.job_instance.job_uuid

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
			return frame_b64
		except Exception as e:
			if self.logger:
				self.logger.error(f'Failed to capture frame: {e}', exc_info=True)
			return None

	async def _stream_frames(self):
		"""
		Stream frames to the WebSocket consumer's group by capturing them in a loop.
		"""
		if self.logger:
			self.logger.info('Started streaming frames by capturing in a loop.')

		group_name = f'BrowserStreaming_Business_{self.business_id}'

		while self.recording:
			if self.paused:
				await asyncio.sleep(0.1)
				continue

			try:
				start_time = asyncio.get_event_loop().time()

				frame_b64 = await self._capture_frame()

				if frame_b64 and self.channel_layer:
					await self.channel_layer.group_send(
						group_name, {'type': 'send_frame', 'frame': frame_b64, 'job_uuid': str(self.job_uuid)}
					)

				# Adjust sleep time to maintain the target FPS
				elapsed_time = asyncio.get_event_loop().time() - start_time
				sleep_duration = (1 / self.fps) - elapsed_time
				if sleep_duration > 0:
					await asyncio.sleep(sleep_duration)

			except Exception as e:
				if self.logger:
					self.logger.error(f'Error during frame streaming loop: {e}', exc_info=True)
				# Stop streaming on error
				break

	async def start(self):
		"""
		Start streaming frames.
		"""
		if self.recording:
			if self.logger:
				self.logger.warning('Streaming already in progress.')
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
		if self.logger:
			self.logger.info('Stopping frame streaming.')
