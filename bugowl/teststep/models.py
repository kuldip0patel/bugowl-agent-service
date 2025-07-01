import uuid

from api.utils import JobStatusEnum
from django.db import models
from testask.models import TestTaskRun
from testcase.models import TestCaseRun

# Create your models here.


class TestStepRun(models.Model):
	test_case_run = models.ForeignKey(TestCaseRun, on_delete=models.CASCADE)  # Agent service table F Key
	test_task_run = models.ForeignKey(TestTaskRun, on_delete=models.CASCADE)  # Agent service table F Key
	uuid = models.UUIDField(unique=True, default=uuid.uuid4)
	status = models.CharField(max_length=20, choices=JobStatusEnum.choices())
	action = models.JSONField()  # Array[ { element_index = int (DOM index),element_name = char (Email/Submit/Password),element_value = char (abc@gmail.com),element_action = char (click/type/drag),element_xpath = char (xpath of element),},]
	result = models.CharField(max_length=255)
	llm_input = models.TextField()
	llm_output = models.JSONField()
	llm_input_tokens = models.IntegerField()
	llm_output_tokens = models.IntegerField()
	llm_thinking = models.TextField(null=True, blank=True)
	llm_time_taken = models.FloatField()  # // In seconds, ⏱️ LLM call took 9.70 seconds
	network_requests = models.JSONField()  # A JSON Array of REQ/RES
	console = models.TextField()
	current_url = models.URLField()  # URL/TextField (e.g. baya.biz/login baya.biz/custemer/new)
	caching_hash = models.TextField(
		null=True, blank=True
	)  # Hash/Char(127) allow null # We will do hash of ( test_task_title + llm + actions +  system_prompt_hash)
	screenshot = models.URLField(null=True, blank=True)
	agent_history = models.TextField()
	DOM = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
