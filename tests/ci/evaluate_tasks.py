"""
Runs all agent tasks in parallel (up to 10 at a time) using separate subprocesses.
Each task gets its own Python process, preventing browser session interference.
Does not fail on partial failures (always exits 0).
"""

import argparse
import asyncio
import glob
import json
import logging
import os
import sys
import warnings

import aiofiles
import yaml
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from browser_use.agent.service import Agent
from browser_use.agent.views import AgentHistoryList
from browser_use.browser.profile import BrowserProfile
from browser_use.browser.session import BrowserSession

# --- CONFIG ---
MAX_PARALLEL = 10
TASK_DIR = (
	sys.argv[1]
	if len(sys.argv) > 1 and not sys.argv[1].startswith('--')
	else os.path.join(os.path.dirname(__file__), '../agent_tasks')
)
TASK_FILES = glob.glob(os.path.join(TASK_DIR, '*.yaml'))


class JudgeResponse(BaseModel):
	success: bool
	explanation: str


async def run_single_task(task_file):
	"""Run a single task in the current process (called by subprocess)"""
	try:
		# Suppress all logging in subprocess to avoid interfering with JSON output
		logging.getLogger().setLevel(logging.CRITICAL)
		for logger_name in ['browser_use', 'telemetry', 'message_manager']:
			logging.getLogger(logger_name).setLevel(logging.CRITICAL)
		warnings.filterwarnings('ignore')

		async with aiofiles.open(task_file, 'r') as f:
			content = await f.read()
		task_data = yaml.safe_load(content)
		task = task_data['task']
		judge_context = task_data.get('judge_context', ['The agent must solve the task'])
		max_steps = task_data.get('max_steps', 15)
		agent_llm = ChatOpenAI(model='gpt-4.1-mini')
		judge_llm = ChatOpenAI(model='gpt-4.1-mini')

		# Each subprocess gets its own profile and session
		profile = BrowserProfile(
			headless=True,
			user_data_dir=None,
		)
		session = BrowserSession(browser_profile=profile)

		agent = Agent(task=task, llm=agent_llm, browser_session=session)
		history: AgentHistoryList = await agent.run(max_steps=max_steps)
		agent_output = history.final_result() or ''

		criteria = '\n- '.join(judge_context)
		judge_prompt = f"""
You are a evaluator of a browser agent task inside a ci/cd pipeline. Here was the agent's task:
{task}

Here is the agent's output:
{agent_output}

Criteria for success:
- {criteria}

Reply in JSON with keys: success (true/false), explanation (string).
"""
		structured_llm = judge_llm.with_structured_output(JudgeResponse)
		judge_response = await structured_llm.ainvoke(judge_prompt)

		result = {
			'file': os.path.basename(task_file),
			'success': judge_response.success,
			'explanation': judge_response.explanation,
		}

		# Clean up session before returning
		await session.stop()

		return result

	except Exception as e:
		# Ensure session cleanup even on error
		try:
			await session.stop()
		except Exception:
			pass

		return {'file': os.path.basename(task_file), 'success': False, 'explanation': f'Task failed with error: {str(e)}'}


async def run_task_subprocess(task_file, semaphore):
	"""Run a task in a separate subprocess"""
	async with semaphore:
		try:
			# Set environment to reduce noise in subprocess
			env = os.environ.copy()
			env['PYTHONPATH'] = os.pathsep.join(sys.path)

			proc = await asyncio.create_subprocess_exec(
				sys.executable,
				__file__,
				'--task',
				task_file,
				stdout=asyncio.subprocess.PIPE,
				stderr=asyncio.subprocess.PIPE,
				env=env,
			)
			stdout, stderr = await proc.communicate()

			if proc.returncode == 0:
				try:
					# Parse JSON result from subprocess
					stdout_text = stdout.decode().strip()
					# Find the JSON line (should be the last line that starts with {)
					lines = stdout_text.split('\n')
					json_line = None
					for line in reversed(lines):
						line = line.strip()
						if line.startswith('{') and line.endswith('}'):
							json_line = line
							break

					if json_line:
						result = json.loads(json_line)
					else:
						raise ValueError(f'No JSON found in output: {stdout_text}')

				except (json.JSONDecodeError, ValueError) as e:
					result = {
						'file': os.path.basename(task_file),
						'success': False,
						'explanation': f'Failed to parse subprocess result: {str(e)[:100]}',
					}
			else:
				stderr_text = stderr.decode().strip()
				result = {
					'file': os.path.basename(task_file),
					'success': False,
					'explanation': f'Subprocess failed (code {proc.returncode}): {stderr_text[:200]}',
				}
		except Exception as e:
			result = {
				'file': os.path.basename(task_file),
				'success': False,
				'explanation': f'Failed to start subprocess: {str(e)}',
			}

		return result


async def main():
	"""Run all tasks in parallel using subprocesses"""
	semaphore = asyncio.Semaphore(MAX_PARALLEL)

	print(f'Found task files: {TASK_FILES}')

	if not TASK_FILES:
		print('No task files found!')
		return 0, 0

	# Run all tasks in parallel subprocesses
	tasks = [run_task_subprocess(task_file, semaphore) for task_file in TASK_FILES]
	results = await asyncio.gather(*tasks)

	passed = sum(1 for r in results if r['success'])
	total = len(results)

	print('\n' + '=' * 60)
	print(f'{"RESULTS":^60}\n')

	# Prepare table data
	headers = ['Task', 'Success', 'Reason']
	rows = []
	for r in results:
		status = '✅' if r['success'] else '❌'
		rows.append([r['file'], status, r['explanation']])

	# Calculate column widths
	col_widths = [max(len(str(row[i])) for row in ([headers] + rows)) for i in range(3)]

	# Print header
	header_row = ' | '.join(headers[i].ljust(col_widths[i]) for i in range(3))
	print(header_row)
	print('-+-'.join('-' * w for w in col_widths))

	# Print rows
	for row in rows:
		print(' | '.join(str(row[i]).ljust(col_widths[i]) for i in range(3)))

	print('\n' + '=' * 60)
	print(f'\n{"SCORE":^60}')
	print(f'\n{"=" * 60}\n')
	print(f'\n{"*" * 10}  {passed}/{total} PASSED  {"*" * 10}\n')
	print('=' * 60 + '\n')

	return passed, total


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--task', type=str, help='Path to a single task YAML file (for subprocess mode)')
	args = parser.parse_args()

	if args.task:
		# Subprocess mode: run a single task and output ONLY JSON
		try:
			result = asyncio.run(run_single_task(args.task))
			# Output ONLY the JSON result, nothing else
			print(json.dumps(result))
		except Exception as e:
			# Even on critical failure, output valid JSON
			error_result = {
				'file': os.path.basename(args.task),
				'success': False,
				'explanation': f'Critical subprocess error: {str(e)}',
			}
			print(json.dumps(error_result))
	else:
		# Parent process mode: run all tasks in parallel subprocesses
		passed, total = asyncio.run(main())
		print(f'PASSED={passed}')
		print(f'TOTAL={total}')
