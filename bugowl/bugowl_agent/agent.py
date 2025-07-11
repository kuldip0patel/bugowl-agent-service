import asyncio
import json
import logging
import os
import uuid
from datetime import datetime

import boto3
import coloredlogs
from api.utils import Browser, JobStatusEnum
from asgiref.sync import sync_to_async
from testask.serializers import TestTaskRunSerializer
from testcase.serializers import TestCaseRunSerializer

from browser_use import Agent
from browser_use.browser import BrowserProfile
from browser_use.browser.profile import get_display_size
from browser_use.browser.session import BrowserSession
from browser_use.utils import save_failure_screenshot

from .utils import get_llm_model

# from .video_recording_streaming import VideoRecording


class AgentManager:
	def _setup_logger(self):
		"""
		Set up a custom logger for the AgentManager class with colored logs.
		"""

		self.logger = logging.getLogger('AgentManager')
		self.logger.setLevel(logging.DEBUG)

		self.logger.propagate = False

		# Create a colored formatter
		coloredlogs.install(
			level='DEBUG',
			logger=self.logger,
			fmt='%(asctime)s [%(name)s] - [%(levelname)s] %(pathname)s:%(lineno)d - %(funcName)s: %(message)s',
			level_styles={
				'debug': {'color': 'cyan'},
				'info': {'color': 'green'},
				'warning': {'color': 'yellow'},
				'error': {'color': 'red'},
				'critical': {'color': 'red', 'bold': True},
			},
			field_styles={
				'asctime': {'color': 'white'},
				'levelname': {'color': 'white', 'bold': True},
				'pathname': {'color': 'blue'},
				'lineno': {'color': 'blue'},
				'funcName': {'color': 'blue'},
			},
			isatty=True,
			force_color=True,
		)

	def __init__(
		self,
		job_instance,
		headless=True,
		browser_type=Browser.CHROME.value,
		llm_model='gemini-2.5-flash',
		save_conversation_path='logs/conversation',
		record_video_dir='videos/',
		enable_memory=True,
		use_vision=True,
		cloud_sync=None,
		use_thinking=False,
		highlight_elements=False,
	):
		"""
		Initialize the AgentManager with default or user-provided configurations.

		Args:
			headless (bool): Whether to run the browser in headless mode.
			browser_type (str): Type of browser to use (e.g., "chrome").
			llm_model (str): The model to use for the LLM (e.g., "gpt-4o").
			save_conversation_path (str): Path to save conversation logs.
			record_video_dir (str): Directory to save recorded videos.
			enable_memory (bool): Whether to enable memory for the agent.
			use_vision (bool): Whether to enable vision for the agent.
			cloud_sync (str): Cloud sync configuration (default: None).
			use_thinking (bool): Whether to enable thinking mode for the agent.
		"""
		self._setup_logger()
		self.logger.info('Initializing AgentManager...')
		self.job_instance = job_instance
		self.headless = headless
		self.browser_type = browser_type if browser_type in Browser.choices() else Browser.CHROME.value
		self.llm = get_llm_model(llm_model)
		self.llm_model = llm_model
		self.save_conversation_path = save_conversation_path
		self.record_video_dir = record_video_dir
		self.enable_memory = enable_memory
		self.use_vision = use_vision
		self.cloud_sync = cloud_sync
		self.use_thinking = use_thinking
		self.highlight_elements = highlight_elements
		self.browser_session = None
		self.agent = None
		self.test_case_run = None
		self.testtask_run = None
		self.test_case_list = None
		self.testtask_list = None
		self.logger.info('AgentManager initialized successfully.')

	def get_chrome_args(self):
		"""
		Get Chrome arguments optimized for automation.
		"""
		return [
			'--disable-password-manager-reauthentication',
			'--disable-features=PasswordManager,AutofillServerCommunication',
			'--disable-save-password-bubble',
			'--disable-notifications',
			'--disable-infobars',
			'--disable-translate',
			'--disable-popup-blocking',
			'--disable-default-apps',
			'--disable-extensions-http-throttling',
			'--disable-geolocation',
			'--disable-media-stream',
			'--use-fake-ui-for-media-stream',
			'--use-fake-device-for-media-stream',
			'--no-first-run',
			'--no-default-browser-check',
			'--disable-backgrounding-occluded-windows',
			'--disable-renderer-backgrounding',
			'--disable-background-timer-throttling',
		]

	def configure_browser(self):
		"""
		Configure the browser profile for the session.
		"""
		self.logger.info('Configuring browser profile...')
		screen_size = get_display_size() or {'width': 1920, 'height': 1080}
		browser_profile = BrowserProfile(
			viewport=None,
			keep_alive=True,
			headless=self.headless,
			disable_security=False,
			highlight_elements=self.highlight_elements,
			record_video_dir=self.record_video_dir,
			record_video_size=screen_size,
			window_size=screen_size,
			user_data_dir=f'/app/bugowl/browser_profiles/{uuid.uuid4()}',
			args=self.get_chrome_args(),
		)
		self.browser_session = BrowserSession(browser_profile=browser_profile)
		# self.video_recording = VideoRecording(self)
		self.logger.info('Browser session configured.')

	async def save_testcase_run(self, test_case_run_data):
		"""
		Save the test case run data into the db.
		"""
		self.logger.info('Saving test case run data...')
		serializer = TestCaseRunSerializer(data=test_case_run_data)
		is_valid = await sync_to_async(serializer.is_valid)()
		if is_valid:
			self.test_case_run = await sync_to_async(serializer.save)()
			self.logger.info('Test case run data saved successfully.')
			return True
		else:
			self.logger.error(f'Failed to save test case run data: {serializer.errors}', exc_info=True)
			return False

	async def save_testtask_run(self, test_task_run_data):
		"""
		Save the test task run data into the db.
		"""
		self.logger.info('Saving test task run data...')
		serializer = TestTaskRunSerializer(data=test_task_run_data)
		is_valid = await sync_to_async(serializer.is_valid)()
		if is_valid:
			self.testtask_run = await sync_to_async(serializer.save)()  # type: ignore
			self.logger.info('Test task run data saved successfully.')
			return True
		else:
			self.logger.error(f'Failed to save test task run data: {serializer.errors}', exc_info=True)
			return False

	def process_job_payload(self):
		"""
		Process and save the test case and test task run data.
		"""
		self.logger.info('Processing job payload...')
		payload = self.job_instance.payload

		test_case_list = []

		self.logger.info('Processing test cases from payload...')
		test_cases = payload.get('test_case', [])
		for test_case in test_cases:
			test_case_data = {
				'job': self.job_instance.id,  # Link to the Job instance
				'job_uuid': self.job_instance.job_uuid,
				'test_case_uuid': test_case['uuid'],
				'name': test_case['name'],
				'priority': test_case['priority'],
				'environment': payload.get('environment'),
				'base_url': payload.get('environment', {}).get('url'),
				'status': JobStatusEnum.RUNNING.value,
				'browser': test_case['browser'] if test_case['browser'] else Browser.CHROME.value,
				'is_headless': self.headless,
				'created_by': self.job_instance.created_by,
			}
			self.logger.info(f'Processing test Tasks for test case: {test_case["name"]}...')
			test_tasks = test_case.get('test_task', [])
			test_task_list = []
			for test_task in test_tasks:
				self.logger.info(f'Processing Test Data for task: {test_task["title"]}...')
				test_data_id = test_task['test_data']
				self.logger.info(f'Test Data ID for task {test_task["title"]}: {test_data_id}')
				test_data_obj = None
				for td in payload.get('test_data') or []:
					if td.get('id') == test_data_id:
						test_data_obj = td
						break

				test_task_data = {
					'test_case_run': None,
					'test_task_uuid': test_task['uuid'],
					'title': test_task['title'],
					'status': JobStatusEnum.RUNNING.value,  # Initial status can be set to the job's status
					'test_data': test_data_obj,
				}
				test_task_list.append(test_task_data)
			test_case_data['test_task'] = test_task_list
			test_case_list.append(test_case_data)

		self.test_case_list = test_case_list
		self.logger.info('Job payload processed successfully.')

	async def start_browser_session(self):
		"""
		Start the browser session.
		"""
		if not self.browser_session:
			self.configure_browser()
		await self.browser_session.start()  # type: ignore
		self.logger.info('Browser session started.')

	async def stop_browser_session(self):
		"""
		Stop the browser session.
		"""
		if self.browser_session:
			await self.browser_session.kill()
			self.logger.info('Browser session stopped.')

	async def update_testtask_run(self, status):
		"""
		Update the test task run status.
		"""
		if self.testtask_run:
			self.testtask_run.status = (
				status if self.testtask_run.status == JobStatusEnum.RUNNING.value else self.testtask_run.status
			)
			await sync_to_async(self.testtask_run.save)(update_fields=['status'])

	async def update_testcase_run(self, status, video_url):
		"""
		Update the test case run status.
		"""
		if self.test_case_run:
			self.test_case_run.status = (
				status if self.test_case_run.status == JobStatusEnum.RUNNING.value else self.test_case_run.status
			)
			if video_url:
				self.test_case_run.video = video_url
			await sync_to_async(self.test_case_run.save)(update_fields=['status', 'video'])

	async def run_test_case(self):
		"""
		Run a test case.
		"""
		if not self.test_case_list or len(self.test_case_list) == 0:
			self.logger.error('No test cases to run. Please process the job payload first.')
			return

		self.logger.info('Running test cases...')

		try:
			# if not self.browser_session:
			# 	await self.start_browser_session()
			# self.logger.info('Browser session is ready. Starting test case execution...')
			run_results = {}
			for test_case in self.test_case_list:
				self.logger.info(f'testcase name: {test_case["name"]}')
				test_tasks = test_case.pop('test_task')
				result = await self.save_testcase_run(test_case)
				if result:
					if not self.browser_session:
						await self.start_browser_session()
						self.logger.info('New Browser session is ready for next testcase. Starting test case execution...')
					else:
						await self.stop_browser_session()
						self.logger.info('Browser session stopped. Starting new browser session for next testcase...')
						await self.start_browser_session()
						self.logger.info('New Browser session is ready for next testcase. Starting test case execution...')
					self.logger.info(f'Test case {test_case["name"]} saved successfully.')
					run_results[self.test_case_run.name] = []  # type: ignore
					# await self.video_recording.start()
					for count, test_task in enumerate(test_tasks, start=1):
						self.logger.info(f'Test task title: {test_task["title"]}')
						test_task['test_case_run'] = self.test_case_run.id if self.test_case_run else None
						result = await self.save_testtask_run(test_task)

						if result:
							title = self.testtask_run.title  # type: ignore
							self.logger.info(f'Test task {title} saved successfully.')
							self.logger.info(f'Executing Task #{count}: {title}')
							sensitive_data = (
								{self.testtask_run.test_data.get('name'): self.testtask_run.test_data.get('data')}  # type: ignore
								if self.testtask_run.test_data  # type: ignore
								else {}
							)

							history, output = await self.run_task(title, sensitive_data=sensitive_data)
							if not history.is_successful():
								# Handle failure (e.g., take a screenshot)
								await self.update_testtask_run(status=JobStatusEnum.FAILED.value)
								await save_failure_screenshot(self.browser_session, str(self.test_case_run.test_case_uuid))  # type: ignore
							else:
								await self.update_testtask_run(status=JobStatusEnum.PASS_.value)

							self.logger.info(f'Task #{count} Result: {output}')
							run_results[self.test_case_run.name].append({'task': title, 'result': output})  # type: ignore

						else:
							self.logger.error(f'Failed to save test task {test_task["title"]}.', exc_info=True)
							return

							# After all test tasks for this test case are executed, check their results
					await self.stop_browser_session()
					video_url = await self.upload_video_S3()
					task_results = run_results[self.test_case_run.name]  # type: ignore
					all_success = all(task_result['result'] == '✅ SUCCESSFUL' for task_result in task_results)
					final_status = JobStatusEnum.PASS_.value if all_success else JobStatusEnum.FAILED.value
					# video_url = await self.video_recording.stop()
					# self.logger.info(f'Video URL: {video_url}')
					await self.update_testcase_run(status=final_status, video_url=video_url)

				else:
					self.logger.error(f'Failed to save test case {test_case["name"]}.', exc_info=True)
					return
			return run_results
		except Exception as e:
			self.logger.error(f'Error running test cases: {e}', exc_info=True)
			raise
		finally:
			if self.browser_session:
				await self.stop_browser_session()

	async def run_task(self, task, sensitive_data={}):
		"""
		Run a single task using the Agent.
		"""
		if not self.agent:
			self.logger.info(f'Sensitvie data: {sensitive_data}')
			test_case_uuid = str(self.test_case_run.test_case_uuid)  # type: ignore
			self.agent = Agent(
				task=self.testtask_run.title,  # type: ignore
				task_id=test_case_uuid,
				llm=self.llm,
				browser_session=self.browser_session,
				enable_memory=self.enable_memory,
				save_conversation_path=self.save_conversation_path,
				use_vision=self.use_vision,
				sensitive_data=sensitive_data,
				cloud_sync=self.cloud_sync,
				use_thinking=self.use_thinking,
				file_system_path=f'/app/bugowl/browser_data/browser_user_agent{test_case_uuid}-{str(uuid.uuid4())}/',
			)
		else:
			if len(sensitive_data) > 0:
				self.agent.sensitive_data.update(sensitive_data)  # type: ignore
			self.logger.info(f'Updated sensitive data: {self.agent.sensitive_data}')  # type: ignore
			self.agent.add_new_task(task)

		history = await self.agent.run()
		output = '✅ SUCCESSFUL' if history.is_successful() else '❌ FAILED!'

		return history, output

	def run_job(self):
		"""
		Run the entire job.
		"""
		self.logger.info('Running job...')
		try:
			self.process_job_payload()
			run_results = asyncio.run(self.run_test_case())
			self.logger.info('Job completed.')
			return run_results
		except Exception as e:
			self.logger.error(f'Error running job: {e}', exc_info=True)
			raise

	async def upload_video_S3(self):
		"""
		Upload the Playwright video recording for the current test case to S3.
		This should be called after the browser session is stopped.
		"""
		try:
			if not self.browser_session:
				self.logger.error('No browser session to upload video from.')
				return None
			page = await self.browser_session.get_current_page()
			if not page:
				self.logger.error('No page to upload video from.')
				return None
			video_path = await page.video.path()  # type: ignore
			if not video_path or not os.path.exists(video_path):
				self.logger.error(f'No video file found at {video_path}')
				return None

			# Generate new filename
			new_filename = self.get_video_filename()
			new_video_dir = os.path.join('videos', 'browser_recordings')
			os.makedirs(new_video_dir, exist_ok=True)
			new_video_path = os.path.join(new_video_dir, new_filename)

			# Rename/move the video file
			os.rename(video_path, new_video_path)
			self.logger.info(f'Renamed video from {video_path} to {new_video_path}')

			# Upload to S3
			# Use the same logic as in VideoRecording.upload_to_s3

			s3_bucket = os.getenv('AWS_STORAGE_BUCKET_NAME')
			aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
			aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
			region_name = os.getenv('AWS_S3_REGION_NAME')
			s3_custom_domain = os.getenv('AWS_S3_CUSTOM_DOMAIN')
			obj_params = os.getenv('AWS_S3_OBJECT_PARAMETERS')
			s3_object_parameters = json.loads(obj_params) if obj_params else None

			session = boto3.session.Session(  # type: ignore
				aws_access_key_id=aws_access_key_id,
				aws_secret_access_key=aws_secret_access_key,
				region_name=region_name,
			)
			s3 = session.client('s3')
			s3_key = f'videos/browser_recordings/{new_filename}'
			extra_args = {}
			if s3_object_parameters:
				extra_args.update(s3_object_parameters)
			try:
				s3.upload_file(new_video_path, s3_bucket, s3_key, ExtraArgs=extra_args)
				self.logger.info(f'Upload to S3 successful: {s3_key}')
			except Exception as e:
				self.logger.error(f'Failed to upload video to S3: {e}')
				return None
			if s3_custom_domain:
				url = f'https://{s3_custom_domain}/{s3_key}'
			else:
				url = f'https://{s3_bucket}.s3.amazonaws.com/{s3_key}'
			self.logger.info(f'S3 video URL: {url}')
			return url
		except Exception as e:
			self.logger.error(f'Error in upload_video_S3: {e}', exc_info=True)
			return None

	def get_video_filename(self, ext='mp4'):
		timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
		uid = str(uuid.uuid4())
		job_uuid = self.job_instance.job_uuid
		testcase_uuid = self.test_case_run.test_case_uuid  # type: ignore
		filename = f'{job_uuid}-{testcase_uuid}-{uid}_{timestamp}.{ext}'
		self.logger.debug(f'Generated video filename: {filename}')
		return filename
