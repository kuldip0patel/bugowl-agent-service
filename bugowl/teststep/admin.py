from django.contrib import admin

from .models import TestStepRun

# Register your models here.


@admin.register(TestStepRun)
class TestStepRunAdmin(admin.ModelAdmin):
	list_display = (
		'test_case_run',
		'test_task_run',
		'uuid',
		'status',
		'action',
		'result',
		'llm_input',
		'llm_output',
		'llm_input_tokens',
		'llm_output_tokens',
		'llm_thinking',
		'llm_time_taken',
		'network_requests',
		'console',
		'current_url',
		'caching_hash',
		'screenshot',
		'agent_history',
		'DOM',
		'created_at',
		'updated_at',
	)
	search_fields = ('uuid', 'status', 'result')
	list_filter = ('status', 'created_at', 'updated_at')
	readonly_fields = ('uuid', 'created_at', 'updated_at')
