from celery import shared_task


@shared_task
def health_check_task():
    """
    A simple task that returns True to verify Celery is working.
    """
    return True
