import uuid

from api.utils import JobStatusEnum
from django.db import models
from testcase.models import TestCaseRun

# Create your models here.


class TestTaskRun(models.Model):
	uuid = models.UUIDField(unique=True, default=uuid.uuid4)  # UUID for the test task run
	test_case_run = models.ForeignKey(TestCaseRun, on_delete=models.CASCADE)  # Agent service table F Key
	test_task_uuid = models.UUIDField()  # Comes from main API, UUID of the test task
	title = models.TextField()
	failure_screenshot = models.URLField(null=True, blank=True)  # URL to the failure screenshot
	status = models.CharField(max_length=20, choices=JobStatusEnum.choices())  # Will be updated by background worker/user
	test_data = models.JSONField(null=True, blank=True)  # Specific to the environment of the test case., Comes from main service
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
