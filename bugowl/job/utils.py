from enum import Enum


class JobTypeEnum(str, Enum):
	TEST_CASE = 'TestCase'
	TEST_SUITE = 'TestSuite'

	@classmethod
	def choices(cls):
		return [(job_type.value, job_type.value) for job_type in cls]
