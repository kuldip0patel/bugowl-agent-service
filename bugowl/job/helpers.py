import logging

from api.utils import Browser
from django.conf import settings
from rest_framework.exceptions import ValidationError
from testask.serializers import TestTaskRunSerializer
from testcase.serializers import TestCaseRunSerializer

from .models import Job
from .utils import JobTypeEnum

logger = logging.getLogger(settings.ENV)


def validate_job_payload(data):
	def validate_job(job):
		if not job:
			raise ValidationError("Missing 'job' field.")
		required_fields = [
			'id',
			'uuid',
			'status',
			'job_type',
			'created_at',
			'updated_at',
			'test_case',
			'test_suite',
			'experimental',
			'Business',
			'Project',
			'created_by',
		]
		for field in required_fields:
			if field not in job:
				raise ValidationError(f"Missing '{field}' in job.")
		if not isinstance(job['created_by'], dict):
			raise ValidationError("'created_by' in job must be a dictionary.")
		for field in ['id', 'full_name', 'email']:
			if field not in job['created_by']:
				raise ValidationError(f"Missing '{field}' in job['created_by'].")

	def validate_case_suite(case, suite):
		if not (suite or case):
			raise ValidationError("Missing 'test_suite' and 'test_case' field.")
		if case:
			if not isinstance(case, list):
				raise ValidationError("'test_case' must be a list.")
			for test_case in case:
				required_fields = ['id', 'uuid', 'test_suite', 'name', 'priority', 'browser', 'is_draft', 'test_task']
				for field in required_fields:
					if field not in test_case:
						raise ValidationError(f"Missing '{field}' in test_case.")
				if not isinstance(test_case['test_task'], list):
					raise ValidationError("'test_task' in test_case must be a list.")
				for idx, task in enumerate(test_case['test_task']):
					required_fields = ['id', 'uuid', 'title', 'created_at', 'updated_at', 'created_by', 'test_data']
					for field in required_fields:
						if field not in task:
							raise ValidationError(f"Missing '{field}' in test_task at index {idx}.")
					if not isinstance(task['created_by'], int):
						raise ValidationError(f"'created_by' in test_task at index {idx} must be an integer (user id).")
					if task['test_data'] is not None and not isinstance(task['test_data'], int):
						raise ValidationError(f"'test_data' in test_task at index {idx} must be an integer or null.")
		if suite:
			if not isinstance(suite, dict):
				raise ValidationError("'test_suite' must be a dictionary.")
			required_fields = ['id', 'name', 'description', 'language', 'priority', 'type']
			for field in required_fields:
				if field not in suite:
					raise ValidationError(f"Missing '{field}' in test_suite.")

	def validate_environment(environment):
		if not isinstance(environment, dict):
			raise ValidationError("'environment' must be a dictionary.")
		required_fields = ['id', 'name', 'description', 'url']
		for field in required_fields:
			if field not in environment:
				raise ValidationError(f"Missing '{field}' in environment.")

	def validate_test_data(test_data):
		if not test_data:
			return
		if not isinstance(test_data, dict):
			raise ValidationError("'test_data' must be a dictionary mapping test data names to data values.")
		for test_data_name, data_value in test_data.items():
			if not isinstance(test_data_name, str):
				raise ValidationError('Test data name must be a string.')
			if not isinstance(data_value, dict):
				raise ValidationError(f"Value for '{test_data_name}' must be a dictionary (key-value pairs).")

	validate_job(data.get('job'))
	validate_case_suite(data.get('test_case'), data.get('test_suite'))
	validate_environment(data.get('environment'))
	validate_test_data(data.get('test_data'))


