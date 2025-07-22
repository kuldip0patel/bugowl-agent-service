import logging

from bugowl_agent.agent import AgentManager
from bugowl_agent.exceptions import JobCancelledException
from celery import shared_task
from django.conf import settings

from bugowl.api.utils import JobStatusEnum
from job.models import Job

from .helpers import get_cancel_job_status_cache

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
		job_cache_status = get_cancel_job_status_cache(job.job_uuid)

		if job_cache_status and job_cache_status == JobStatusEnum.CANCELED.value:
			logger.info('Job %s is already cancelled, skipping execution', job.job_uuid)
			raise JobCancelledException('execute_job')

		agent_manager = AgentManager(job)
		run_results = agent_manager.run_job()

		logger.info(f'Job executed successfully. Results: {run_results}')
		return True, run_results

	except JobCancelledException as e:
		logger.info(f'Job cancelled: {e}')
		job.status = JobStatusEnum.CANCELED.value
		job.save(update_fields=['status', 'updated_at'])
		# key = get_cancel_cache_key(job.job_uuid)
		# cache.delete(key)
		# logger.info(f'Cache key {key} deleted successfully.')
		return False, 'Job is Cancelled'
	except Exception as e:
		logger.error(f'Error occurred while executing job: {e}', exc_info=True)
		return False, None
