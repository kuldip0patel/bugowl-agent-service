from django.contrib import admin

# Register your models here.
from .models import LLMCache, TestCaseRun


@admin.register(TestCaseRun)
class TestCaseRunAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'job',
		'job_uuid',
		'uuid',
		'test_case_uuid',
		'environment',
		'base_url',
		'status',
		'video',
		'llm',
		'browser',
		'browser_session',
		'is_headless',
		'system_prompt_hash',
		'created_at',
		'updated_at',
		'created_by',
	)
	search_fields = ('uuid', 'status', 'created_by')
	list_filter = ('status', 'created_at', 'updated_at')
	readonly_fields = ('uuid', 'created_at', 'updated_at')


@admin.register(LLMCache)
class LLMCacheAdmin(admin.ModelAdmin):
	list_display = ('caching_hash', 'llm_output', 'created_at')
	search_fields = ('caching_hash',)
	list_filter = ('created_at',)
