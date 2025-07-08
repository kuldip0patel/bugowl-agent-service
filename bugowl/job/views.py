import logging

from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .helpers import save_case_task_runs, validate_job_payload
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

	permission_classes = []  # No permission required for this view for testing purposes
	authentication_classes = []  # No authentication required for this view for testing purposes

	def get(self, request, *args, **kwargs):
		try:
			job_uuid = kwargs.get('job_uuid')
			if not job_uuid:
				return Response({'error': 'Job UUID is required'}, status=status.HTTP_400_BAD_REQUEST)

			# Fetch the Job instance
			job = Job.objects.get(job_uuid=job_uuid)

			# Fetch all TestCaseRuns under the Job
			test_case_runs = job.testcaserun_set.all()

			# Prepare the response structure
			response_data = {
				'job': {
					'uuid': job.job_uuid,
					'test_case_uuid': job.test_case_uuid,
					'test_suite_uuid': job.test_suite_uuid,
					'environment': job.environment,
					'job_type': job.job_type,
					'status': job.status,
					'created_by': job.created_by,
					'created_at': job.created_at,
					'updated_at': job.updated_at,
				},
				'test_case_runs': [],
			}

			for test_case_run in test_case_runs:
				# Fetch all TestTaskRuns under the TestCaseRun
				test_task_runs = test_case_run.testtaskrun_set.all()

				test_task_data = []
				for test_task_run in test_task_runs:
					# Fetch all TestStepRuns under the TestTaskRun
					test_step_runs = test_task_run.teststeprun_set.all()

					test_step_data = [
						{
							'test_case_run': test_case_run.id,
							'test_task_run': test_task_run.id,
							'uuid': test_step_run.uuid,
							'status': test_step_run.status,
							'action': test_step_run.action,
							'result': test_step_run.result,
							'llm_input': test_step_run.llm_input,
							'llm_output': test_step_run.llm_output,
							'llm_input_tokens': test_step_run.llm_input_tokens,
							'llm_output_tokens': test_step_run.llm_output_tokens,
							'llm_thinking': test_step_run.llm_thinking,
							'llm_time_taken': test_step_run.llm_time_taken,
							'current_url': test_step_run.current_url,
							'screenshot': test_step_run.screenshot,
							'created_at': test_step_run.created_at,
							'updated_at': test_step_run.updated_at,
						}
						for test_step_run in test_step_runs
					]

					test_task_data.append(
						{
							'uuid': test_task_run.uuid,
							'test_case_run': test_case_run.id,
							'test_task_uuid': test_task_run.test_task_uuid,
							'title': test_task_run.title,
							'status': test_task_run.status,
							'test_data': test_task_run.test_data,
							'created_at': test_task_run.created_at,
							'updated_at': test_task_run.updated_at,
							'test_steps': test_step_data,
						}
					)

				response_data['test_case_runs'].append(
					{
						'uuid': test_case_run.uuid,
						'job_uuid': test_case_run.job_uuid,
						'test_case_uuid': test_case_run.test_case_uuid,
						'name': test_case_run.name,
						'priority': test_case_run.priority,
						'environment': test_case_run.environment,
						'base_url': test_case_run.base_url,
						'status': test_case_run.status,
						'video': test_case_run.video,
						'failure_screenshot': test_case_run.failure_screenshot,
						'browser': test_case_run.browser,
						'browser_session': test_case_run.browser_session,
						'created_at': test_case_run.created_at,
						'updated_at': test_case_run.updated_at,
						'test_tasks': test_task_data,
					}
				)

			return Response(response_data, status=status.HTTP_200_OK)

		except Job.DoesNotExist:
			return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)
		except Exception as e:
			logger.error('Error fetching job: %s', str(e), exc_info=True)
			return Response({'error': 'Failed to fetch job', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
