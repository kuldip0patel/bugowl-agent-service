import json
import logging

from django.conf import settings

from .utils import PLAYCOMMANDS

logger = logging.getLogger(settings.ENV)


async def LOAD_TASK(self, data):
	"""
	Load a task based on the provided data.
	"""
	try:
		await self.playground_agent.load_task(data)
		await self.send(text_data=json.dumps({'ACK': PLAYCOMMANDS.ACK_S2C_OK.value, 'message': 'Task loaded successfully'}))
	except Exception as e:
		await self.send(text_data=json.dumps({'ACK': PLAYCOMMANDS.ACK_S2C_ERROR.value, 'error': str(e)}))


async def EXECUTE_ALL_TASKS(self, data):
	"""
	Execute all tasks in the current session.
	"""
	try:
		await self.playground_agent.load_task(data)
		await self.playground_agent.execute_all_tasks()
		await self.send(
			text_data=json.dumps({'ACK': PLAYCOMMANDS.ACK_S2C_OK.value, 'message': 'All tasks executed successfully'})
		)
	except Exception as e:
		await self.send(text_data=json.dumps({'ACK': PLAYCOMMANDS.ACK_S2C_ERROR.value, 'error': str(e)}))


async def COMMAND_HANDLER(self, data):
	"""Handle commands received from the WebSocket.
	Args:
	    data (dict): The data received from the WebSocket.
	"""

	if not data.get('COMMANDS'):
		logger.warning('No COMMANDS found in received data')
		await self.send(
			text_data=json.dumps({'ACK': PLAYCOMMANDS.ACK_S2C_ERROR.value, 'error': 'No COMMANDS found in received data'})
		)
		return

	if data['COMMAND'] == PLAYCOMMANDS.LOAD_TASK.value:
		if not data.get('ALL_TASK_DATA'):
			logger.error('No ALL_TASK_DATA provided for LOAD_TASK command')
			await self.send(
				text_data=json.dumps(
					{'ACK': PLAYCOMMANDS.ACK_S2C_ERROR.value, 'error': 'No ALL_TASK_DATA provided for LOAD_TASK command'}
				)
			)
		else:
			logger.info('Processing LOAD_TASK command')
			await LOAD_TASK(self, data['ALL_TASK_DATA'])

	elif data['COMMAND'] == PLAYCOMMANDS.EXECUTE_ALL_TASKS.value:
		if not data.get('ALL_TASK_DATA'):
			logger.error('No ALL_TASK_DATA provided for LOAD_TASK command')
			await self.send(
				text_data=json.dumps(
					{'ACK': PLAYCOMMANDS.ACK_S2C_ERROR.value, 'error': 'No ALL_TASK_DATA provided for LOAD_TASK command'}
				)
			)
		else:
			logger.info('Processing EXECUTE_ALL_TASKS command')
			await EXECUTE_ALL_TASKS(self, data['ALL_TASK_DATA'])
	elif data['COMMAND'] == PLAYCOMMANDS.EXECUTE_TASK.value:
		pass
	elif data['COMMAND'] == PLAYCOMMANDS.STOP_TASK.value:
		pass
	else:
		logger.error(f'Unknown command received: {data["COMMAND"]}')
		await self.send(text_data=json.dumps({'ACK': 'S2C_ERROR', 'error': f'Unknown command: {data["COMMAND"]}'}))