def save_case_task_runs(job_instance):
	# Extract payload from the job instance
	payload = job_instance.payload

	# Extract test cases from the payload
	test_cases = payload.get('test_case', [])
	test_case_run_instance_list = []
	for test_case in test_cases:
		# Prepare data for TestCaseRun
		test_case_data = {
			'job': job_instance.id,  # Link to the Job instance
			'job_uuid': job_instance.job_uuid,
			'test_case_uuid': test_case['uuid'],
			'name': test_case['name'],
			'priority': test_case['priority'],
			'environment': payload.get('environment'),
			'base_url': payload.get('environment', {}).get('url'),
			'status': job_instance.status,
			'browser': test_case['browser'] if test_case['browser'] else Browser.CHROME.value,
			'is_headless': False,  # Default value, can be updated as needed
			'created_by': job_instance.created_by,
		}

		test_case_serializer = TestCaseRunSerializer(data=test_case_data)
		if test_case_serializer.is_valid():
			test_case_run_instance = test_case_serializer.save()
			test_case_run_instance_list.append(test_case_run_instance.id)
			test_tasks = test_case.get('test_task', [])
			for test_task in test_tasks:
				test_data_id = test_task['test_data']

				if test_data_id is not None and not isinstance(test_data_id, int):
					raise ValueError(f"'test_data' in test_task must be an integer or null, got {test_data_id}")

				test_data_obj = None
				logger.debug(f'Fetching test data {payload.get("test_data") or []}')
				for td in payload.get('test_data') or []:
					if td.get('id') == test_data_id:
						test_data_obj = td
						break

				test_task_data = {
					'test_case_run': test_case_run_instance.id,
					'test_task_uuid': test_task['uuid'],
					'title': test_task['title'],
					'status': job_instance.status,  # Initial status can be set to the job's status
					'test_data': test_data_obj,
				}

				test_task_serializer = TestTaskRunSerializer(data=test_task_data)
				if test_task_serializer.is_valid():
					test_task_serializer.save()
				else:
					raise ValueError(f'Invalid TestTaskRun data: {test_task_serializer.errors}')
		else:
			raise ValueError(f'Invalid TestCaseRun data: {test_case_serializer.errors}')

	return test_case_run_instance_list


def get_job_details(job_uuid):
	"""
	Fetch job details, test case runs, test task runs, and test step runs based on job_uuid.

	Args:
	    job_uuid (str): The UUID of the job.

	Returns:
	    dict: A dictionary containing job details and related test case, task, and step runs.
	"""

	# Fetch the Job instance
	job = Job.objects.get(job_uuid=job_uuid)

	# Fetch all TestCaseRuns under the Job
	test_case_runs = job.testcaserun_set.all()  # type: ignore

	# Prepare the response structure
	response_data = {
		'job': {
			'uuid': job.job_uuid,
			'test_case_uuid': job.test_case_uuid,
			'test_suite_uuid': job.test_suite_uuid,
			'environment': job.environment,
			'job_type': job.job_type,
			'status': job.status,
			'created_by': job.created_by,
			'created_at': job.created_at,
			'updated_at': job.updated_at,
		},
		'test_case_runs': [],
	}

	if job.job_type == JobTypeEnum.TEST_CASE:
		for test_case_run in test_case_runs:
			# Fetch all TestTaskRuns under the TestCaseRun
			test_task_runs = test_case_run.testtaskrun_set.all()  # type: ignore[attr-defined]

			test_task_data = []
			for test_task_run in test_task_runs:
				# Fetch all TestStepRuns under the TestTaskRun
				test_step_runs = test_task_run.teststeprun_set.all()  # type: ignore[attr-defined]

				test_step_data = [
					{
						'test_case_run': test_case_run.id,
						'test_task_run': test_task_run.id,
						'uuid': test_step_run.uuid,
						'status': test_step_run.status,
						'action': test_step_run.action,
						'result': test_step_run.result,
						# 'llm_input': test_step_run.llm_input,
						'llm_output': test_step_run.llm_output,
						# 'llm_input_tokens': test_step_run.llm_input_tokens,
						# 'llm_output_tokens': test_step_run.llm_output_tokens,
						# 'llm_thinking': test_step_run.llm_thinking,
						'llm_time_taken': test_step_run.llm_time_taken,
						'current_url': test_step_run.current_url,
						'screenshot': test_step_run.screenshot,
						'created_at': test_step_run.created_at,
						'updated_at': test_step_run.updated_at,
					}
					for test_step_run in test_step_runs
				]

				test_task_data.append(
					{
						'uuid': test_task_run.uuid,
						'test_case_run': test_case_run.id,
						'test_task_uuid': test_task_run.test_task_uuid,
						'title': test_task_run.title,
						'status': test_task_run.status,
						'test_data': test_task_run.test_data,
						'created_at': test_task_run.created_at,
						'updated_at': test_task_run.updated_at,
						'test_steps': test_step_data,
					}
				)

			response_data['test_case_runs'].append(
				{
					'uuid': test_case_run.uuid,
					'job_uuid': test_case_run.job_uuid,
					'test_case_uuid': test_case_run.test_case_uuid,
					'name': test_case_run.name,
					'priority': test_case_run.priority,
					'environment': test_case_run.environment,
					'base_url': test_case_run.base_url,
					'status': test_case_run.status,
					'video': test_case_run.video,
					'failure_screenshot': test_case_run.failure_screenshot,
					'browser': test_case_run.browser,
					'browser_session': test_case_run.browser_session,
					'created_at': test_case_run.created_at,
					'updated_at': test_case_run.updated_at,
					'test_tasks': test_task_data,
				}
			)
	elif job.job_type == JobTypeEnum.TEST_SUITE:
		for test_case_run in test_case_runs:
			response_data['test_case_runs'].append(
				{
					'uuid': test_case_run.uuid,
					'job_uuid': test_case_run.job_uuid,
					'test_case_uuid': test_case_run.test_case_uuid,
					'name': test_case_run.name,
					'priority': test_case_run.priority,
					'environment': test_case_run.environment,
					'base_url': test_case_run.base_url,
					'status': test_case_run.status,
					'video': test_case_run.video,
					'failure_screenshot': test_case_run.failure_screenshot,
					'browser': test_case_run.browser,
					'browser_session': test_case_run.browser_session,
					'created_at': test_case_run.created_at,
					'updated_at': test_case_run.updated_at,
				}
			)

	return response_data


