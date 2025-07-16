import base64
import json
import os
import uuid
from datetime import datetime

import anyio
import boto3
import cv2
from channels.layers import get_channel_layer
from django.conf import settings

from browser_use.llm import ChatAnthropic, ChatGoogle, ChatGroq, ChatOpenAI

# aws configs
s3_bucket = os.getenv('AWS_STORAGE_BUCKET_NAME')
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = os.getenv('AWS_S3_REGION_NAME')
s3_custom_domain = os.getenv('AWS_S3_CUSTOM_DOMAIN')
obj_params = os.getenv('AWS_S3_OBJECT_PARAMETERS')
s3_object_parameters = json.loads(obj_params) if obj_params else None

google_models = [
	'gemini-2.0-flash',
	'gemini-2.0-flash-exp',
	'gemini-2.0-flash-lite-preview-02-05',
	'Gemini-2.0-exp',
	'gemini-2.5-flash',
]

openai_models = [
	'gpt-4.1',
	'gpt-4.1-mini',
	'gpt-4.1-nano',
	'gpt-4.1-2025-04-14',
	'gpt-4.1-mini-2025-04-14',
	'gpt-4.1-nano-2025-04-14',
	'o4-mini',
	'o4-mini-2025-04-16',
	'o3',
	'o3-2025-04-16',
	'o3-mini',
	'o3-mini-2025-01-31',
	'o1',
	'o1-2024-12-17',
	'o1-preview',
	'o1-preview-2024-09-12',
	'o1-mini',
	'o1-mini-2024-09-12',
	'gpt-4o',
	'gpt-4o-2024-11-20',
	'gpt-4o-2024-08-06',
	'gpt-4o-2024-05-13',
	'gpt-4o-audio-preview',
	'gpt-4o-audio-preview-2024-10-01',
	'gpt-4o-audio-preview-2024-12-17',
	'gpt-4o-audio-preview-2025-06-03',
	'gpt-4o-mini-audio-preview',
	'gpt-4o-mini-audio-preview-2024-12-17',
	'gpt-4o-search-preview',
	'gpt-4o-mini-search-preview',
	'gpt-4o-search-preview-2025-03-11',
	'gpt-4o-mini-search-preview-2025-03-11',
	'chatgpt-4o-latest',
	'codex-mini-latest',
	'gpt-4o-mini',
	'gpt-4o-mini-2024-07-18',
	'gpt-4-turbo',
	'gpt-4-turbo-2024-04-09',
	'gpt-4-0125-preview',
	'gpt-4-turbo-preview',
	'gpt-4-1106-preview',
	'gpt-4-vision-preview',
	'gpt-4',
	'gpt-4-0314',
	'gpt-4-0613',
	'gpt-4-32k',
	'gpt-4-32k-0314',
	'gpt-4-32k-0613',
	'gpt-3.5-turbo',
	'gpt-3.5-turbo-16k',
	'gpt-3.5-turbo-0301',
	'gpt-3.5-turbo-0613',
	'gpt-3.5-turbo-1106',
	'gpt-3.5-turbo-0125',
	'gpt-3.5-turbo-16k-0613',
]

groq_models = ['meta-llama/llama-4-maverick-17b-128e-instruct', 'meta-llama/llama-4-scout-17b-16e-instruct', 'qwen/qwen3-32b']

anthropic_models = [
	'claude-3-7-sonnet-latest',
	'claude-3-7-sonnet-20250219',
	'claude-3-5-haiku-latest',
	'claude-3-5-haiku-20241022',
	'claude-sonnet-4-20250514',
	'claude-sonnet-4-0',
	'claude-4-sonnet-20250514',
	'claude-3-5-sonnet-latest',
	'claude-3-5-sonnet-20241022',
	'claude-3-5-sonnet-20240620',
	'claude-opus-4-0',
	'claude-opus-4-20250514',
	'claude-4-opus-20250514',
	'claude-3-opus-latest',
	'claude-3-opus-20240229',
	'claude-3-sonnet-20240229',
	'claude-3-haiku-20240307',
	'claude-2.1',
	'claude-2.0',
]


def get_llm_model(model_name: str):
	"""
	Returns the appropriate LLM model based on the provided model name.

	Args:
		model_name (str): The name of the LLM model.

	Returns:
		ChatOpenAI | ChatGoogle | ChatGroq | ChatAnthropic: The corresponding LLM model instance.
	"""
	if model_name in google_models:
		return ChatGoogle(model=model_name)
	elif model_name in openai_models:
		return ChatOpenAI(model=model_name)
	elif model_name in groq_models:
		return ChatGroq(model=model_name)
	elif model_name in anthropic_models:
		return ChatAnthropic(model=model_name)
	else:
		raise ValueError(f'Unsupported LLM model: {model_name}.')


def get_video_filename(job_uuid, testcase_uuid, ext='mp4'):
	timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
	uid = str(uuid.uuid4())
	filename = f'{job_uuid}-{testcase_uuid}-{uid}_{timestamp}.{ext}'
	return filename


