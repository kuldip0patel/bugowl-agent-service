import logging

from bugowl_agent.agent import AgentManager
from celery import shared_task
from django.conf import settings

from job.models import Job

logger = logging.getLogger(settings.ENV)


@shared_task()
def execute_job(job_id):
	"""
	Execute a job

	Args:
		job_instance (Job): Job id
	Returns:

	"""

	try:
		job = Job.objects.get(id=job_id)
	except Job.DoesNotExist:
		logger.error(f'Job with id {job_id} does not exist')
		return False, None
	except Exception as e:
		logger.error(f'Error occurred while fetching Job instances: {e}', exc_info=True)
		return

	try:
		agent_manager = AgentManager(job)
		run_results = agent_manager.run_job()

		logger.info(f'Job executed successfully. Results: {run_results}')
		return True, run_results

	except Exception as e:
		logger.error(f'Error occurred while executing job: {e}', exc_info=True)
		return False, None

	# for test_case_instance in test_case_instances:
	# 	# Fetch related test tasks for the test case
	# 	test_tasks = test_case_instance.testtaskrun_set.all()  # type: ignore[attr-defined]

	# 	# If the related name is not 'testtaskrun_set', use the correct one as defined in your TestTaskRun model's ForeignKey.
	# 	# For example, if the related_name is 'test_tasks', use:
	# 	# test_tasks = test_case_instance.test_tasks.all()

	# 	# Extract task titles and test data dictionaries
	# 	test_task_titles = [task.title for task in test_tasks]
	# 	test_task_data_list = {
	# 		task.test_data.get('name'): task.test_data.get('data')
	# 		for task in test_tasks
	# 		if isinstance(task.test_data, dict) and 'name' in task.test_data and 'data' in task.test_data
	# 	}

	# 	logger.info(f'Executing test tasks: {test_task_titles} with data: {test_task_data_list}')
	# 	logger.info('calling the agent function')

	# 	try:
	# 		asyncio.run(run_tasks(test_task_titles, test_task_data_list))
	# 		logger.info('Agent function executed successfully')
	# 	except Exception as e:
	# 		logger.error(f'Error occurred while executing test tasks: {e}', exc_info=True)
