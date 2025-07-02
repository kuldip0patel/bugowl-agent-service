from celery import shared_task


@shared_task
def health_check_task():
	"""
	A simple task that returns True to verify Celery is working.
	"""
	print('AGENT: Inside a celery health check task for celery health check')
	return True
