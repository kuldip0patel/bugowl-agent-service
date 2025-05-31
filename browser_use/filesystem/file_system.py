import asyncio
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

INVALID_FILENAME_ERROR_MESSAGE = 'Error: Invalid filename format. Must be alphanumeric with .txt or .md extension.'


class FileSystem:
	def __init__(self, dir_path: str):
		# Create a base directory
		self.base_dir = Path(dir_path)
		self.base_dir.mkdir(parents=True, exist_ok=True)

		# Create and use a dedicated subfolder for all operations
		self.dir = self.base_dir / 'data_storage'
		if self.dir.exists():
			raise ValueError(
				'File system directory already exists - stopping for safety purposes. Please delete it first if you want to use this directory.'
			)
		self.dir.mkdir(exist_ok=True)

		# Initialize default files
		self.results_file = self.dir / 'results.md'
		self.todo_file = self.dir / 'todo.md'
		self.results_file.touch(exist_ok=True)
		self.todo_file.touch(exist_ok=True)

		# Create a thread pool executor for file operations
		self._executor = ThreadPoolExecutor()

	def _is_valid_filename(self, file_name: str) -> bool:
		"""Check if filename matches the required pattern: name.extension"""
		pattern = r'^[a-zA-Z0-9_\-]+\.(txt|md)$'
		return bool(re.match(pattern, file_name))

	async def read_file(self, file_name: str) -> str:
		if not self._is_valid_filename(file_name):
			return INVALID_FILENAME_ERROR_MESSAGE

		path = self.dir / file_name
		if not path.exists():
			return f"File '{file_name}' not found."

		try:
			# Run file read in a thread to avoid blocking
			content = await asyncio.get_event_loop().run_in_executor(self._executor, lambda: path.read_text())
			return f'Read from file {file_name}:\n{content}'
		except Exception:
			return f"Error: Could not read file '{file_name}'."

	async def write_file(self, file_name: str, content: str) -> str:
		if not self._is_valid_filename(file_name):
			return INVALID_FILENAME_ERROR_MESSAGE

		try:
			path = self.dir / file_name
			# Run file write in a thread to avoid blocking
			await asyncio.get_event_loop().run_in_executor(self._executor, lambda: path.write_text(content))
			return f'Data written to {file_name} successfully.'
		except Exception:
			return f"Error: Could not write to file '{file_name}'."

	async def append_file(self, file_name: str, content: str) -> str:
		if not self._is_valid_filename(file_name):
			return INVALID_FILENAME_ERROR_MESSAGE

		path = self.dir / file_name
		if not path.exists():
			return f"File '{file_name}' not found."

		try:
			# Run file append in a thread to avoid blocking
			await asyncio.get_event_loop().run_in_executor(self._executor, lambda p=path, c=content: p.open('a').write(c + '\n'))
			return f'Data appended to {file_name} successfully.'
		except Exception:
			return f"Error: Could not append to file '{file_name}'."

	def describe(self) -> str:
		"""List all files with their line counts."""
		description = ''
		for f in self.dir.iterdir():
			if f.is_file():
				try:
					num_lines = len(f.read_text().splitlines())
					description += f'- {f.name} — {num_lines} lines\n'
				except Exception:
					description += f'- {f.name} — [error reading file]\n'

		return description

	def get_todo_contents(self) -> str:
		return self.todo_file.read_text()
