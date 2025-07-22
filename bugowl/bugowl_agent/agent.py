import asyncio
import logging
import os
import uuid

import coloredlogs
from api.utils import Browser, JobStatusEnum
from asgiref.sync import sync_to_async
from django.core.cache import cache
from job.helpers import get_cancel_job_status_cache
from job.utils import get_cancel_cache_key
from testask.serializers import TestTaskRunSerializer
from testcase.serializers import TestCaseRunSerializer
from websocket.utils import get_job_streaming_group_name

from browser_use import Agent
from browser_use.browser import BrowserProfile
from browser_use.browser.profile import get_display_size
from browser_use.browser.session import BrowserSession

from .exceptions import JobCancelledException
from .tasks import update_status_main
from .utils import CHROME_ARGS, get_llm_model, save_failure_screenshot, upload_video_S3
from .video_recording_streaming import LiveStreaming  # Import LiveStreaming


class PlayGroundTask:
	"""
	A simple task class to encapsulate task-related data.
	"""

	def __init__(self, uuid, title, data={}):
		self.uuid = uuid
		self.title = title
		self.test_data = data

	def __str__(self):
		return f'Task(uuid={self.uuid}, title={self.title})'


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
		job_instance=None,
		headless=True,
		browser_type=Browser.CHROME.value,
		llm_model=None,
		save_conversation_path='logs/conversation',
		record_video_dir='videos/',
		enable_memory=True,
		use_vision=True,
		cloud_sync=None,
		use_thinking=False,
		highlight_elements=False,
		channel_name=None,
	):
		"""
		Initialize the AgentManager with default or user-provided configurations.

		Args:
			headless (bool): Whether to run the browser in headless mode.
			browser_type (str): Type of browser to use (e.g., "chrome").
			llm_model (str, optional): The model to use for the LLM (e.g., "gpt-4o").
				If None, reads from LLM_MODEL environment variable or defaults to 'gemini-2.5-flash'.
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

		# Configure LLM model from environment variable or use provided/default value
		if llm_model is None:
			llm_model = os.getenv('LLM_MODEL', 'gemini-2.5-flash')
		self.logger.info('Using LLM model: %s', llm_model)

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
		self.page = None
		self.live_streaming = None
		self.channel_name = channel_name
		self.group_name = None

		self.task_id = None

		self.logger.info('AgentManager initialized successfully.')

	def get_chrome_args(self):
		"""
		Get Chrome arguments optimized for automation.
		"""
		return CHROME_ARGS

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
		self.logger.info('Browser session configured.')

	async def save_testcase_run(self, test_case_run_data):
		"""
		Save the test case run data into the db.
		"""
		self.check_job_cancelled('save_testcase_run')
		self.logger.info('Saving test case run data...')
		serializer = TestCaseRunSerializer(data=test_case_run_data)
		is_valid = await sync_to_async(serializer.is_valid)()
		if is_valid:
			self.test_case_run = await sync_to_async(serializer.save)()
			self.logger.info('Test case run data saved successfully.')
			self.logger.info('Updating test case run status to RUNNING in the main server...')
			update_status_main.delay(  # type: ignore
				job_uuid=str(self.job_instance.job_uuid),  # type: ignore
				test_case_uuid=str(self.test_case_run.test_case_uuid),  # type: ignore
				test_case_status=self.test_case_run.status,
			)
			return True
		else:
			self.logger.error(f'Failed to save test case run data: {serializer.errors}', exc_info=True)
			return False

	async def save_testtask_run(self, test_task_run_data):
		"""
		Save the test task run data into the db.
		"""
		self.check_job_cancelled('save_testtask_run')
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
		self.check_job_cancelled('process_job_payload')

		self.logger.info('Processing job payload...')
		payload = self.job_instance.payload  # type: ignore

		test_case_list = []

		self.logger.info('Processing test cases from payload...')
		test_cases = payload.get('test_case', [])
		for test_case in test_cases:
			test_case_data = {
				'job': self.job_instance.id,  # type:ignore # Link to the Job instance
				'job_uuid': self.job_instance.job_uuid,  # type: ignore
				'test_case_uuid': test_case['uuid'],
				'name': test_case['name'],
				'priority': test_case['priority'],
				'environment': payload.get('environment'),
				'base_url': payload.get('environment', {}).get('url'),
				'status': JobStatusEnum.RUNNING.value,
				'browser': test_case['browser'] if test_case['browser'] else Browser.CHROME.value,
				'is_headless': self.headless,
				'created_by': self.job_instance.created_by,  # type: ignore
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

	def check_job_cancelled(self, exception_message):
		"""
		Check if the job is cancelled based on the cache status.
		Raise JobCancelledException if the job is cancelled.
		"""
		if not self.job_instance:
			self.logger.warning('Job instance is not set. Cannot check job cancellation status.')
			return
		job_status_cache = get_cancel_job_status_cache(self.job_instance.job_uuid)
		if job_status_cache and job_status_cache == JobStatusEnum.CANCELED.value:
			self.logger.info(f'Job {self.job_instance.job_uuid} is cancelled. {exception_message}')

			raise JobCancelledException(f'{exception_message}')

	async def start_browser_session(self):
		"""
		Start the browser session and initialize LiveStreaming.
		"""
		self.check_job_cancelled('start_browser_session')
		if not self.browser_session:
			self.configure_browser()
		await self.browser_session.start()  # type: ignore
		self.logger.info('Browser session started.')

		# Initialize and start LiveStreaming
		if not self.channel_name:
			self.group_name = get_job_streaming_group_name(self.job_instance.job_uuid)  # type: ignore

		self.live_streaming = LiveStreaming(
			agent_manager=self, channel_name=self.channel_name, group_name=self.group_name, fps=12
		)
		await self.live_streaming.start()
		self.logger.info('Live streaming started.')

		if self.browser_session:
			if self.browser_session.browser_context and self.browser_session.browser_context.pages[0]:
				self.browser_session.logger.info('BUGOWL:LOADING DVD ANIMATION')
				await self.browser_session._show_dvd_screensaver_loading_animation(self.browser_session.browser_context.pages[0])
			else:
				self.browser_session.logger.info('BUGOWL:FAILED to load DVD ANIMATION')

	async def stop_browser_session(self):
		"""
		Stop the browser session and LiveStreaming.
		"""

		# Stop LiveStreaming
		if hasattr(self, 'live_streaming') and (self.live_streaming.recording if self.live_streaming else False):  # type: ignore
			await self.live_streaming.stop()  # type: ignore
			self.live_streaming = None
			self.logger.info('Live streaming stopped.')

		if self.browser_session:
			await self.browser_session.kill()
			self.browser_session = None
			self.logger.info('Browser session stopped.')

		self.check_job_cancelled('stop_browser_session')

	async def update_testtask_run(self, status):
		"""
		Update the test task run status.
		"""

		if self.testtask_run:
			update_fields = ['status', 'updated_at']
			self.testtask_run.status = status
			await sync_to_async(self.testtask_run.save)(update_fields=update_fields)

	async def update_testcase_run(self, status, video_url=None, image_url=None):
		"""
		Update the test case run status.
		"""
		if self.test_case_run:
			update_fields = ['status', 'updated_at']
			self.test_case_run.status = status
			if video_url:
				self.test_case_run.video = video_url
				update_fields.append('video')
			if image_url:
				self.test_case_run.failure_screenshot = image_url
				update_fields.append('failure_screenshot')
			await sync_to_async(self.test_case_run.save)(update_fields=update_fields)
			self.logger.info(f'Updating test case status to {status} in the main server...')
			update_status_main.delay(  # type: ignore
				job_uuid=str(self.job_instance.job_uuid),  # type: ignore
				test_case_uuid=str(self.test_case_run.test_case_uuid),  # type: ignore
				test_case_status=status,
			)

	async def update_job_instance(self, status):
		"""
		Update the job instance status.
		"""
		if self.job_instance:
			self.check_job_cancelled('update_job_instance')

			self.job_instance.status = status
			await sync_to_async(self.job_instance.save)(update_fields=['status', 'updated_at'])
			self.logger.info(f'Updating job status to {status} in the main server...')
			update_status_main.delay(  # type: ignore
				job_uuid=str(self.job_instance.job_uuid), job_status=status
			)

	async def run_test_case(self):
		"""
		Run a test case.
		"""
		if not self.test_case_list or len(self.test_case_list) == 0:
			self.logger.error('No test cases to run. Please process the job payload first.')
			return

		self.logger.info('Running test cases...')

		self.check_job_cancelled('run_test_case')

		self.logger.info('updating job status to RUNNING')
		await self.update_job_instance(status=JobStatusEnum.RUNNING.value)
		run_results_case = {}
		try:
			for test_case in self.test_case_list:
				self.logger.info(f'testcase name: {test_case["name"]}')
				test_tasks = test_case.pop('test_task')
				result = await self.save_testcase_run(test_case)
				run_results_task = {}

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
					image_url = None
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
							self.check_job_cancelled('run_test_case_taskLoop')
							self.task_id = str(self.test_case_run.test_case_uuid)  # type:ignore
							history, output = await self.run_task(title, sensitive_data=sensitive_data)
							self.logger.info(f'Task #{count} Result: {output}')
							run_results_task[str(self.testtask_run.uuid)] = output  # type: ignore

							if not history.is_successful():
								# Handle failure (e.g., take a screenshot)
								image_url = await save_failure_screenshot(
									self.browser_session,
									self.logger,
									str(self.job_instance.job_uuid),  # type: ignore
									str(self.test_case_run.test_case_uuid),  # type: ignore
								)
								await self.update_testtask_run(status=JobStatusEnum.FAILED.value)
								break
							else:
								image_url = None
								await self.update_testtask_run(status=JobStatusEnum.PASS_.value)
						else:
							self.logger.error(f'Failed to save test task {test_task["title"]}.', exc_info=True)
							await self.update_job_instance(status=JobStatusEnum.FAILED.value)
							return

					# After all test tasks for this test case are executed, check their results
					self.page = await self.browser_session.get_current_page()  # type: ignore
					video_url = await self.page.video.path() if self.page else None  # type: ignore
					self.logger.info(f'Video URL: {video_url}')
					await self.stop_browser_session()
					video_url = await upload_video_S3(
						self.job_instance,
						self.test_case_run,
						video_url,
						self.logger,
					)
					task_results = run_results_task  # type: ignore
					all_success = all(result == '✅ SUCCESSFUL' for result in task_results.values())
					final_status = JobStatusEnum.PASS_.value if all_success else JobStatusEnum.FAILED.value
					run_results_case[str(self.test_case_run.uuid)] = all_success  # type: ignore

					await self.update_testcase_run(status=final_status, video_url=video_url, image_url=image_url)
				else:
					self.logger.error(f'Failed to save test case {test_case["name"]}.', exc_info=True)
					await self.update_job_instance(status=JobStatusEnum.FAILED.value)
					return
			self.logger.info('All test cases executed successfully.')
		except JobCancelledException as e:
			self.logger.info(f'Job cancelled from {e}')
			raise JobCancelledException('run_test_case')
		except Exception as e:
			self.logger.error(f'Error running test cases: {e}', exc_info=True)
			await self.update_job_instance(status=JobStatusEnum.FAILED.value)
			raise
		finally:
			if self.browser_session:
				await self.stop_browser_session()
			return run_results_case

	async def run_task(self, task, sensitive_data={}):
		"""
		Run a single task using the Agent.
		"""
		if not self.agent:
			self.logger.info(f'Sensitive data: {sensitive_data}')
			self.check_job_cancelled('run_task')
			self.agent = Agent(
				task=task,  # type: ignore
				task_id=self.task_id,
				llm=self.llm,
				browser_session=self.browser_session,
				enable_memory=self.enable_memory,
				save_conversation_path=self.save_conversation_path,
				use_vision=self.use_vision,
				sensitive_data=sensitive_data,
				cloud_sync=self.cloud_sync,
				use_thinking=self.use_thinking,
				file_system_path=f'/app/bugowl/browser_data/browser_user_agent{self.task_id}-{str(uuid.uuid4())}/',
			)
		else:
			if len(sensitive_data) > 0:
				self.agent.sensitive_data.update(sensitive_data)  # type: ignore
			self.logger.info(f'Updated sensitive data: {self.agent.sensitive_data}')  # type: ignore
			self.check_job_cancelled('run_task')
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
			if self.job_instance is None:
				self.logger.error('Job instance is not set. Cannot run job.')
				return
			self.process_job_payload()

			run_results = asyncio.run(self.run_test_case())
			self.logger.info('Job completed.')
			self.logger.info(f'Run results: {run_results}')
			all_testcases_passed = all(run_results.values())  # type: ignore
			final_job_status = JobStatusEnum.PASS_.value if all_testcases_passed else JobStatusEnum.FAILED.value
			asyncio.run(self.update_job_instance(status=final_job_status))
			return run_results
		except JobCancelledException as e:
			key = get_cancel_cache_key(self.job_instance.job_uuid)  # type: ignore
			cache.delete(key)
			self.logger.info(f'Cache key {key} deleted successfully.')
			self.logger.info(f'Job cancelled from {e}')
			self.logger.info('Job Cancelled from run_job')
			if self.test_case_run:
				if self.test_case_run.status not in [JobStatusEnum.PASS_.value, JobStatusEnum.FAILED.value]:
					self.logger.info(f'Updating test case {self.test_case_run.test_case_uuid} status to CANCELED')
					self.test_case_run.status = JobStatusEnum.CANCELED.value
					self.test_case_run.save(update_fields=['status', 'updated_at'])
			if self.testtask_run:
				if self.testtask_run.status not in [JobStatusEnum.PASS_.value, JobStatusEnum.FAILED.value]:
					self.logger.info(f'Updating test task {self.testtask_run.testtask_uuid} status to CANCELED')
					self.testtask_run.status = JobStatusEnum.CANCELED.value
					self.testtask_run.save(update_fields=['status', 'updated_at'])
			asyncio.run(self.stop_browser_session())
			raise JobCancelledException('run_job')
		except Exception as e:
			self.logger.error(f'Error running job: {e}', exc_info=True)
			raise


# AgentManager for Playground Tasks


class PlayGroundAgentManager(AgentManager):
	"""
	AgentManager for managing tasks in the playground.
	"""

	def __init__(self, task_id, channel_name, **kwargs):
		"""
		Initialize the PlaygroundAgentManager with default or user-provided configurations.
		"""
		super().__init__(channel_name=channel_name, **kwargs)
		self.task_id = task_id
		self.playground_task_list = []
		self.channel_name = channel_name
		self.logger.info('PlaygroundAgentManager initialized successfully.')

	async def run_all_tasks(self):
		"""
		Run all tasks in the playground.
		"""
		if not self.browser_session:
			await self.start_browser_session()
			self.logger.info('New Browser session is ready for task execution...')
		else:
			await self.stop_browser_session()
			self.logger.info('Browser session stopped. Starting new browser session for task execution...')
			await self.start_browser_session()
			self.logger.info('New Browser session is ready for task execution...')

		if not (self.playground_task_list or self.task_id):
			self.logger.warning('No tasks found in the playground.')
			return

		run_results = {}
		try:
			for task in self.playground_task_list:
				self.logger.info(f'Executing Task: {task}')
				history, output = await self.run_task(task.title, sensitive_data=task.test_data)
				self.logger.info(f'Task Result: {output}')
				run_results[task] = output

				if not history.is_successful():
					self.logger.error(f'Task {task} failed.')
					return run_results, f'{task} - FAILED'

			self.logger.info('All tasks executed successfully.')
			return run_results, 'All tasks - SUCCESSFUL'

		except Exception as e:
			self.logger.error(f'Error running tasks: {e}', exc_info=True)
			raise

	async def load_tasks(self, tasks_data):
		"""
		Load tasks with the given data.
		"""
		tasks = []
		for task_info in tasks_data:
			task = PlayGroundTask(
				uuid=task_info.get('uuid'),
				title=task_info.get('title'),
				# data=task_info.get('data'),
			)
			tasks.append(task)
		self.playground_task_list = tasks
		self.logger.info('Tasks loaded')

	async def get_task(self, uuid):
		"""
		Get a task by its UUID.
		"""
		if not self.playground_task_list:
			self.logger.error('No tasks loaded in the playground.')
			return None
		for task in self.playground_task_list:
			if task.uuid == uuid:
				return task
		self.logger.error(f'Task with UUID {uuid} not found.')
		return None


# class PlayGroundAgent:
# 	def _setup_logger(self):
# 		"""
# 		Set up a custom logger for the AgentManager class with colored logs.
# 		"""

