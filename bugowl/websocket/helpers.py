import json

from .utils import PLAYCOMMANDS


async def LOAD_TASK(self, data):
	"""
	Load a task based on the provided data.
	"""
	try:
		await self.playground_agent.load_task(data)
		await self.send(text_data=json.dumps({'ACK': PLAYCOMMANDS.ACK_S2C_OK.value, 'message': 'Task loaded successfully'}))
	except Exception as e:
		await self.send(text_data=json.dumps({'ACK': PLAYCOMMANDS.ACK_S2C_ERROR.value, 'error': str(e)}))
