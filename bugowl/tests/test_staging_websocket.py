#!/usr/bin/env python3
"""
Test WebSocket connection to staging server
"""

import asyncio
import json
import ssl
import sys

import websockets


async def test_staging_websocket():
	# Token provided by user
	token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VyX2VtYWlsIjoic3dheWFtamFpbjIzQGdudS5hYy5pbiIsImZpcnN0X25hbWUiOiJTd2F5YW0iLCJsYXN0X25hbWUiOiJKYWluIiwiYnVzaW5lc3MiOjIsImV4cCI6MTc1Mjc3Mjg5OCwiaWF0IjoxNzUyNzcyMjk4LCJpc3MiOiJtYWluLUJ1Z093bCJ9.pHP-4ij9V1eTf_In2olgKLker9afZl01W9lG9LgQdaU'

	# WebSocket URL for staging
	ws_url = f'wss://stg.bugowl.helpchat.social/agent/LiveStreaming/?token={token}'

	print(f'🔗 Testing WebSocket connection to: {ws_url}')
	print('=' * 80)

	# Create SSL context for secure WebSocket
	ssl_context = ssl.create_default_context()

	try:
		print('🔌 Attempting to connect...')

		# Try to connect with timeout
		async with websockets.connect(ws_url, ssl=ssl_context, ping_interval=20, ping_timeout=10) as websocket:
			print('✅ WebSocket connection established successfully!')
			print(f'📡 Connected to: {websocket.remote_address}')
			# print(f'🔒 SSL/TLS: {websocket.secure}')

			# Send a test message
			test_message = {
				'type': 'test',
				'message': 'Hello from Python WebSocket client!',
				'timestamp': asyncio.get_event_loop().time(),
			}

			print(f'📤 Sending test message: {test_message}')
			await websocket.send(json.dumps(test_message))

			# Try to receive messages for a few seconds
			print('👂 Listening for messages...')
			try:
				for i in range(3):  # Try to receive up to 3 messages
					response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
					print(f'📥 Received message {i + 1}: {response}')

					# Try to parse as JSON
					try:
						parsed_response = json.loads(response)
						print(f'   📋 Parsed JSON: {parsed_response}')
					except json.JSONDecodeError:
						print(f'   📄 Raw text: {response}')

			except TimeoutError:
				print('⏰ No more messages received within timeout (this might be normal)')

			print('🔌 Connection test completed successfully')

	except websockets.ConnectionClosed as e:
		print(f'❌ WebSocket connection was closed: {e}')
		print(f'   Close code: {e.code}')
		print(f'   Close reason: {e.reason}')

	except ConnectionRefusedError:
		print('❌ Connection refused - server might not be running or accessible')

	except TimeoutError:
		print('❌ Connection timeout - server might not be responding')
		print('   💡 This could indicate network issues or server overload')

	except ssl.SSLError as e:
		print(f'❌ SSL/TLS error: {e}')
		print('   💡 This could indicate certificate issues or SSL configuration problems')

	except Exception as e:
		print(f'❌ Unexpected error: {type(e).__name__}: {e}')
		import traceback

		print('   📋 Full traceback:')
		traceback.print_exc()


if __name__ == '__main__':
	print('🧪 WebSocket Connection Test - Staging Server')
	print('=' * 50)

	try:
		asyncio.run(test_staging_websocket())
	except KeyboardInterrupt:
		print('\n⚠️ Test interrupted by user')
		sys.exit(1)

	print('\n🏁 Test completed')
