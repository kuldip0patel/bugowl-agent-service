from rest_framework import serializers

from .models import Job


class JobSerializer(serializers.ModelSerializer):
	class Meta:
		model = Job
		fields = [
			'uuid',
			'test_case_uuid',
			'test_suite_uuid',
			'environment',
			'job_type',
			'status',
			'business',
			'project',
			'created_by',
			'created_at',
			'updated_at',
			'experimental',
			'payload',
		]
		read_only_fields = [
			'uuid',
			'created_at',
			'updated_at',
		]
