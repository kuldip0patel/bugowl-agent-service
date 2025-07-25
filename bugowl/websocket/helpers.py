import json
import logging

from api.utils import JobStatusEnum
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
		if self.playground_agent.execution:
			logger.warning('Tasks are already being executed. Please wait until the current execution is complete.')
			await self.send(
				text_data=json.dumps({'ACK': PLAYCOMMANDS.S2C_ERROR.value, 'error': 'Tasks are already being executed.'})
			)
			return False
		if self.playground_agent.paused:
			logger.warning('Tasks are paused. Please resume before executing new tasks.')
			await self.send(text_data=json.dumps({'ACK': PLAYCOMMANDS.S2C_ERROR.value, 'error': 'Tasks are paused.'}))
			return False
		if self.playground_agent.stopped:
			logger.error('PlaygroundAgentManager has been stopped. Cannot execute tasks.')
			await self.send(
				text_data=json.dumps({'ACK': PLAYCOMMANDS.S2C_ERROR.value, 'error': 'PlaygroundAgentManager has been stopped.'})
			)
			return False
		await self.playground_agent.load_tasks(data)
		run_results, response = await self.playground_agent.run_all_tasks(self.send)
		logger.info(f'run_results: {run_results}\n response: {response}')
		await self.send(
			text_data=json.dumps(
				{
					'ACK': PLAYCOMMANDS.S2C_ALL_TASKS_STATUS.value,
					'message': 'All tasks executed successfully',
					'run_results': run_results,
					'response': response,
				}
			)
		)
	except Exception as e:
		raise


async def EXECUTE_TASK(self, data, uuid):
	"""
	Execute a specific task based on the provided data.
	"""
	try:
		if self.playground_agent.execution:
			logger.warning('Tasks are already being executed. Please wait until the current execution is complete.')
			await self.send(
				text_data=json.dumps({'ACK': PLAYCOMMANDS.S2C_ERROR.value, 'error': 'Tasks are already being executed.'})
			)
			return False
		if self.playground_agent.paused:
			logger.warning('Tasks are paused. Please resume before executing a new task.')
			await self.send(text_data=json.dumps({'ACK': PLAYCOMMANDS.S2C_ERROR.value, 'error': 'Tasks are paused.'}))
			return False
		if self.playground_agent.stopped:
			logger.error('PlaygroundAgentManager has been stopped. Cannot execute tasks.')
			await self.send(
				text_data=json.dumps({'ACK': PLAYCOMMANDS.S2C_ERROR.value, 'error': 'PlaygroundAgentManager has been stopped.'})
			)
			return False

		await self.playground_agent.load_tasks(data)
		task = await self.playground_agent.get_task(uuid)
		task.status = JobStatusEnum.RUNNING.value
		await self.send(
			text_data=json.dumps(
				{
					'ACK': PLAYCOMMANDS.S2C_TASK_STATUS.value,
					'task_uuid': str(task.uuid),
					'task_title': task.title,
					'task_status': task.status,
				}
			)
		)
		history, output = await self.playground_agent.run_task(task)
		await self.send(
			text_data=json.dumps(
				{
					'ACK': PLAYCOMMANDS.S2C_TASK_STATUS.value,
					'task_uuid': str(self.playground_agent.task.uuid),
					'task_title': self.playground_agent.task.title,
					'task_status': self.playground_agent.task.status,
				}
			)
		)
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
			logger.info('Processing STOP command')
			await self.playground_agent.stop()
			await self.send(text_data=json.dumps({'ACK': PLAYCOMMANDS.S2C_STOP.value, 'message': 'stopped successfully'}))
		elif data['COMMAND'] == PLAYCOMMANDS.C2S_PAUSE.value:
			logger.info('Processing PAUSE command')
			await self.playground_agent.pause()
			await self.send(text_data=json.dumps({'ACK': PLAYCOMMANDS.S2C_PAUSE.value, 'message': 'paused successfully'}))
		elif data['COMMAND'] == PLAYCOMMANDS.C2S_RESUME.value:
			logger.info('Processing RESUME command')
			await self.playground_agent.resume()
			await self.send(text_data=json.dumps({'ACK': PLAYCOMMANDS.S2C_RESUME.value, 'message': 'resumed successfully'}))

		elif data['COMMAND'] == PLAYCOMMANDS.C2S_RESTART.value:
			logger.info('Processing RESTART command')
			await self.playground_agent.restart()
			await self.send(text_data=json.dumps({'ACK': PLAYCOMMANDS.S2C_RESTART.value, 'message': 'restarted successfully'}))

		else:
			logger.error(f'Unknown command received: {data["COMMAND"]}')
			await self.send(
				text_data=json.dumps({'ACK': PLAYCOMMANDS.S2C_ERROR.value, 'error': f'Unknown command: {data["COMMAND"]}'})
			)

	except Exception as e:
		raise
