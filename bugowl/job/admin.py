from django.contrib import admin

# Register your models here.
from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'uuid',
		'test_case_uuid',
		'test_suite_uuid',
		'environment',
		'job_type',
		'status',
		'created_by',
		'business',
		'project',
		'created_at',
		'updated_at',
		'experimental',
	)
	list_filter = ('job_type', 'status', 'created_at', 'updated_at', 'experimental')
	readonly_fields = ('created_at', 'updated_at')
