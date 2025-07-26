import enum


class PLAYCOMMANDS(enum.Enum):
	S2C_CONNECT = 'S2C_CONNECT'
	C2S_CONNECT = 'C2S_CONNECT'
	S2C_ERROR = 'S2C_ERROR'
	C2S_RUN_ALL_TASKS = 'C2S_RUN_ALL_TASKS'
	C2S_RUN_TASK = 'C2S_RUN_TASK'
	C2S_STOP = 'C2S_STOP'
	S2C_STOP = 'S2C_STOP'
	C2S_PAUSE = 'C2S_PAUSE'
	S2C_PAUSE = 'S2C_PAUSE'
	C2S_RESUME = 'C2S_RESUME'
	S2C_RESUME = 'S2C_RESUME'
	S2C_TASK_STATUS = 'S2C_TASK_STATUS'
	S2C_ALL_TASKS_STATUS = 'S2C_ALL_TASKS_STATUS'

	@classmethod
	def choices(cls):
		return [(role.value, role.value.title()) for role in cls]


get_job_streaming_group_name = lambda job_uuid: f'BrowserStreaming_Job_{job_uuid}'
