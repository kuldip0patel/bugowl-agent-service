import uuid

from api.utils import JobStatusEnum
from django.db import models

# Create your models here.


class Job(models.Model):
	JOB_TYPE_CHOICES = [('TestCase', 'TestCase'), ('TestSuite', 'TestSuite')]
	job_uuid = models.UUIDField(unique=True, default=uuid.uuid4)  # comes from main API
	test_case_uuid = models.UUIDField(null=True, blank=True)  # comes from main API
	test_suite_uuid = models.UUIDField(null=True, blank=True)  # comes from main API
	environment = models.JSONField()  # plain text 50 chars #comes from main API
	job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
	status = models.CharField(max_length=20, choices=JobStatusEnum.choices())
	business = models.IntegerField()
	project = models.IntegerField()
	created_by = models.JSONField()
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	experimental = models.BooleanField(default=False)
	payload = models.JSONField()  # Additional data for the job
