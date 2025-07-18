import logging
import os
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	import cv2  # type: ignore[import-untyped]
	import numpy as np  # type: ignore[import-untyped]
else:
	try:
		import cv2  # type: ignore[import-untyped]
		import numpy as np  # type: ignore[import-untyped]
	except ImportError:
		cv2 = None  # type: ignore
		np = None  # type: ignore

logger = logging.getLogger(__name__)


class VideoRecorder:
	def __init__(self, save_dir: str, width: int = 1920, height: int = 1080, fps: int = 30):
		logger.info('Initializing VideoRecorder with save_dir: %s, dimensions: %dx%d, fps: %d', save_dir, width, height, fps)
		if cv2 is None:
			logger.error('OpenCV (cv2) is not available for video recording')
			raise ImportError('OpenCV (cv2) is required for video recording. Install with: pip install opencv-python')

		self.save_dir = save_dir
		self.width = width
		self.height = height
		self.fps = fps
		self.current_video: 'cv2.VideoWriter' | None = None  # type: ignore
		self.current_filename: str | None = None

		# Create save directory if it doesn't exist
		logger.info('Creating save directory: %s', save_dir)
		os.makedirs(save_dir, exist_ok=True)
		logger.info('VideoRecorder initialized successfully')

	def start_recording(self, action_index: int):
		"""Start recording a new video segment"""
		logger.info('Starting video recording for action index: %d', action_index)
		if cv2 is None:
			logger.error('OpenCV (cv2) is not available for video recording')
			raise ImportError('OpenCV (cv2) is required for video recording')

		if self.current_video is not None:
			logger.info('Stopping existing recording before starting new one')
			self.stop_recording()

		timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
		filename = f'action_{action_index}_{timestamp}.mp4'
		self.current_filename = os.path.join(self.save_dir, filename)
		logger.info('Generated video filename: %s', self.current_filename)

		fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # type: ignore[attr-defined]
		logger.info('Creating VideoWriter with codec: mp4v, fps: %d, dimensions: %dx%d', self.fps, self.width, self.height)
		self.current_video = cv2.VideoWriter(self.current_filename, fourcc, self.fps, (self.width, self.height))  # type: ignore[attr-defined]

		if not self.current_video.isOpened():
			logger.error('Failed to open video writer for: %s', self.current_filename)
			raise RuntimeError(f'Failed to open video writer for {self.current_filename}')

		logger.info('Started recording to %s', self.current_filename)

	def add_frame(self, frame: np.ndarray):
		"""Add a frame to the current video"""
		if self.current_video is not None:
			logger.debug('Adding frame to video recording (shape: %s)', frame.shape)
			self.current_video.write(frame)
		else:
			logger.warning('Attempted to add frame but no video recording is active')

	def stop_recording(self):
		"""Stop the current recording"""
		logger.info('Stopping video recording')
		if self.current_video is not None:
			logger.info('Releasing video writer for: %s', self.current_filename)
			self.current_video.release()
			self.current_video = None
			logger.info('Stopped recording to %s', self.current_filename)
			self.current_filename = None
		else:
			logger.warning('Attempted to stop recording but no video recording is active')


class LiveStreamer:
	def __init__(self, stream_url: str, width: int = 1920, height: int = 1080, fps: int = 30):
		logger.info('Initializing LiveStreamer with stream_url: %s, dimensions: %dx%d, fps: %d', stream_url, width, height, fps)
		self.stream_url = stream_url
		self.width = width
		self.height = height
		self.fps = fps
		self.stream: cv2.VideoWriter | None = None
		logger.info('LiveStreamer initialized successfully')

	def start_streaming(self):
		"""Start streaming to the specified URL"""
		logger.info('Starting live streaming to: %s', self.stream_url)
		if cv2 is None:
			logger.error('OpenCV (cv2) is not available for streaming')
			raise ImportError('OpenCV (cv2) is required for streaming')

		if self.stream is not None:
			logger.info('Stopping existing stream before starting new one')
			self.stop_streaming()

		# Initialize streaming (example using RTMP)
		fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # type: ignore[attr-defined]
		logger.info(
			'Creating VideoWriter for streaming with codec: mp4v, fps: %d, dimensions: %dx%d', self.fps, self.width, self.height
		)
		self.stream = cv2.VideoWriter(self.stream_url, fourcc, self.fps, (self.width, self.height))  # type: ignore[attr-defined]

		if not self.stream.isOpened():
			logger.error('Failed to open stream writer for: %s', self.stream_url)
			raise RuntimeError(f'Failed to open stream writer for {self.stream_url}')

		logger.info('Started streaming to %s', self.stream_url)

	def add_frame(self, frame: np.ndarray):
		"""Add a frame to the stream"""
		if self.stream is not None:
			logger.debug('Adding frame to live stream (shape: %s)', frame.shape)
			self.stream.write(frame)
		else:
			logger.warning('Attempted to add frame but no live stream is active')

	def stop_streaming(self):
		"""Stop the current stream"""
		logger.info('Stopping live streaming')
		if self.stream is not None:
			logger.info('Releasing stream writer for: %s', self.stream_url)
			self.stream.release()
			self.stream = None
			logger.info('Stopped streaming to %s', self.stream_url)
		else:
			logger.warning('Attempted to stop streaming but no live stream is active')


async def capture_screen(page) -> 'np.ndarray':
	"""Capture the current screen as a numpy array"""
	logger.debug('Starting screen capture')
	if cv2 is None or np is None:
		logger.error('OpenCV (cv2) and numpy are not available for screen capture')
		raise ImportError('OpenCV (cv2) and numpy are required for screen capture')

	logger.debug('Taking screenshot from page')
	screenshot = await page.screenshot()
	logger.debug('Screenshot captured, size: %d bytes', len(screenshot))

	# Convert bytes to numpy array
	nparr = np.frombuffer(screenshot, np.uint8)  # type: ignore[attr-defined]
	logger.debug('Converting screenshot to numpy array')
	frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # type: ignore[attr-defined]

	if frame is None:
		logger.error('Failed to decode screenshot to frame')
		raise RuntimeError('Failed to decode screenshot')

	logger.debug('Screen capture completed successfully, frame shape: %s', frame.shape)
	return frame
