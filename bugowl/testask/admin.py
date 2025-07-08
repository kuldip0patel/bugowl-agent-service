from django.contrib import admin

# Register your models here.
from .models import TestTaskRun


@admin.register(TestTaskRun)
class TestTaskRunAdmin(admin.ModelAdmin):
	list_display = (
		'test_case_run',
		'uuid',
		'test_task_uuid',
		'title',
		'status',
		'test_data',
		'created_at',
		'updated_at',
	)
	search_fields = ('uuid', 'title', 'status')
	list_filter = ('status', 'created_at', 'updated_at')
	readonly_fields = (
		'uuid',
		'created_at',
		'updated_at',
	)
