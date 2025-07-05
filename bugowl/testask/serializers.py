from rest_framework import serializers

from .models import TestTaskRun


class TestTaskRunSerializer(serializers.ModelSerializer):
	class Meta:
		model = TestTaskRun
		fields = [
			'uuid',
			'test_case_run',
			'test_task_uuid',
			'title',
			'status',
			'test_data',
			'created_at',
			'updated_at',
		]
		read_only_fields = ['uuid', 'created_at', 'updated_at']