# 		self.logger = logging.getLogger('PlayGroundAgent')
# 		self.logger.setLevel(logging.DEBUG)

# 		self.logger.propagate = False

# 		# Create a colored formatter
# 		coloredlogs.install(
# 			level='DEBUG',
# 			logger=self.logger,
# 			fmt='%(asctime)s [%(name)s] - [%(levelname)s] %(pathname)s:%(lineno)d - %(funcName)s: %(message)s',
# 			level_styles={
# 				'debug': {'color': 'cyan'},
# 				'info': {'color': 'green'},
# 				'warning': {'color': 'yellow'},
# 				'error': {'color': 'red'},
# 				'critical': {'color': 'red', 'bold': True},
# 			},
# 			field_styles={
# 				'asctime': {'color': 'white'},
# 				'levelname': {'color': 'white', 'bold': True},
# 				'pathname': {'color': 'blue'},
# 				'lineno': {'color': 'blue'},
# 				'funcName': {'color': 'blue'},
# 			},
# 			isatty=True,
# 			force_color=True,
# 		)

# 	def __init__(
# 		self,
# 		task_id,
# 		llm_model=None,
# 		enable_memory=True,
# 		save_conversation_path='logs/playground/conversation',
# 		use_vision=True,
# 		cloud_sync=None,
# 		use_thinking=False,
# 		highlight_elements=False,
# 		headless=True,
# 	):
# 		"""
# 		Initialize the PlayGroundAgent with default or user-provided configurations.
# 		"""

