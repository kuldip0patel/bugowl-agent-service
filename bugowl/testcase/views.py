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
			logger.error('Validation Error: %s', str(e))
			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

		logger.info('User: %s', user.user_email)
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
		if not isinstance(test_data, dict):
			raise ValidationError("'test_data' must be a dictionary mapping environment IDs to lists of test data.")
		for env_key, test_data_list in test_data.items():
			if not isinstance(test_data_list, list):
				raise ValidationError(f"Value for environment '{env_key}' must be a list of test data objects.")
			for idx, td in enumerate(test_data_list):
				if not isinstance(td, dict):
					raise ValidationError(f"Test data at index {idx} in environment '{env_key}' must be a dictionary.")
				required_fields = ['test_data_id', 'test_data_name', 'environment_id', 'environment_name', 'data']
				for field in required_fields:
					if field not in td:
						raise ValidationError(f"Missing '{field}' in test data at index {idx} for environment '{env_key}'.")
				if not isinstance(td['data'], dict):
					raise ValidationError(
						f"'data' field in test data at index {idx} for environment '{env_key}' must be a dictionary."
					)
