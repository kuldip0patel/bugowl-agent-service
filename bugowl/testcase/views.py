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
			self.validate_environment(data.get('environment'))
			self.validate_test_data(data.get('test_data'))
		except ValidationError as e:
			logger.error('Validation Error: %s', str(e))
			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

		logger.info('User: %s', user.user_email)
		logger.info('Job Data: %s', data.get('job'))
		logger.info('Test Suite: %s', data.get('test_suite'))
		logger.info('Test Case: %s', data.get('test_case'))
		logger.info('Environment: %s', data.get('environment'))
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

	def validate_environment(self, environment):
		if not isinstance(environment, dict):
			raise ValidationError("'environment' must be a dictionary.")
		for key, value in environment.items():
			# Add specific validation for environment fields here
			pass

	def validate_test_data(self, test_data):
		if not test_data:
			raise ValidationError("Missing 'test_data' field.")
		if not isinstance(test_data, dict):
			raise ValidationError("'test_data' must be a dictionary mapping test data names to data values.")
		for test_data_name, data_value in test_data.items():
			if not isinstance(test_data_name, str):
				raise ValidationError('Test data name must be a string.')
			if not isinstance(data_value, dict):
				raise ValidationError(f"Value for '{test_data_name}' must be a dictionary (key-value pairs).")
