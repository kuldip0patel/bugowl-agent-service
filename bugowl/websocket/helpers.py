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
		await self.playground_agent.load_tasks(data)
		await self.send(text_data=json.dumps({'ACK': PLAYCOMMANDS.S2C_OK.value, 'message': 'Task loaded successfully'}))
	except Exception as e:
		raise


async def EXECUTE_ALL_TASKS(self, data):
	"""
	Execute all tasks in the current session.
	"""
	try:
		await self.playground_agent.load_tasks(data)
		await self.playground_agent.run_all_tasks()
		await self.send(text_data=json.dumps({'ACK': PLAYCOMMANDS.S2C_OK.value, 'message': 'All tasks executed successfully'}))
	except Exception as e:
		raise


async def EXECUTE_TASK(self, data, uuid):
	"""
	Execute a specific task based on the provided data.
	"""
	try:
		await self.playground_agent.load_tasks(data)
		task = await self.playground_agent.get_task(uuid)

		await self.playground_agent.run_task(task.title, {})
		await self.send(text_data=json.dumps({'ACK': PLAYCOMMANDS.S2C_OK.value, 'message': 'Task executed successfully'}))
	except Exception as e:
		raise


async def COMMAND_HANDLER(self, data):
	"""Handle commands received from the WebSocket.
	Args:
		data (dict): The data received from the WebSocket.
	"""
	try:
		if not data.get('COMMAND'):
			logger.warning('No COMMANDS found in received data')
			await self.send(
				text_data=json.dumps({'ACK': PLAYCOMMANDS.S2C_ERROR.value, 'error': 'No COMMANDS found in received data'})
			)
			return

		elif data['COMMAND'] == PLAYCOMMANDS.C2S_LOAD_TASK.value:
			if not data.get('ALL_TASK_DATA'):
				logger.error('No ALL_TASK_DATA provided for LOAD_TASK command')
				await self.send(
					text_data=json.dumps(
						{'ACK': PLAYCOMMANDS.S2C_ERROR.value, 'error': 'No ALL_TASK_DATA provided for LOAD_TASK command'}
					)
				)
			else:
				logger.info('Processing LOAD_TASK command')
				await LOAD_TASK(self, data['ALL_TASK_DATA'])

		elif data['COMMAND'] == PLAYCOMMANDS.C2S_EXECUTE_ALL_TASKS.value:
			if not data.get('ALL_TASK_DATA'):
				logger.error('No ALL_TASK_DATA provided for LOAD_TASK command')
				await self.send(
					text_data=json.dumps(
						{'ACK': PLAYCOMMANDS.S2C_ERROR.value, 'error': 'No ALL_TASK_DATA provided for LOAD_TASK command'}
					)
				)
			else:
				logger.info('Processing EXECUTE_ALL_TASKS command')
				await EXECUTE_ALL_TASKS(self, data['ALL_TASK_DATA'])
		elif data['COMMAND'] == PLAYCOMMANDS.C2S_EXECUTE_TASK.value:
			if not data.get('ALL_TASK_DATA'):
				logger.error('No ALL_TASK_DATA provided for LOAD_TASK command')
				await self.send(
					text_data=json.dumps(
						{'ACK': PLAYCOMMANDS.S2C_ERROR.value, 'error': 'No ALL_TASK_DATA provided for LOAD_TASK command'}
					)
				)
				return
			if not data.get('TASK_UUID'):
				logger.error('No TASK_UUID provided for EXECUTE_TASK command')
				await self.send(
					text_data=json.dumps(
						{'ACK': PLAYCOMMANDS.S2C_ERROR.value, 'error': 'No TASK_UUID provided for EXECUTE_TASK command'}
					)
				)
				return
			logger.info('Processing EXECUTE_TASK command')
			await EXECUTE_TASK(self, data['ALL_TASK_DATA'], data['TASK_UUID'])
		elif data['COMMAND'] == PLAYCOMMANDS.C2S_STOP.value:
			self.playground_agent.agent.stop()
		elif data['COMMAND'] == PLAYCOMMANDS.C2S_PAUSE.value:
			self.playground_agent.agent.pause()
		elif data['COMMAND'] == PLAYCOMMANDS.C2S_RESUME.value:
			self.playground_agent.agent.resume()
		else:
			logger.error(f'Unknown command received: {data["COMMAND"]}')
			await self.send(
				text_data=json.dumps({'ACK': PLAYCOMMANDS.S2C_ERROR.value, 'error': f'Unknown command: {data["COMMAND"]}'})
			)

	except Exception as e:
		raise
