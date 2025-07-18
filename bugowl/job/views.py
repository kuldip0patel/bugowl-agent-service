import logging

from api.utils import JobStatusEnum
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from testcase.models import TestCaseRun

from .helpers import get_cancel_job_status_cache, get_job_details, get_test_case_details, validate_job_payload
from .models import Job
from .serializer import JobSerializer
from .tasks import execute_job
from .utils import get_cancel_cache_key

logger = logging.getLogger(settings.ENV)


class ExecuteJob(APIView):
	def post(self, request, *args, **kwargs):
		logger.info('ExecuteJob POST request received from user: %s', request.user)
		data = request.data
		logger.info('Processing job execution request with data keys: %s', list(data.keys()) if data else [])
		try:
			logger.info('Validating job payload')
			validate_job_payload(data)
			logger.info('Job payload validation successful')
		except ValidationError as e:
			logger.error('Validation Error: %s', str(e))
			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
		try:
			job_data = data.get('job')
			test_suite_uuid = data.get('test_suite').get('uuid') if data.get('test_suite') else None
			if not test_suite_uuid:
				test_case_uuid = data.get('test_case')[0]['uuid'] if data.get('test_case') else None
			else:
				test_case_uuid = None
			logger.info('Extracted job details - test_suite_uuid: %s, test_case_uuid: %s', test_suite_uuid, test_case_uuid)

			job_data = {
				'job_uuid': job_data['uuid'],
				'test_case_uuid': test_case_uuid,
				'test_suite_uuid': test_suite_uuid,
				'environment': data.get('environment'),
				'job_type': job_data['job_type'],
				'status': job_data['status'],
				'business': job_data['Business'],
				'project': job_data['Project'],
				'created_by': job_data['created_by'],
				'experimental': job_data['experimental'],
				'payload': data,
			}
			logger.info('Prepared job data for creation with UUID: %s, type: %s', job_data['job_uuid'], job_data['job_type'])

			job_cache_status = get_cancel_job_status_cache(job_data['job_uuid'])

			if job_cache_status and job_cache_status == JobStatusEnum.CANCELED.value:
				logger.info('Job %s is already cancelled, skipping creation', job_data['job_uuid'])
				return Response({'message': 'Job is already cancelled'}, status=status.HTTP_400_BAD_REQUEST)

			with transaction.atomic():
				logger.info('Starting database transaction for job creation')
				serializer = JobSerializer(data=job_data)
				if not serializer.is_valid():
					logger.error('Job serializer validation failed: %s', serializer.errors)
					return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

				job_instance = serializer.save()
				logger.info('Job created successfully with UUID: %s', job_instance.job_uuid)

			job_cache_status = get_cancel_job_status_cache(job_data['job_uuid'])

			if job_cache_status and job_cache_status == JobStatusEnum.CANCELED.value:
				logger.info('Job %s is cancelled, skipping execution', job_data['job_uuid'])
				return Response({'message': 'Job is cancelled'}, status=status.HTTP_400_BAD_REQUEST)

			logger.info('Queuing job execution for job ID: %s', job_instance.id)
			execute_job.delay(job_instance.id)  # type: ignore
			logger.info('Job execution queued successfully for UUID: %s', job_instance.job_uuid)

			return Response({'message': 'Job created successfully, Executing the Job'}, status=status.HTTP_201_CREATED)
		except ValueError as ve:
			logger.error('Value Error for testask/case: %s', str(ve), exc_info=True)
			return Response({'error for testask/case': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
		except Exception as e:
			logger.error('Error creating job: %s', str(e), exc_info=True)
			return Response({'error': 'Failed to create job', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _handle_job_detail_request(request, job_uuid, is_public=False):
	"""
	Common helper method to handle job detail requests for both authenticated and public views.

	Args:
		request: The HTTP request object
		job_uuid: The UUID of the job to fetch
		is_public (bool): Whether this is a public request (affects logging messages)

	Returns:
		Response: Django REST framework Response object
	"""
	view_type = 'public' if is_public else 'authenticated'
	logger.info('Job detail %s request received', view_type)

	try:
		logger.info('Fetching %s job details for UUID: %s', view_type, job_uuid)
		if not job_uuid:
			logger.warning('Job UUID not provided in %s request', view_type)
			return Response({'error': 'Job UUID is required'}, status=status.HTTP_400_BAD_REQUEST)

		response_data = get_job_details(job_uuid)
		logger.info('Successfully retrieved %s job details for UUID: %s', view_type, job_uuid)
		return Response(response_data, status=status.HTTP_200_OK)

	except Job.DoesNotExist:
		logger.warning('Job not found for %s request with UUID: %s', view_type, job_uuid)
		return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)
	except Exception as e:
		logger.error('Error fetching job in %s request: %s', view_type, str(e), exc_info=True)
		return Response({'error': 'Failed to fetch job', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobDetailView(APIView):
	"""
	Job detail view to fetch job details, testcaserun, testtaskrun, and teststeprun details by Job UUID.
	"""

	def get(self, request, *args, **kwargs):
		job_uuid = kwargs.get('job_uuid')
		return _handle_job_detail_request(request, job_uuid, is_public=False)


class JobPublicDetailView(APIView):
	"""Job public detail view to fetch job details, testcaserun, testtaskrun, and teststeprun details by Job UUID.
	This view is accessible without authentication.
	"""

	permission_classes = []
	authentication_classes = []

	def get(self, request, *args, **kwargs):
		job_uuid = kwargs.get('job_uuid')
		return _handle_job_detail_request(request, job_uuid, is_public=True)


def _handle_test_case_detail_request(request, is_public=False):
	"""
	Common helper method to handle test case detail requests for both authenticated and public views.

	Args:
		request: The HTTP request object
		is_public (bool): Whether this is a public request (affects logging messages)

	Returns:
		Response: Django REST framework Response object
	"""
	view_type = 'public' if is_public else 'authenticated'
	logger.info('Test case detail %s request received', view_type)

	try:
		job_uuid = request.query_params.get('job_uuid')
		test_case_uuid = request.query_params.get('test_case_uuid')
		logger.info('Fetching %s TestCaseRun for Job UUID: %s and Test Case UUID: %s', view_type, job_uuid, test_case_uuid)

		if not job_uuid:
			logger.warning('Job UUID not provided in %s test case detail request', view_type)
			return Response({'error': 'Job UUID is required'}, status=status.HTTP_400_BAD_REQUEST)
		elif not test_case_uuid:
			logger.warning('Test Case UUID not provided in %s test case detail request', view_type)
			return Response({'error': 'Test Case UUID is required'}, status=status.HTTP_400_BAD_REQUEST)

		response_data = get_test_case_details(job_uuid, test_case_uuid)
		logger.info(
			'Successfully retrieved %s test case details for Job UUID: %s, Test Case UUID: %s',
			view_type,
			job_uuid,
			test_case_uuid,
		)

		return Response(response_data, status=status.HTTP_200_OK)
	except TestCaseRun.DoesNotExist:
		logger.warning(
			'TestCaseRun not found for %s request with Job UUID: %s, Test Case UUID: %s', view_type, job_uuid, test_case_uuid
		)
		response_data = {
			'error': 'TestCaseRun not found',
			'job_uuid': job_uuid,
			'test_case_uuid': test_case_uuid,
		}
		return Response(response_data, status=status.HTTP_200_OK)
		# return Response({'error': 'TestCaseRun not found'}, status=status.HTTP_404_NOT_FOUND)
	except Exception as e:
		logger.error('Error fetching TestCaseRun in %s request: %s', view_type, str(e), exc_info=True)
		return Response({'error': 'Failed to fetch TestCaseRun', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobTestCaseDetailView(APIView):
	"""
	Job test case detail view to fetch  testcaserun, testtaskrun, and teststeprun details by Job UUID and Test Case UUID.
	"""

	def get(self, request, *args, **kwargs):
		return _handle_test_case_detail_request(request, is_public=False)


class JobTestCasePublicDetailView(APIView):
	"""
	Job test case public detail view to fetch  testcaserun, testtaskrun, and teststeprun details by Job UUID and Test Case UUID.
		This view is accessible without authentication.
	"""

	permission_classes = []
	authentication_classes = []

	def get(self, request, *args, **kwargs):
		return _handle_test_case_detail_request(request, is_public=True)


class CancelJobAPIView(APIView):
	"""
	API view to cancel a job by its UUID.
	"""

	def post(self, request, *args, **kwargs):
		job_uuid = request.data.get('job_uuid')
		logger.info('CancelJobAPI POST request received for Job UUID: %s', job_uuid)

		if not job_uuid:
			logger.warning('Job UUID not provided in cancel request')
			return Response({'error': 'Job UUID is required'}, status=status.HTTP_400_BAD_REQUEST)

		try:
			cache_key = get_cancel_cache_key(job_uuid)
			cache.set(cache_key, JobStatusEnum.CANCELED.value, timeout=2 * 24 * 60 * 60)

			return Response({'message': 'Job cancelled successfully'}, status=status.HTTP_200_OK)

		except Exception as e:
			logger.error('Error cancelling job %s: %s', job_uuid, str(e), exc_info=True)
			return Response({'error': 'Failed to cancel job', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
