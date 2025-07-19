import enum


class PLAYCOMMANDS(enum.Enum):
	ACK_S2C_CONNECT = 'S2C_CONNECT'
	ACK_S2C_ERROR = 'S2C_ERROR'
	LOAD_TASK = 'LOAD_TASK'
	ACK_S2C_OK = 'S2C_OK'
	EXECUTE_ALL_TASKS = 'EXECUTE_ALL_TASKS'
	EXECUTE_TASK = 'EXECUTE_TASK'
	STOP_TASK = 'STOP_TASK'

	@classmethod
	def choices(cls):
		return [(role.value, role.value.title()) for role in cls]
