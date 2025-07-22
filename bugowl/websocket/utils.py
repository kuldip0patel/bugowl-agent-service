import enum


class PLAYCOMMANDS(enum.Enum):
	ACK_S2C_CONNECT = 'ACK_S2C_CONNECT'
	C2S_CONNECT = 'C2S_CONNECT'
	ACK_S2C_ERROR = 'ACK_S2C_ERROR'
	LOAD_TASK = 'LOAD_TASK'
	ACK_S2C_OK = 'ACK_S2C_OK'
	EXECUTE_ALL_TASKS = 'EXECUTE_ALL_TASKS'
	EXECUTE_TASK = 'EXECUTE_TASK'
	STOP = 'STOP'
	PAUSE = 'PAUSE'
	RESUME = 'RESUME'

	@classmethod
	def choices(cls):
		return [(role.value, role.value.title()) for role in cls]


get_job_streaming_group_name = lambda job_uuid: f'BrowserStreaming_Job_{job_uuid}'
