import asyncio
import logging
import os

import redis.asyncio as aioredis
from bugowl_agent.agent import PlayGroundAgentManager
from celery import shared_task
from django.conf import settings

from .utils import PLAYCOMMANDS, get_playground_streaming_key

logger = logging.getLogger(settings.ENV)


async def Load_Task(playground_agent, tasks_to_execute, tasks_to_load):
	"""
	Load a task based on the provided data.
	"""
	try:
		logger.info('Loading tasks')
		await playground_agent.load_tasks(tasks_to_load)
		logger.info('Tasks loaded successfully')

		# If tasks_to_execute is provided, load them as well
		if tasks_to_execute:
			await playground_agent.add_tasks_to_execute(tasks_to_execute)
			logger.info('Tasks to execute added successfully')

		return True
	except Exception as e:
		logger.error(f'Error loading task: {e}', exc_info=True)
		return False


async def COMMAND_HANDLER(playground_agent, message):
	"""Handle commands received from the WebSocket.
	Args:
	    message (dict): The data received from the WebSocket.
	"""
	try:
		if not message.get('COMMAND'):
			logger.warning('No COMMANDS found in received data')
			return {'ACK': 'ERROR', 'error': 'No COMMANDS found in received data'}

		command = message['COMMAND']
		if command == PLAYCOMMANDS.C2S_EXECUTE_TASK.value:
			tasks_to_load = message.get('tasks_to_load', [])
			tasks_to_execute = message.get('tasks_to_execute', [])
			await Load_Task(playground_agent, tasks_to_execute, tasks_to_load)
		elif command == PLAYCOMMANDS.C2S_PAUSE.value:
			await playground_agent.pause_execution()
		elif command == PLAYCOMMANDS.C2S_RESUME.value:
			await playground_agent.resume_execution()
		elif command == PLAYCOMMANDS.C2S_STOP.value:
			await playground_agent.stop_execution()

	except Exception as e:
		logger.error(f'Error handling command: {e}', exc_info=True)


async def listen_to_redis_stream(playground_agent, redis, task_id):
	"""
	Listen to a Redis stream for messages related to the task_id.
	"""
	playground_agent.stream_key = get_playground_streaming_key(task_id)
	stream_key = playground_agent.stream_key
	logger.info(f'Listening to Redis stream: {stream_key}')
	last_id = '0'
	try:
		while True:
			messages = await redis.xread({stream_key: last_id}, count=1, block=0)
			if messages:
				for stream, msgs in messages:
					for message_id, message_data in msgs:
						logger.info(f'Received message from Redis stream {stream}: {message_data}')
						last_id = message_id
						await COMMAND_HANDLER(playground_agent, message_data)
						await asyncio.sleep(0.1)
	except Exception as e:
		logger.error(f'Error listening to Redis stream: {e}', exc_info=True)


@shared_task()
def execute_playground_task(task_id, channel_name):
	try:
		logger.info(f'Starting execution of playground task with ID: {task_id}')
		logger.info('Connecting to Redis for task execution')
		redis = aioredis.from_url(os.getenv('DJANGO_CACHE_LOCATION', ''), decode_responses=True)
		logger.info('Successfully connected to Redis')

		logger.info('Initializing PlayGroundAgentManager')
		playground_agent = PlayGroundAgentManager(
			task_id=task_id,
			channel_name=channel_name,
			save_conversation_path='logs/playground/conversation',
			record_video_dir=None,
		)
		logger.info('Starting browser session for playground agent')
		asyncio.run(playground_agent.start_browser_session())
		logger.info('Browser session started successfully')

		logger.info('Starting Redis stream listener')
		asyncio.create_task(listen_to_redis_stream(playground_agent, redis, task_id))

		logger.info('Executing tasks in playground agent')

		while True:
			playground_agent.execute_tasks()
		# Continue with the rest of the task execution logic
	except Exception as e:
		asyncio.run(playground_agent.stop_browser_session())
		logger.error(f'Error executing playground task: {e}', exc_info=True)
