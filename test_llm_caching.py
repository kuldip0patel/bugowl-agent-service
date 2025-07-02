"""
Test script for LLM response caching functionality.

This script tests:
1. Message hashing consistency
2. AgentOutput serialization/deserialization
3. Cache storage and retrieval
4. Integration with the Agent class
"""

import asyncio
import tempfile

# Import the modules we need to test
from browser_use.agent.cache_utils import LLMResponseCache, deserialize_agent_output, hash_messages, serialize_agent_output
from browser_use.agent.views import ActionModel, AgentOutput
from browser_use.llm.messages import SystemMessage, UserMessage


def test_message_hashing():
	"""Test that message hashing is deterministic and consistent."""
	print('🧪 Testing message hashing...')

	# Create test messages
	messages1 = [SystemMessage(content='You are a helpful assistant.'), UserMessage(content='Hello, how are you?')]

	messages2 = [SystemMessage(content='You are a helpful assistant.'), UserMessage(content='Hello, how are you?')]

	messages3 = [
		SystemMessage(content='You are a helpful assistant.'),
		UserMessage(content='Hello, how are you today?'),  # Different content
	]

	# Test hash consistency
	hash1 = hash_messages(messages1)
	hash2 = hash_messages(messages2)
	hash3 = hash_messages(messages3)

	assert hash1 == hash2, 'Same messages should produce same hash'
	assert hash1 != hash3, 'Different messages should produce different hashes'
	assert len(hash1) == 64, 'SHA-256 hash should be 64 characters'

	print('✅ Hash consistency test passed')
	print(f'   Hash 1: {hash1[:16]}...')
	print(f'   Hash 2: {hash2[:16]}...')
	print(f'   Hash 3: {hash3[:16]}...')


def test_agent_output_serialization():
	"""Test AgentOutput serialization and deserialization."""
	print('\n🧪 Testing AgentOutput serialization...')

	# For testing purposes, we'll create a simple mock action model
	# that mimics the structure but doesn't require the full registry setup
	from pydantic import create_model

	from browser_use.controller.views import DoneAction

	# Create a test action model with a done field
	TestActionModel = create_model('TestActionModel', __base__=ActionModel, done=(DoneAction | None, None))

	# Create a mock action using the proper structure
	action = TestActionModel(done=DoneAction(success=True, text='Task completed'))

	# Create test AgentOutput
	original_output = AgentOutput(
		thinking='I need to complete this task',
		evaluation_previous_goal='Previous goal was successful',
		memory='User wants to test functionality',
		next_goal='Complete the test',
		action=[action],
	)

	# Test serialization
	serialized = serialize_agent_output(original_output)
	assert isinstance(serialized, dict), 'Serialized output should be a dictionary'
	assert 'thinking' in serialized, 'Serialized output should contain thinking'
	assert 'action' in serialized, 'Serialized output should contain action'

	# Test deserialization
	deserialized = deserialize_agent_output(serialized, ActionModel)
	assert isinstance(deserialized, AgentOutput), 'Deserialized should be AgentOutput'
	assert deserialized.thinking == original_output.thinking, 'Thinking should match'
	assert deserialized.memory == original_output.memory, 'Memory should match'
	assert len(deserialized.action) == len(original_output.action), 'Action count should match'

	print('✅ AgentOutput serialization test passed')


def test_cache_operations():
	"""Test cache storage and retrieval operations."""
	print('\n🧪 Testing cache operations...')

	# Create temporary cache directory
	with tempfile.TemporaryDirectory() as temp_dir:
		cache = LLMResponseCache(cache_dir=temp_dir)

		# Import the DoneAction to create a proper action
		from browser_use.controller.views import DoneAction

		# Create test data
		test_hash = 'test_hash_123'
		action_data = {'done': DoneAction(success=True, text='Test action')}
		action = ActionModel(**action_data)

		test_output = AgentOutput(
			thinking='Test thinking',
			evaluation_previous_goal='Test evaluation',
			memory='Test memory',
			next_goal='Test goal',
			action=[action],
		)

		# Test cache miss
		result = cache.get(test_hash)
		assert result is None, 'Cache should be empty initially'

		# Test cache set
		cache.set(test_hash, test_output)

		# Test cache hit
		cached_data = cache.get(test_hash)
		assert cached_data is not None, 'Cache should return stored data'
		assert isinstance(cached_data, dict), 'Cached data should be a dictionary'

		# Test deserialization of cached data
		deserialized = deserialize_agent_output(cached_data, ActionModel)
		assert deserialized.thinking == test_output.thinking, 'Cached thinking should match'

		# Test cache stats
		stats = cache.stats()
		assert stats['size'] > 0, 'Cache should have items'

		print('✅ Cache operations test passed')
		print(f'   Cache stats: {stats}')


async def test_integration_with_mock_llm():
	"""Test integration with a mock LLM to verify caching behavior."""
	print('\n🧪 Testing integration with mock LLM...')

	# This is a simplified test since we can't easily create a full Agent instance
	# We'll test the core caching logic

	from browser_use.agent.cache_utils import LLMResponseCache, hash_messages

	# Create temporary cache
	with tempfile.TemporaryDirectory() as temp_dir:
		cache = LLMResponseCache(cache_dir=temp_dir)

		# Create test messages
		messages = [SystemMessage(content='You are a test assistant.'), UserMessage(content='Perform a test action.')]

		# Generate hash
		messages_hash = hash_messages(messages)

		# Simulate first call (cache miss)
		cached_response = cache.get(messages_hash)
		assert cached_response is None, 'First call should be cache miss'

		# Import the DoneAction to create a proper action
		from browser_use.controller.views import DoneAction

		# Create mock response
		action_data = {'done': DoneAction(success=True, text='Test completed')}
		action = ActionModel(**action_data)

		mock_response = AgentOutput(
			thinking='Processing test request',
			evaluation_previous_goal='No previous goal',
			memory='Test scenario',
			next_goal='Complete test',
			action=[action],
		)

		# Cache the response
		cache.set(messages_hash, mock_response)

		# Simulate second call (cache hit)
		cached_response = cache.get(messages_hash)
		assert cached_response is not None, 'Second call should be cache hit'

		# Verify cached response can be deserialized
		deserialized = deserialize_agent_output(cached_response, ActionModel)
		assert deserialized.thinking == mock_response.thinking, 'Cached response should match original'

		print('✅ Integration test passed')
		print(f'   Messages hash: {messages_hash[:16]}...')
		print(f'   Cache hit successful: {cached_response is not None}')


def main():
	"""Run all tests."""
	print('🚀 Starting LLM caching tests...\n')

	try:
		# Run synchronous tests
		test_message_hashing()
		test_agent_output_serialization()
		test_cache_operations()

		# Run async test
		asyncio.run(test_integration_with_mock_llm())

		print('\n🎉 All tests passed! LLM caching implementation is working correctly.')

	except Exception as e:
		print(f'\n❌ Test failed: {e}')
		raise


if __name__ == '__main__':
	main()
