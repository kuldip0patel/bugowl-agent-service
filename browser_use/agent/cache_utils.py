"""
Caching utilities for LLM responses in the browser_use agent.

This module provides utilities for:
1. Hashing LLM input messages deterministically
2. Serializing/deserializing AgentOutput objects for caching
3. Managing disk-based cache for LLM responses
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

import diskcache

from browser_use.agent.views import AgentOutput
from browser_use.llm.messages import BaseMessage

logger = logging.getLogger(__name__)


def _serialize_message_content(content: Any) -> str:
	"""
	Serialize message content to a deterministic string representation.

	Args:
	    content: The content to serialize (can be string, list, etc.)

	Returns:
	    str: Deterministic string representation of the content
	"""
	if isinstance(content, str):
		return content
	elif isinstance(content, list):
		# Handle list of content parts (e.g., text + image)
		serialized_parts = []
		for part in content:
			if hasattr(part, 'type'):
				if part.type == 'text':
					serialized_parts.append(f'text:{part.text}')
				elif part.type == 'image_url':
					# For images, we include the URL but not the actual image data
					# This ensures consistent hashing while being practical
					serialized_parts.append(f'image_url:{part.image_url.url}')
				elif part.type == 'refusal':
					serialized_parts.append(f'refusal:{part.refusal}')
				else:
					serialized_parts.append(f'{part.type}:{str(part)}')
			else:
				serialized_parts.append(str(part))
		return '|'.join(serialized_parts)
	else:
		return str(content)


def _serialize_tool_calls(tool_calls: list[Any]) -> str:
	"""
	Serialize tool calls to a deterministic string representation.

	Args:
	    tool_calls: List of tool call objects

	Returns:
	    str: Deterministic string representation of tool calls
	"""
	if not tool_calls:
		return ''

	serialized_calls = []
	for call in tool_calls:
		call_str = f'id:{call.id}|type:{call.type}|name:{call.function.name}|args:{call.function.arguments}'
		serialized_calls.append(call_str)

	return '||'.join(serialized_calls)


def hash_messages(messages: list[BaseMessage]) -> str:
	"""
	Generate a deterministic hash from a list of BaseMessage objects.

	This function serializes the essential content of messages (role, content, etc.)
	and creates a SHA-256 hash that can be used as a cache key.

	Args:
	    messages: List of BaseMessage objects to hash

	Returns:
	    str: Hexadecimal SHA-256 hash of the serialized messages
	"""
	# Create a list of serialized message data
	serialized_messages = []

	for msg in messages:
		msg_data = {
			'role': msg.role,
			'content': _serialize_message_content(msg.content),
		}

		# Add optional fields if present
		if hasattr(msg, 'name') and msg.name:
			msg_data['name'] = msg.name

		if hasattr(msg, 'refusal') and getattr(msg, 'refusal', None):
			msg_data['refusal'] = getattr(msg, 'refusal')

		if hasattr(msg, 'tool_calls') and getattr(msg, 'tool_calls', None):
			msg_data['tool_calls'] = _serialize_tool_calls(getattr(msg, 'tool_calls'))

		serialized_messages.append(msg_data)

	# Convert to JSON string with sorted keys for deterministic output
	json_str = json.dumps(serialized_messages, sort_keys=True, separators=(',', ':'))

	# Create SHA-256 hash
	hash_obj = hashlib.sha256(json_str.encode('utf-8'))
	return hash_obj.hexdigest()


def serialize_agent_output(agent_output: AgentOutput) -> dict[str, Any]:
	"""
	Serialize an AgentOutput object to a dictionary for caching.

	Args:
	    agent_output: The AgentOutput object to serialize

	Returns:
	    Dict[str, Any]: Serialized representation of the AgentOutput
	"""
	return {
		'thinking': agent_output.thinking,
		'evaluation_previous_goal': agent_output.evaluation_previous_goal,
		'memory': agent_output.memory,
		'next_goal': agent_output.next_goal,
		'action': [action.model_dump() for action in agent_output.action],
	}


def deserialize_agent_output(data: dict[str, Any], action_model_class: type) -> AgentOutput:
	"""
	Deserialize a dictionary back to an AgentOutput object.

	Args:
	    data: Serialized AgentOutput data
	    action_model_class: The action model class to use for deserializing actions

	Returns:
	    AgentOutput: Reconstructed AgentOutput object
	"""
	# Reconstruct action objects
	actions = []
	for action_data in data['action']:
		action_obj = action_model_class(**action_data)
		actions.append(action_obj)

	return AgentOutput(
		thinking=data['thinking'],
		evaluation_previous_goal=data['evaluation_previous_goal'],
		memory=data['memory'],
		next_goal=data['next_goal'],
		action=actions,
	)


class LLMResponseCache:
	"""
	Disk-based cache for LLM responses using diskcache.
	"""

	def __init__(self, cache_dir: str | None = None, cache_size_limit: int = 1024 * 1024 * 1024):  # 1GB default
		"""
		Initialize the LLM response cache.

		Args:
		    cache_dir: Directory to store cache files. If None, uses default location.
		    cache_size_limit: Maximum cache size in bytes (default: 1GB)
		"""
		if cache_dir is None:
			# Use a default cache directory in the user's cache directory
			cache_dir = os.path.expanduser('~/.cache/browser_use/llm_responses')

		self.cache_dir = Path(cache_dir)
		self.cache_dir.mkdir(parents=True, exist_ok=True)

		# Initialize diskcache with size limit
		self.cache = diskcache.Cache(
			directory=str(self.cache_dir), size_limit=cache_size_limit, eviction_policy='least-recently-used'
		)

		logger.info(f'Initialized LLM response cache at {self.cache_dir} with {cache_size_limit} bytes limit')

	def get(self, messages_hash: str) -> dict[str, Any] | None:
		"""
		Retrieve a cached response by message hash.

		Args:
		    messages_hash: Hash of the input messages

		Returns:
		    Optional[Dict[str, Any]]: Cached response data or None if not found
		"""
		try:
			cached_data = self.cache.get(messages_hash)
			if cached_data is not None and isinstance(cached_data, dict):
				logger.debug(f'Cache hit for hash {messages_hash[:16]}...')
				return cached_data
			else:
				logger.debug(f'Cache miss for hash {messages_hash[:16]}...')
				return None
		except Exception as e:
			logger.warning(f'Error retrieving from cache: {e}')
			return None

	def set(self, messages_hash: str, agent_output: AgentOutput) -> None:
		"""
		Store a response in the cache.

		Args:
		    messages_hash: Hash of the input messages
		    agent_output: The AgentOutput to cache
		"""
		try:
			serialized_output = serialize_agent_output(agent_output)
			self.cache.set(messages_hash, serialized_output)
			logger.debug(f'Cached response for hash {messages_hash[:16]}...')
		except Exception as e:
			logger.warning(f'Error storing in cache: {e}')

	def clear(self) -> None:
		"""Clear all cached responses."""
		try:
			self.cache.clear()
			logger.info('Cleared LLM response cache')
		except Exception as e:
			logger.warning(f'Error clearing cache: {e}')

	def stats(self) -> dict[str, Any]:
		"""Get cache statistics."""
		try:
			# Use getattr to safely access cache size
			cache_size = getattr(self.cache, '__len__', lambda: 0)()
			return {'size': cache_size, 'volume': self.cache.volume(), 'directory': str(self.cache_dir)}
		except Exception as e:
			logger.warning(f'Error getting cache stats: {e}')
			return {}
