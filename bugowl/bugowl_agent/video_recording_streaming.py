import asyncio
import base64
import json
import os
import uuid
from datetime import datetime

import boto3
import cv2
import numpy as np
from dotenv import load_dotenv


class VideoRecording:
	def __init__(self, agent_manager, fps=10, video_dir='videos/'):
		# Load environment variables from .env
		load_dotenv()

		self.agent_manager = agent_manager
		self.logger = agent_manager.logger
		self.browser_session = agent_manager.browser_session
		self.fps = fps
		self.video_dir = video_dir
		self.recording = False
		self.paused = False
		self.frames = []
		self.video_path = None
		self._recording_task = None

		# AWS/S3 config from environment
		self.s3_bucket = os.getenv('AWS_STORAGE_BUCKET_NAME')
		self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
		self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
		self.region_name = os.getenv('AWS_S3_REGION_NAME')
		self.s3_acl = os.getenv('AWS_DEFAULT_ACL', 'private')
		self.s3_custom_domain = os.getenv('AWS_S3_CUSTOM_DOMAIN')
		obj_params = os.getenv('AWS_S3_OBJECT_PARAMETERS')
		self.s3_object_parameters = json.loads(obj_params) if obj_params else None

		if self.logger:
			self.logger.info(f"VideoRecording initialized with fps={fps}, video_dir='{video_dir}'")

	def get_video_filename(self, prefix='browser_recording', ext='mp4'):
		timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
		uid = str(uuid.uuid4())
		job_uuid = self.agent_manager.job_instance.job_uuid
		testcase_uuid = self.agent_manager.test_case_run.test_case_uuid
		filename = f'{job_uuid}-{testcase_uuid}-{uid}_{timestamp}.{ext}'
		if self.logger:
			self.logger.debug(f'Generated video filename: {filename}')
		return filename

	async def _capture_frame(self):
		# if self.logger:
		#     self.logger.debug("Capturing browser frame (screenshot)...")
		screenshot_b64 = await self.browser_session.take_screenshot(full_page=True)
		img_bytes = base64.b64decode(screenshot_b64)
		np_arr = np.frombuffer(img_bytes, np.uint8)
		img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
		return img

	async def _record(self):
		if self.logger:
			self.logger.info('Started video recording loop.')
		self.frames = []
		while self.recording:
			if self.paused:
				if self.logger:
					self.logger.debug('Recording paused.')
				await asyncio.sleep(0.1)
				continue
			frame = await self._capture_frame()
			self.frames.append(frame)
			# if self.logger:
			# self.logger.debug(f"Captured frame {len(self.frames)}.")
			await asyncio.sleep(1 / self.fps)
		if self.logger:
			self.logger.info(f'Recording loop ended. Total frames: {len(self.frames)}.')

	async def start(self):
		if self.recording:
			if self.logger:
				self.logger.warning('Recording already in progress.')
			return
		self.recording = True
		self.paused = False
		self.frames = []
		if self.logger:
			self.logger.info('Starting video recording.')
		self._recording_task = asyncio.create_task(self._record())

	async def pause(self):
		self.paused = True
		if self.logger:
			self.logger.info('Video recording paused.')

	async def resume(self):
		self.paused = False
		if self.logger:
			self.logger.info('Video recording resumed.')

	async def stop(self):
		self.recording = False
		if self.logger:
			self.logger.info('Stopping video recording.')
		if self._recording_task:
			await self._recording_task
			self._recording_task = None
		# Save the video as soon as recording stops
		return await self.save()

	async def save(self, filename=None, optimize=True):
		if not self.frames:
			if self.logger:
				self.logger.warning('No frames to save. Video not written.')
			return None
		os.makedirs(self.video_dir, exist_ok=True)
		if not filename:
			filename = self.get_video_filename()
		self.video_path = os.path.join(self.video_dir, filename)
		height, width, _ = self.frames[0].shape
		fourcc = cv2.VideoWriter_fourcc(*'mp4v')
		out = cv2.VideoWriter(self.video_path, fourcc, self.fps, (width, height))
		for frame in self.frames:
			out.write(frame)
		out.release()
		if self.logger:
			self.logger.info(f'Video saved locally at {self.video_path}')
		if optimize:
			return await self.optimize_and_upload(self.video_path)
		else:
			return await self.upload_to_s3(self.video_path)

	async def optimize_and_upload(self, input_path):
		optimized_path = os.path.splitext(input_path)[0] + '_optimized.mp4'
		try:
			import subprocess

			cmd = [
				'ffmpeg',
				'-y',
				'-i',
				input_path,
				'-vcodec',
				'libx264',
				'-crf',
				'28',
				'-preset',
				'veryfast',
				'-movflags',
				'+faststart',
				optimized_path,
			]
			if self.logger:
				self.logger.info(f'Optimizing video with ffmpeg: {" ".join(cmd)}')
			subprocess.run(cmd, check=True)
			video_to_upload = optimized_path
			if self.logger:
				self.logger.info(f'Optimized video saved at {optimized_path}')
		except Exception as e:
			video_to_upload = input_path
			if self.logger:
				self.logger.warning(f'Video optimization failed: {e}. Uploading original video.')
		return await self.upload_to_s3(video_to_upload)

	async def upload_to_s3(self, file_path):
		if self.logger:
			self.logger.info(f"Uploading video to S3 bucket '{self.s3_bucket}'...")
		session = boto3.session.Session(
			aws_access_key_id=self.aws_access_key_id,
			aws_secret_access_key=self.aws_secret_access_key,
			region_name=self.region_name,
		)
		s3 = session.client('s3')
		s3_key = f'videos/browser_recordings/{os.path.basename(file_path)}'
		extra_args = {}
		if self.s3_object_parameters:
			extra_args.update(self.s3_object_parameters)
		try:
			s3.upload_file(file_path, self.s3_bucket, s3_key, ExtraArgs=extra_args)
			if self.logger:
				self.logger.info(f'Upload to S3 successful: {s3_key}')
		except Exception as e:
			if self.logger:
				self.logger.error(f'Failed to upload video to S3: {e}')
			raise
		if self.s3_custom_domain:
			url = f'https://{self.s3_custom_domain}/{s3_key}'
		else:
			url = f'https://{self.s3_bucket}.s3.amazonaws.com/{s3_key}'
		if self.logger:
			self.logger.info(f'S3 video URL: {url}')
		return url