# 		self._setup_logger()
# 		self.logger.info('Initializing PlayGroundAgent...')

# 		if llm_model is None:
# 			llm_model = os.getenv('LLM_MODEL', 'gemini-2.5-flash')
# 		self.logger.info('Using LLM model: %s', llm_model)

# 		self.llm_model = llm_model
# 		self.llm = get_llm_model(llm_model)
# 		self.save_conversation_path = save_conversation_path
# 		self.headless = headless
# 		self.highlight_elements = highlight_elements
# 		self.browser_session = None
# 		self.agent = None
# 		self.task_id = task_id
# 		self.enable_memory = enable_memory
# 		self.save_conversation_path = save_conversation_path
# 		self.use_vision = use_vision
# 		self.sensitive_data = None
# 		self.cloud_sync = cloud_sync
# 		self.use_thinking = use_thinking
# 		self.task_lists = []

# 	def get_chrome_args(self):
# 		"""
# 		Get Chrome arguments optimized for automation.
# 		"""
# 		return CHROME_ARGS

# 	def configure_browser(self):
# 		"""
# 		Configure the browser profile for the session.
# 		"""
# 		self.logger.info('Configuring browser profile...')
# 		screen_size = get_display_size() or {'width': 1920, 'height': 1080}
# 		browser_profile = BrowserProfile(
# 			viewport=None,
# 			keep_alive=True,
# 			headless=self.headless,
# 			disable_security=False,
# 			highlight_elements=self.highlight_elements,
# 			window_size=screen_size,
# 			user_data_dir=f'/app/bugowl/browser_profiles/{uuid.uuid4()}',
# 			args=self.get_chrome_args(),
# 		)
# 		self.browser_session = BrowserSession(browser_profile=browser_profile)
# 		self.logger.info('Browser session configured.')

