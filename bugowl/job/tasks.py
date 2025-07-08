import asyncio
import logging

from celery import shared_task
from django.conf import settings
from testcase.models import TestCaseRun

from bugowl.agent import run_tasks

logger = logging.getLogger(settings.ENV)


@shared_task()
def execute_test_cases(job_instance, test_case_instance_list):
	"""
	Execute test cases of a job

	Args:
		test_case_instance_list (list): List of TestCaseRun ids.
		job_instance (Job): The job instance

	Returns:

	"""

	try:
		# Fetch TestCaseRun instances for the given ids
		test_case_instances = list(TestCaseRun.objects.filter(id__in=test_case_instance_list))
	except Exception as e:
		logger.error(f'Error occurred while fetching TestCaseRun instances: {e}', exc_info=True)
		return

	for test_case_instance in test_case_instances:
		# Fetch related test tasks for the test case
		test_tasks = test_case_instance.testtaskrun_set.all()  # type: ignore[attr-defined]

		# If the related name is not 'testtaskrun_set', use the correct one as defined in your TestTaskRun model's ForeignKey.
		# For example, if the related_name is 'test_tasks', use:
		# test_tasks = test_case_instance.test_tasks.all()

		# Extract task titles and test data dictionaries
		test_task_titles = [task.title for task in test_tasks]
		test_task_data_list = {
			task.test_data.get('name'): task.test_data.get('data')
			for task in test_tasks
			if isinstance(task.test_data, dict) and 'name' in task.test_data and 'data' in task.test_data
		}

		logger.info(f'Executing test tasks: {test_task_titles} with data: {test_task_data_list}')
		logger.info('calling the agent function')

		try:
			asyncio.run(run_tasks(test_task_titles, test_task_data_list))
		except Exception as e:
			logger.error(f'Error occurred while executing test tasks: {e}', exc_info=True)
