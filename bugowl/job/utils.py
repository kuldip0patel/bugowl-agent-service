from enum import Enum


class JobTypeEnum(str, Enum):
	TEST_CASE = 'TestCase'
	TEST_SUITE = 'TestSuite'

	@classmethod
	def choices(cls):
		return [(job_type.value, job_type.value) for job_type in cls]


def get_cancel_cache_key(job_uuid):
	"""
	Generate a cache key for job cancellation based on the job UUID.
	"""
	return f'cancel_job_{job_uuid}'
