import logging

from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(settings.ENV)


class ExecuteJob(APIView):
	def post(self, request, *args, **kwargs):
		data = request.data
		user = request.user
		try:
			self.validate_job(data.get('job'))
			self.validate_test_suite(data.get('test_suite'))
			self.validate_test_case(data.get('test_case'))
			self.validate_environments(data.get('environments'))
			self.validate_test_data(data.get('test_data'))
		except ValidationError as e:
			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

		logger.info('User: %s', user)
		logger.info('Job Data: %s', data.get('job'))
		logger.info('Test Suite: %s', data.get('test_suite'))
		logger.info('Test Case: %s', data.get('test_case'))
		logger.info('Environments: %s', data.get('environments'))
		logger.info('Test Data: %s', data.get('test_data'))

		return Response({'message': 'JOB Received Successfully, Executing the JOB'}, status=status.HTTP_200_OK)

	def validate_job(self, job):
		if not job:
			raise ValidationError("Missing 'job' field.")
		# Add specific validation for job fields here
		# Example: if 'job_field_styles' not in job: raise ValidationError("Missing 'job_field_styles'.")

	def validate_test_suite(self, test_suite):
		if test_suite is None:
			raise ValidationError("Missing 'test_suite' field.")
		# Add specific validation for test_suite fields here

	def validate_test_case(self, test_case):
		if not test_case:
			raise ValidationError("Missing 'test_case' field.")
		# Add specific validation for test_case fields here

	def validate_environments(self, environments):
		if not isinstance(environments, list):
			raise ValidationError("'environments' must be a list.")
		for env in environments:
			# Add specific validation for environment fields here
			pass

	def validate_test_data(self, test_data):
		if not test_data:
			raise ValidationError("Missing 'test_data' field.")
		for env_key, env_data in test_data.items():
			if not isinstance(env_data, dict):
				raise ValidationError(f"Environment '{env_key}' must be a dictionary.")
			if 'data' not in env_data:
				raise ValidationError(f"Missing 'data' field in environment '{env_key}'.")
			# Add specific validation for test_data fields here
