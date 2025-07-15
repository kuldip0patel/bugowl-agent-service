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
