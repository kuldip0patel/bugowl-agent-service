import enum


class PLAYCOMMANDS(enum.Enum):
	S2C_CONNECT = 'S2C_CONNECT'
	C2S_CONNECT = 'C2S_CONNECT'
	C2S_RESTART = 'C2S_RESTART'
	S2C_ERROR = 'S2C_ERROR'
	C2S_LOAD_TASK = 'C2S_LOAD_TASK'
	S2C_OK = 'S2C_OK'
	C2S_EXECUTE_ALL_TASKS = 'C2S_EXECUTE_ALL_TASKS'
	C2S_EXECUTE_TASK = 'C2S_EXECUTE_TASK'
	C2S_STOP = 'C2S_STOP'
	C2S_PAUSE = 'C2S_PAUSE'
	C2S_RESUME = 'C2S_RESUME'

	@classmethod
	def choices(cls):
		return [(role.value, role.value.title()) for role in cls]


get_job_streaming_group_name = lambda job_uuid: f'BrowserStreaming_Job_{job_uuid}'
