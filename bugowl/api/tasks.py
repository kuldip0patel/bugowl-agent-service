import logging

from celery import shared_task
from django.conf import settings

logger = logging.getLogger(settings.ENV)

from celery.signals import task_postrun, task_prerun
from django.db import connection


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
	"""Close database connections before task execution"""
	connection.close()


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
	"""Close database connections after task execution"""
	connection.close()


@shared_task
def health_check_task():
	"""
	A simple task that returns True to verify Celery is working.
	"""
	print('AGENT: Inside a celery health check task for celery health check')
	return True


# @worker_ready.connect
# def at_worker_ready(sender, **kwargs):
# 	logger.info('Celery worker is ready.')
# 	import django
# 	if not apps.ready:
# 		django.setup()
# 	from job.models import Job
# 	from job.tasks import execute_job
# 	from .utils import JobStatusEnum

# 	logger.info('Checking for queued jobs...')
# 	queued_jobs = Job.objects.filter(status=JobStatusEnum.QUEUED.value)
# 	logger.info(f'Queued {queued_jobs.count()} jobs to celery worker on startup.')
# 	for job in queued_jobs:
# 		# logger.info(f'Queued job found: {job.id}, scheduling for execution.')  # type: ignore
# 		# execute_job.delay(job.id)  # type: ignore
# 		pass  # Uncomment to enable job execution on worker startup
