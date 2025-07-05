import logging

from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .helpers import execute_test_cases, save_case_task_runs, validate_job_payload
from .serializer import JobSerializer

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

			execute_test_cases(job_instance, test_cases)

			return Response({'message': 'Job created successfully, Executing the Job'}, status=status.HTTP_201_CREATED)
		except ValueError as ve:
			logger.error('Value Error for testask/case: %s', str(ve), exc_info=True)
			return Response({'error for testask/case': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
		except Exception as e:
			logger.error('Error creating job: %s', str(e), exc_info=True)
			return Response({'error': 'Failed to create job', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
