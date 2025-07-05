from rest_framework import serializers

from .models import TestCaseRun


class TestCaseRunSerializer(serializers.ModelSerializer):
	class Meta:
		model = TestCaseRun
		fields = [
			'job_uuid',
			'uuid',
			'test_case_uuid',
			'name',
			'priority',
			'environment',
			'base_url',
			'status',
			'video',
			'failure_screenshot',
			'llm',
			'browser',
			'browser_session',
			'is_headless',
			'system_prompt_hash',
			'created_at',
			'updated_at',
			'created_by',
		]
		read_only_fields = ['uuid', 'created_at', 'updated_at']
