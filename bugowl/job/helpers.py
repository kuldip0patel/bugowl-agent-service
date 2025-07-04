from rest_framework.exceptions import ValidationError


def validate_job_payload(data):
	def validate_job(job):
		if not job:
			raise ValidationError("Missing 'job' field.")
		required_fields = [
			'id',
			'uuid',
			'status',
			'job_type',
			'created_at',
			'updated_at',
			'test_case',
			'test_suite',
			'experimental',
			'Business',
			'Project',
			'created_by',
		]
		for field in required_fields:
			if field not in job:
				raise ValidationError(f"Missing '{field}' in job.")
		if not isinstance(job['created_by'], dict):
			raise ValidationError("'created_by' in job must be a dictionary.")
		for field in ['id', 'full_name', 'email']:
			if field not in job['created_by']:
				raise ValidationError(f"Missing '{field}' in job['created_by'].")

	def validate_case_suite(case, suite):
		if not (suite or case):
			raise ValidationError("Missing 'test_suite' and 'test_case' field.")
		if case:
			if not isinstance(case, list):
				raise ValidationError("'test_case' must be a list.")
			for test_case in case:
				required_fields = ['id', 'uuid', 'test_suite', 'name', 'priority', 'browser', 'is_draft', 'test_task']
				for field in required_fields:
					if field not in test_case:
						raise ValidationError(f"Missing '{field}' in test_case.")
				if not isinstance(test_case['test_task'], list):
					raise ValidationError("'test_task' in test_case must be a list.")
				for idx, task in enumerate(test_case['test_task']):
					required_fields = ['id', 'uuid', 'title', 'created_at', 'updated_at', 'created_by', 'test_data']
					for field in required_fields:
						if field not in task:
							raise ValidationError(f"Missing '{field}' in test_task at index {idx}.")
					if not isinstance(task['created_by'], int):
						raise ValidationError(f"'created_by' in test_task at index {idx} must be an integer (user id).")
					if task['test_data'] is not None and not isinstance(task['test_data'], int):
						raise ValidationError(f"'test_data' in test_task at index {idx} must be an integer or null.")
		if suite:
			if not isinstance(suite, dict):
				raise ValidationError("'test_suite' must be a dictionary.")
			required_fields = ['id', 'name', 'description', 'language', 'priority', 'type']
			for field in required_fields:
				if field not in suite:
					raise ValidationError(f"Missing '{field}' in test_suite.")

	def validate_environment(environment):
		if not isinstance(environment, dict):
			raise ValidationError("'environment' must be a dictionary.")
		required_fields = ['id', 'name', 'description', 'url']
		for field in required_fields:
			if field not in environment:
				raise ValidationError(f"Missing '{field}' in environment.")

	def validate_test_data(test_data):
		if not test_data:
			return
		if not isinstance(test_data, dict):
			raise ValidationError("'test_data' must be a dictionary mapping test data names to data values.")
		for test_data_name, data_value in test_data.items():
			if not isinstance(test_data_name, str):
				raise ValidationError('Test data name must be a string.')
			if not isinstance(data_value, dict):
				raise ValidationError(f"Value for '{test_data_name}' must be a dictionary (key-value pairs).")

	validate_job(data.get('job'))
	validate_case_suite(data.get('test_case'), data.get('test_suite'))
	validate_environment(data.get('environment'))
	validate_test_data(data.get('test_data'))