def get_test_case_details(job_uuid, test_case_uuid):
	"""
	Fetch test case, task, and step details for a specific job and test case.

	Args:
	    job_uuid (str): The UUID of the job.
	    test_case_uuid (str): The UUID of the test case.

	Returns:
	    dict: A dictionary containing test task and step details.
	"""
	# Fetch the Job instance
	job = Job.objects.get(job_uuid=job_uuid, test_case_uuid=test_case_uuid)

	# Fetch all TestCaseRuns under the Job
	test_case_runs = job.testcaserun_set.all()  # type: ignore

	# Prepare the response structure
	response_data = {
		'test_tasks': [],
	}
	for test_case_run in test_case_runs:
		# Fetch all TestTaskRuns under the TestCaseRun
		test_task_runs = test_case_run.testtaskrun_set.all()  # type: ignore[attr-defined]
		test_task_data = []
		for test_task_run in test_task_runs:
			# Fetch all TestStepRuns under the TestTaskRun
			test_step_runs = test_task_run.teststeprun_set.all()  # type: ignore[attr-defined]
			test_step_data = [
				{
					'test_case_run': test_case_run.id,
					'test_task_run': test_task_run.id,
					'uuid': test_step_run.uuid,
					'status': test_step_run.status,
					'action': test_step_run.action,
					'result': test_step_run.result,
					# 'llm_input': test_step_run.llm_input,
					'llm_output': test_step_run.llm_output,
					# 'llm_input_tokens': test_step_run.llm_input_tokens,
					# 'llm_output_tokens': test_step_run.llm_output_tokens,
					# 'llm_thinking': test_step_run.llm_thinking,
					'llm_time_taken': test_step_run.llm_time_taken,
					'current_url': test_step_run.current_url,
					'screenshot': test_step_run.screenshot,
					'created_at': test_step_run.created_at,
					'updated_at': test_step_run.updated_at,
				}
				for test_step_run in test_step_runs
			]
			test_task_data.append(
				{
					'uuid': test_task_run.uuid,
					'test_case_run': test_case_run.id,
					'test_task_uuid': test_task_run.test_task_uuid,
					'title': test_task_run.title,
					'status': test_task_run.status,
					'test_data': test_task_run.test_data,
					'created_at': test_task_run.created_at,
					'updated_at': test_task_run.updated_at,
					'test_steps': test_step_data,
				}
			)
		response_data['test_tasks'].append(test_task_data)

	return response_data
