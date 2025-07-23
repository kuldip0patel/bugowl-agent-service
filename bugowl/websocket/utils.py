import enum


class PLAYCOMMANDS(enum.Enum):
	C2S_START = 'C2S_START'
	ACK_S2C_CONNECT = 'ACK_S2C_CONNECT'
	C2S_CONNECT = 'C2S_CONNECT'
	ACK_S2C_ERROR = 'ACK_S2C_ERROR'
	LOAD_TASK = 'LOAD_TASK'
	ACK_S2C_OK = 'ACK_S2C_OK'
	EXECUTE_ALL_TASKS = 'EXECUTE_ALL_TASKS'
	C2S_EXECUTE_TASK = 'EXECUTE_TASK'
	C2S_STOP = 'STOP'
	C2S_PAUSE = 'PAUSE'
	C2S_RESUME = 'RESUME'

	@classmethod
	def choices(cls):
		return [(role.value, role.value.title()) for role in cls]


get_job_streaming_group_name = lambda job_uuid: f'BrowserStreaming_Job_{job_uuid}'

get_playground_streaming_key = lambda task_id: f'PlayGround:{task_id}:response'