# 	async def start_browser_session(self):
# 		"""
# 		Start the browser session.
# 		"""
# 		if not self.browser_session:
# 			self.configure_browser()
# 		await self.browser_session.start()  # type: ignore

# 		self.logger.info('Browser session started.')

# 		if self.browser_session:
# 			if self.browser_session.browser_context and self.browser_session.browser_context.pages[0]:
# 				self.browser_session.logger.info('BUGOWL:LOADING DVD ANIMATION')
# 				await self.browser_session._show_dvd_screensaver_loading_animation(self.browser_session.browser_context.pages[0])
# 			else:
# 				self.browser_session.logger.info('BUGOWL:FAILED to load DVD ANIMATION')

# 	async def stop_browser_session(self):
# 		"""
# 		Stop the browser session.
# 		"""
# 		if self.browser_session:
# 			await self.browser_session.kill()
# 			self.browser_session = None
# 			self.logger.info('Browser session stopped.')

# 	async def run_task(self, task, sensitive_data={}):
# 		"""
# 		Run a single task using the Agent.
# 		"""
# 		if not self.agent:
# 			self.logger.info(f'Sensitive data: {sensitive_data}')
# 			self.agent = Agent(
# 				task=task,
# 				task_id=self.task_id,
# 				llm=self.llm,
# 				browser_session=self.browser_session,
# 				enable_memory=self.enable_memory,
# 				save_conversation_path=self.save_conversation_path,
# 				use_vision=self.use_vision,
# 				sensitive_data=sensitive_data,
# 				cloud_sync=self.cloud_sync,
# 				use_thinking=self.use_thinking,
# 				file_system_path=f'/app/bugowl/browser_data/playground/browser_user_agent{self.task_id}-{str(uuid.uuid4())}/',
# 			)
# 		else:
# 			if len(sensitive_data) > 0:
# 				self.agent.sensitive_data.update(sensitive_data)  # type: ignore
# 			self.logger.info(f'Updated sensitive data: {self.agent.sensitive_data}')  # type: ignore
# 			self.agent.add_new_task(task)

