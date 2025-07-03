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
		if cv2 is None:
			raise ImportError('OpenCV (cv2) is required for video recording. Install with: pip install opencv-python')

		self.save_dir = save_dir
		self.width = width
		self.height = height
		self.fps = fps
		self.current_video: 'cv2.VideoWriter' | None = None  # type: ignore
		self.current_filename: str | None = None

		# Create save directory if it doesn't exist
		os.makedirs(save_dir, exist_ok=True)

	def start_recording(self, action_index: int):
		"""Start recording a new video segment"""
		if self.current_video is not None:
			self.stop_recording()

		timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
		filename = f'action_{action_index}_{timestamp}.mp4'
		self.current_filename = os.path.join(self.save_dir, filename)

		fourcc = cv2.VideoWriter_fourcc(*'mp4v')
		self.current_video = cv2.VideoWriter(self.current_filename, fourcc, self.fps, (self.width, self.height))
		logger.info(f'Started recording to {self.current_filename}')

	def add_frame(self, frame: np.ndarray):
		"""Add a frame to the current video"""
		if self.current_video is not None:
			self.current_video.write(frame)

	def stop_recording(self):
		"""Stop the current recording"""
		if self.current_video is not None:
			self.current_video.release()
			self.current_video = None
			logger.info(f'Stopped recording to {self.current_filename}')
			self.current_filename = None


class LiveStreamer:
	def __init__(self, stream_url: str, width: int = 1920, height: int = 1080, fps: int = 30):
		self.stream_url = stream_url
		self.width = width
		self.height = height
		self.fps = fps
		self.stream: cv2.VideoWriter | None = None

	def start_streaming(self):
		"""Start streaming to the specified URL"""
		if self.stream is not None:
			self.stop_streaming()

		# Initialize streaming (example using RTMP)
		fourcc = cv2.VideoWriter_fourcc(*'mp4v')
		self.stream = cv2.VideoWriter(self.stream_url, fourcc, self.fps, (self.width, self.height))
		logger.info(f'Started streaming to {self.stream_url}')

	def add_frame(self, frame: np.ndarray):
		"""Add a frame to the stream"""
		if self.stream is not None:
			self.stream.write(frame)

	def stop_streaming(self):
		"""Stop the current stream"""
		if self.stream is not None:
			self.stream.release()
			self.stream = None
			logger.info(f'Stopped streaming to {self.stream_url}')


async def capture_screen(page) -> np.ndarray:
	"""Capture the current screen as a numpy array"""
	screenshot = await page.screenshot()
	# Convert bytes to numpy array
	nparr = np.frombuffer(screenshot, np.uint8)
	frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
	return frame
