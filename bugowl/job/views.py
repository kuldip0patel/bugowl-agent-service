import logging

from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .helpers import get_job_details, get_test_case_details, save_case_task_runs, validate_job_payload
from .models import Job
from .serializer import JobSerializer
from .tasks import execute_test_cases

logger = logging.getLogger(settings.ENV)


class ExecuteJob(APIView):
	def post(self, request, *args, **kwargs):
		data = request.data
		user = request.user
		try:
			validate_job_payload(data)
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

			with transaction.atomic():
				serializer = JobSerializer(data=job_data)
				if not serializer.is_valid():
					return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

				job_instance = serializer.save()
				logger.info('Job created successfully with UUID: %s', job_instance.job_uuid)
				logger.info('Now Saving TestCaseRun and TestTaskRun instances')

				# Save TestCaseRun and TestTaskRun instances
				# This function will handle the creation of TestCaseRun and TestTaskRun instances
				test_cases = save_case_task_runs(job_instance)

			logger.info('TestCaseRun and TestTaskRun instances saved successfully')

			logger.info('Now executing test cases')

			execute_test_cases.delay(job_instance.id, test_cases)  # type: ignore

			return Response({'message': 'Job created successfully, Executing the Job'}, status=status.HTTP_201_CREATED)
		except ValueError as ve:
			logger.error('Value Error for testask/case: %s', str(ve), exc_info=True)
			return Response({'error for testask/case': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
		except Exception as e:
			logger.error('Error creating job: %s', str(e), exc_info=True)
			return Response({'error': 'Failed to create job', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobDetailView(APIView):
	"""
	Job detail view to fetch job details, testcaserun, testtaskrun, and teststeprun details by Job UUID.
	"""

	def get(self, request, *args, **kwargs):
		try:
			job_uuid = kwargs.get('job_uuid')
			if not job_uuid:
				return Response({'error': 'Job UUID is required'}, status=status.HTTP_400_BAD_REQUEST)

			response_data = get_job_details(job_uuid)
			return Response(response_data, status=status.HTTP_200_OK)

		except Job.DoesNotExist:
			return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)
		except Exception as e:
			logger.error('Error fetching job: %s', str(e), exc_info=True)
			return Response({'error': 'Failed to fetch job', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobPublicDetailView(APIView):
	"""Job public detail view to fetch job details, testcaserun, testtaskrun, and teststeprun details by Job UUID.
	This view is accessible without authentication.
	"""

	permission_classes = []
	authentication_classes = []

	def get(self, request, *args, **kwargs):
		try:
			job_uuid = kwargs.get('job_uuid')
			if not job_uuid:
				return Response({'error': 'Job UUID is required'}, status=status.HTTP_400_BAD_REQUEST)

			response_data = get_job_details(job_uuid)

			return Response(response_data, status=status.HTTP_200_OK)

		except Job.DoesNotExist:
			return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)
		except Exception as e:
			logger.error('Error fetching job: %s', str(e), exc_info=True)
			return Response({'error': 'Failed to fetch job', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobTestCaseDetailView(APIView):
	"""
	Job test case detail view to fetch  testcaserun, testtaskrun, and teststeprun details by Job UUID and Test Case UUID.
	"""

	def get(self, request, *args, **kwargs):
		try:
			job_uuid = request.query_params.get('job_uuid')
			test_case_uuid = request.query_params.get('test_case_uuid')
			logger.info('Fetching TestCaseRun for Job UUID: %s and Test Case UUID: %s', job_uuid, test_case_uuid)
			if not job_uuid:
				return Response({'error': 'Job UUID is required'}, status=status.HTTP_400_BAD_REQUEST)
			elif not test_case_uuid:
				return Response({'error': 'Test Case UUID is required'}, status=status.HTTP_400_BAD_REQUEST)

			response_data = get_test_case_details(job_uuid, test_case_uuid)

			return Response(response_data, status=status.HTTP_200_OK)
		except Job.DoesNotExist:
			return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)
		except Exception as e:
			logger.error('Error fetching TestCaseRun: %s', str(e), exc_info=True)
			return Response(
				{'error': 'Failed to fetch TestCaseRun', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)


class JobTestCasePublicDetailView(APIView):
	"""
	Job test case public detail view to fetch  testcaserun, testtaskrun, and teststeprun details by Job UUID and Test Case UUID.
		This view is accessible without authentication.
	"""

	permission_classes = []
	authentication_classes = []

	def get(self, request, *args, **kwargs):
		try:
			job_uuid = request.query_params.get('job_uuid')
			test_case_uuid = request.query_params.get('test_case_uuid')
			logger.info('Fetching TestCaseRun for Job UUID: %s and Test Case UUID: %s', job_uuid, test_case_uuid)
			if not job_uuid:
				return Response({'error': 'Job UUID is required'}, status=status.HTTP_400_BAD_REQUEST)
			elif not test_case_uuid:
				return Response({'error': 'Test Case UUID is required'}, status=status.HTTP_400_BAD_REQUEST)

			response_data = get_test_case_details(job_uuid, test_case_uuid)

			return Response(response_data, status=status.HTTP_200_OK)
		except Job.DoesNotExist:
			return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)
		except Exception as e:
			logger.error('Error fetching TestCaseRun: %s', str(e), exc_info=True)
			return Response(
				{'error': 'Failed to fetch TestCaseRun', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)
