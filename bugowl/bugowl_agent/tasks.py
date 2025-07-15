import logging
import os

from api.utils import HttpMethod, HttpUtils
from celery import shared_task
from django.conf import settings
from job.helpers import generate_agent_JWT_token

logger = logging.getLogger(settings.ENV)


@shared_task()
def update_status_main(
	job_uuid=None,
	job_status=None,
	test_case_uuid=None,
	test_case_status=None,
):
	"""
	Update the status of a job

	Args:
		job_uuid (int): The uuid of the job to update
		job_status (str): The new status to set
		test_case_uuid (int): The uuid of the test case to update
		test_case_status (str): The new status to set for the test case
	Returns:
		bool: True if the status was updated successfully, False otherwise
	"""

	try:
		main_host = os.getenv('MAIN_SERVER_HOST', 'http://localhost:8000')
		token, payload = generate_agent_JWT_token('agent')
		response = HttpUtils.invoke_http_request_inner(
			method=HttpMethod.POST,
			url=f'{main_host}/api/job/status-update/',
			headers={'Authorization': f'Token {token}'},
			json={
				'job_uuid': job_uuid,
				'job_status': job_status,
				'test_case_uuid': test_case_uuid,
				'test_case_status': test_case_status,
			},
		)

		try:
			response_ = response.json()
		except Exception as e:
			response_ = response.text

		if response.status_code == 200:
			logger.info(f'Successfully updated job status: {response_}')
			return True, 'Status updated successfully'
		else:
			logger.error(f'Failed to update job status: {response.status_code} - {response_}')
			return False, 'Failed to update status'

	except Exception as e:
		logger.error(f'Error occurred while updating job status: {e}', exc_info=True)
		return False, 'Error occurred while updating status'
