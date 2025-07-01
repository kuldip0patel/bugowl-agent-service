from enum import Enum


class JobStatusEnum(str, Enum):
	SCHEDULED = 'Scheduled'
	QUEUED = 'Queued'
	RUNNING = 'Running'
	CANCELED = 'Canceled'
	PASS_ = 'Pass'
	FAILED = 'Failed'

	@classmethod
	def choices(cls):
		return [(role.value, role.value.title()) for role in cls]


class Browser(str, Enum):
	CHROME = 'chrome'
	FIREFOX = 'firefox'
	SAFARI = 'safari'
	EDGE = 'edge'

	@classmethod
	def choices(cls):
		return [(browser.value, browser.value.title()) for browser in cls]
