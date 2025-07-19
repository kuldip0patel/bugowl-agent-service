import logging

from celery import shared_task
from celery.signals import worker_ready
from django.conf import settings

logger = logging.getLogger(settings.ENV)


@shared_task
def health_check_task():
	"""
	A simple task that returns True to verify Celery is working.
	"""
	print('AGENT: Inside a celery health check task for celery health check')
	return True


@worker_ready.connect
def at_worker_ready(sender, **kwargs):
	logger.info('Celery worker is ready.')
	from job.models import Job
	from job.tasks import execute_job

	from .utils import JobStatusEnum

	logger.info('Checking for queued jobs...')
	queued_jobs = Job.objects.filter(status=JobStatusEnum.QUEUED.value)
	for job in queued_jobs:
		logger.info(f'Queued job found: {job.id}, scheduling for execution.')  # type: ignore
		execute_job.delay(job.id)  # type: ignore
	logger.info(f'Queued {queued_jobs.count()} jobs to celery worker on startup.')