# 		history = await self.agent.run()
# 		output = '✅ SUCCESSFUL' if history.is_successful() else '❌ FAILED!'

# 		return history, output

# 	async def run_all_tasks(self):
# 		"""
# 		Run all tasks in the playground.
# 		"""
# 		if not self.browser_session:
# 			await self.start_browser_session()
# 			self.logger.info('New Browser session is ready for task execution...')
# 		else:
# 			await self.stop_browser_session()
# 			self.logger.info('Browser session stopped. Starting new browser session for task execution...')
# 			await self.start_browser_session()
# 			self.logger.info('New Browser session is ready for task execution...')

# 		run_results = {}
# 		try:
# 			for task in self.task_lists:
# 				self.logger.info(f'Executing Task: {task}')
# 				history, output = await self.run_task(task.title, sensitive_data=task.test_data)
# 				self.logger.info(f'Task Result: {output}')
# 				run_results[task] = output

# 				if not history.is_successful():
# 					self.logger.error(f'Task {task} failed.')
# 					return run_results, f'{task} - FAILED'

# 			self.logger.info('All tasks executed successfully.')
# 			return run_results, 'All tasks - SUCCESSFUL'

# 		except Exception as e:
# 			self.logger.error(f'Error running tasks: {e}', exc_info=True)
# 			raise

# 	async def load_tasks(self, tasks_data):
# 		"""
# 		Load tasks with the given data.
# 		"""
# 		tasks = []
# 		for task_info in tasks_data:
# 			task = PlayGroundTask(
# 				uuid=task_info.get('uuid'),
# 				title=task_info.get('title'),
# 				data=task_info.get('data'),
# 			)
# 			tasks.append(task)
# 		self.task_lists = tasks
# 		self.logger.info('Tasks loaded')