async def upload_video_S3(job_instance, test_case_run, video_path, logger):
	"""
	Upload the Playwright video recording for the current test case to S3.
	This should be called after the browser session is stopped.
	"""
	try:
		if not video_path:
			logger.error('No video path to upload video.')
			return None

		# Generate new filename
		new_filename = get_video_filename(job_instance.job_uuid, test_case_run.test_case_uuid)  # type: ignore
		business_id = str(job_instance.business)
		new_video_dir = os.path.join('videos', 'browser_recordings', business_id)
		os.makedirs(new_video_dir, exist_ok=True)
		new_video_path = os.path.join(new_video_dir, new_filename)

		# Rename/move the video file
		os.rename(video_path, new_video_path)
		logger.info(f'Renamed video from {video_path} to {new_video_path}')

		# Upload to S3
		if not s3_bucket or not aws_access_key_id or not aws_secret_access_key or not region_name:
			logger.error('S3 configuration is missing. Cannot upload video.')
			return None

		session = boto3.session.Session(  # type: ignore
			aws_access_key_id=aws_access_key_id,
			aws_secret_access_key=aws_secret_access_key,
			region_name=region_name,
		)
		s3 = session.client('s3')
		s3_key = f'videos/browser_recordings/{business_id}/{new_filename}'
		extra_args = {}
		if s3_object_parameters:
			extra_args.update(s3_object_parameters)
		try:
			if 'LOCAL' != settings.ENV.upper():
				s3.upload_file(new_video_path, s3_bucket, s3_key, ExtraArgs=extra_args)
				logger.info(f'Upload to S3 successful: {s3_key}')
			else:
				logger.info(f'Skipping S3 upload in LOCAL environment: {s3_key}')
		except Exception as e:
			logger.error(f'Failed to upload video to S3: {e}')
			return None
		# Delete the local video file after successful upload
		try:
			if 'LOCAL' != settings.ENV.upper():
				os.remove(new_video_path)
				logger.info(f'Deleted local video file: {new_video_path}')
			else:
				logger.info(f'Skipping local file deletion in LOCAL environment: {new_video_path}')
		except Exception as e:
			logger.warning(f'Failed to delete local video file {new_video_path}: {e}')
		if s3_custom_domain:
			url = f'https://{s3_custom_domain}/{s3_key}'
		else:
			url = f'https://{s3_bucket}.s3.amazonaws.com/{s3_key}'
		logger.info(f'S3 video URL: {url}')

		return url

	except Exception as e:
		logger.error(f'Error in upload_video_S3: {e}', exc_info=True)
		return None


async def save_failure_screenshot(browser_session, logger, job_uuid, task_id: str) -> str | None:
	"""
	Take a screenshot of the current browser state and save it to a file.

	Args:
		browser_session: The browser session to take the screenshot from
		task_id: The task ID to include in the filename

	Returns:
		str: The path to the saved screenshot file, or None if saving failed
	"""

	try:
		screenshot_b64 = await browser_session.take_screenshot(full_page=True)
		# Build the directory path: failure_screenshots/job_uuid
		if not job_uuid:
			job_uuid = str(uuid.uuid4())
		if not task_id:
			task_id = str(uuid.uuid4())
		dir_path = os.path.join('failure_screenshots', str(job_uuid))
		os.makedirs(dir_path, exist_ok=True)
		filename = os.path.join(dir_path, f'{task_id}.png')

		async with await anyio.open_file(filename, 'wb') as f:
			await f.write(base64.b64decode(screenshot_b64))
		logger.info(f'Saved failure screenshot to {filename}')

		# Upload to S3
		if not s3_bucket or not aws_access_key_id or not aws_secret_access_key or not region_name:
			logger.error('S3 configuration is missing. Cannot upload screenshot.')
			return None

		session = boto3.session.Session(  # type: ignore
			aws_access_key_id=aws_access_key_id,
			aws_secret_access_key=aws_secret_access_key,
			region_name=region_name,
		)
		s3 = session.client('s3')
		s3_key = f'failure_screenshots/{job_uuid}/{task_id}.png'
		extra_args = {}
		if s3_object_parameters:
			extra_args.update(s3_object_parameters)
		try:
			if 'LOCAL' != settings.ENV.upper():
				s3.upload_file(filename, s3_bucket, s3_key, ExtraArgs=extra_args)
				logger.info(f'Failure screenshot uploaded to S3: {s3_key}')
			else:
				logger.info(f'Skipping S3 upload in LOCAL environment: {s3_key}')
		except Exception as e:
			logger.error(f'Failed to upload failure screenshot to S3: {e}')
			return None
		# Delete the local screenshot file after successful upload
		try:
			if 'LOCAL' != settings.ENV.upper():
				os.remove(filename)
				logger.info(f'Deleted local screenshot file: {filename}')
			else:
				logger.info(f'Skipping local file deletion in LOCAL environment: {filename}')
		except Exception as e:
			logger.warning(f'Failed to delete local screenshot file {filename}: {e}')
		if s3_custom_domain:
			url = f'https://{s3_custom_domain}/{s3_key}'
		else:
			url = f'https://{s3_bucket}.s3.amazonaws.com/{s3_key}'
		logger.info(f'S3 failure screenshot URL: {url}')
		return url
	except Exception as e:
		logger.error(f'Failed to save screenshot: {str(e)}')
		return None


async def send_frame_to_websocket(logger, frame_data, job_uuid, user_id):
	"""
	Send a frame to the WebSocket group.

	Args:
		frame_data: The frame data to send.
		job_uuid: The UUID of the job associated with the frame.
		user_id: The ID of the user associated with the frame.
	"""

	try:
		channel_layer = get_channel_layer()
		if channel_layer:
			_, buffer = cv2.imencode('.jpg', frame_data)
			frame_data_b64 = base64.b64encode(buffer).decode('utf-8')

			group_name = f'BrowserStreaming_{user_id}'

			await channel_layer.group_send(group_name, {'type': 'browser_frame', 'frame': frame_data_b64, 'job_uuid': job_uuid})
	except Exception as e:
		logger.error(f'Failed to send frame to WebSocket: {e}', exc_info=True)
