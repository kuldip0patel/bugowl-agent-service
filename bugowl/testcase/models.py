import uuid

from api.utils import Browser, JobStatusEnum
from django.db import models

# Create your models here.


class TestCaseRun(models.Model):
	job_uuid = models.UUIDField()  # comes from main API
	uuid = models.UUIDField(unique=True, default=uuid.uuid4)
	test_case_uuid = models.UUIDField()  # comes from main API
	environment = models.JSONField()  # plain text 50 chars #comes from main API
	base_url = models.URLField(max_length=255)  # comes from main API
	status = models.CharField(max_length=20, choices=JobStatusEnum.choices())  # Will be updated by background worker/user
	video = models.URLField(null=True, blank=True)
	failure_screenshot = models.URLField(null=True, blank=True)
	llm = models.CharField(max_length=127, null=True, blank=True)
	browser = models.CharField(max_length=20, choices=Browser.choices())
	browser_session = models.TextField()
	is_headless = models.BooleanField(default=False)
	system_prompt_hash = models.TextField(
		null=True, blank=True
	)  # Entire system prompt file will be hashed and hash value to be stored here. Will be used for caching
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	created_by = models.CharField(max_length=127)


class LLMCache(models.Model):
	caching_hash = models.TextField(null=True, blank=True, unique=True)
	llm_output = models.JSONField()
	created_at = models.DateTimeField(auto_now_add=True)
