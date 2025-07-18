#!/usr/bin/env python3
"""
Simple test script to verify WebSocket connection to the agent service.
"""

import asyncio
import json
import sys

import websockets


async def test_websocket_connection():
	# Use the same token from the logs
	token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VyX2VtYWlsIjoic3dheWFtamFpbjIzQGdudS5hYy5pbiIsImZpcnN0X25hbWUiOiJTd2F5YW0iLCJsYXN0X25hbWUiOiJKYWluIiwiYnVzaW5lc3MiOjIsImV4cCI6MTc1Mjc3Mjg5OCwiaWF0IjoxNzUyNzcyMjk4LCJpc3MiOiJtYWluLUJ1Z093bCJ9.pHP-4ij9V1eTf_In2olgKLker9afZl01W9lG9LgQdaU'

	# Test different WebSocket URLs
	urls_to_test = [
		f'ws://localhost:8020/agent/LiveStreaming/?token={token}',
		f'ws://127.0.0.1:8020/agent/LiveStreaming/?token={token}',
	]

	for url in urls_to_test:
		print(f'\n=== Testing WebSocket connection to: {url} ===')

		try:
			# Try to connect with a timeout
			async with websockets.connect(url, timeout=10) as websocket:
				print('✅ WebSocket connection successful!')

				# Send a test message
				test_message = {'type': 'test', 'message': 'Hello WebSocket!'}
				await websocket.send(json.dumps(test_message))
				print('📤 Test message sent')

				# Try to receive a response (with timeout)
				try:
					response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
					print(f'📥 Received response: {response}')
				except TimeoutError:
					print('⏰ No response received within 5 seconds (this might be normal)')

				print('🔌 Closing connection...')

		except websockets.exceptions.ConnectionClosed as e:
			print(f'❌ WebSocket connection closed: {e}')
		except ConnectionRefusedError:
			print('❌ Connection refused - server might not be running on this port')
		except TimeoutError:
			print('❌ Connection timeout - server might not be responding')
		except Exception as e:
			print(f'❌ Unexpected error: {type(e).__name__}: {e}')


if __name__ == '__main__':
	print('🧪 WebSocket Connection Test')
	print('=' * 50)

	try:
		asyncio.run(test_websocket_connection())
	except KeyboardInterrupt:
		print('\n⚠️ Test interrupted by user')
		sys.exit(1)

	print('\n✅ Test completed')
