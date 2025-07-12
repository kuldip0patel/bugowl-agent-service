import uuid

from api.utils import Browser, JobStatusEnum
from django.db import models

# Create your models here.


class TestCaseRun(models.Model):
	PRIORITY_CHOICES = [
		('Critical', 'Critical'),
		('High', 'High'),
		('Medium', 'Medium'),
		('Low', 'Low'),
	]
	job = models.ForeignKey(
		'job.Job', on_delete=models.CASCADE
	)  # Foreign key to the Job model, will be used to link test case runs
	job_uuid = models.UUIDField()  # comes from main API
	uuid = models.UUIDField(unique=True, default=uuid.uuid4)
	test_case_uuid = models.UUIDField()  # comes from main API
	name = models.TextField()  # Name of the test case, will be used for display purposes
	priority = models.CharField(
		max_length=20, choices=PRIORITY_CHOICES
	)  # Priority of the test case, will be used for display purposes
	environment = models.JSONField()  # plain text 50 chars #comes from main API
	base_url = models.URLField(max_length=255)  # comes from main API
	status = models.CharField(max_length=20, choices=JobStatusEnum.choices())  # Will be updated by background worker/user
	video = models.URLField(null=True, blank=True)
	llm = models.CharField(max_length=127, null=True, blank=True)
	browser = models.CharField(max_length=20, choices=Browser.choices())
	browser_session = models.TextField(
		null=True, blank=True
	)  # Will be used to store browser session ID or any other relevant info
	is_headless = models.BooleanField(default=False)
	system_prompt_hash = models.TextField(
		null=True, blank=True
	)  # Entire system prompt file will be hashed and hash value to be stored here. Will be used for caching
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	created_by = models.JSONField(
		null=True, blank=True
	)  # User who created this test case run, will be used to fetch user details like name, email, etc.

	def __str__(self):
		return f'{self.id} - {self.name}'  # type: ignore


class LLMCache(models.Model):
	caching_hash = models.TextField(null=True, blank=True, unique=True)
	llm_output = models.JSONField()
	created_at = models.DateTimeField(auto_now_add=True)
