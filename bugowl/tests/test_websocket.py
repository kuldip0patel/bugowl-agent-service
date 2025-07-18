#!/usr/bin/env python3
"""
Comprehensive test for WebSocket connectivity issues
"""

import asyncio
import json
import ssl
import sys

import aiohttp
import websockets


async def test_http_endpoints():
	"""Test HTTP endpoints to verify server connectivity"""
	print('🌐 Testing HTTP endpoints...')

	base_url = 'https://stg.bugowl.helpchat.social'
	endpoints = ['/agent/health_api/', '/agent/health_celery/', '/agent/websocket_debug/']

	timeout = aiohttp.ClientTimeout(total=10)
	async with aiohttp.ClientSession(timeout=timeout) as session:
		for endpoint in endpoints:
			url = f'{base_url}{endpoint}'
			try:
				print(f'   📡 Testing: {url}')
				async with session.get(url) as response:
					print(f'   ✅ Status: {response.status}')
					if response.status == 200:
						try:
							data = await response.json()
							print(f'   📋 Response: {data}')
						except Exception as e:
							text = await response.text()
							print(f'   📄 Response: {text[:200]}... {e}')
					else:
						text = await response.text()
						print(f'   ❌ Error response: {text[:200]}...')
			except Exception as e:
				print(f'   ❌ Failed: {e}')
	print()


async def test_websocket_endpoints():
	"""Test WebSocket endpoints"""
	print('🔌 Testing WebSocket endpoints...')

	token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VyX2VtYWlsIjoic3dheWFtamFpbjIzQGdudS5hYy5pbiIsImZpcnN0X25hbWUiOiJTd2F5YW0iLCJsYXN0X25hbWUiOiJKYWluIiwiYnVzaW5lc3MiOjIsImV4cCI6MTc1Mjc3Mjg5OCwiaWF0IjoxNzUyNzcyMjk4LCJpc3MiOiJtYWluLUJ1Z093bCJ9.pHP-4ij9V1eTf_In2olgKLker9afZl01W9lG9LgQdaU'

	base_url = 'wss://stg.bugowl.helpchat.social'
	endpoints = ['/agent/LiveStreaming/', '/agent/test/']

	ssl_context = ssl.create_default_context()

	for endpoint in endpoints:
		ws_url = f'{base_url}{endpoint}?token={token}'
		print(f'   🔗 Testing: {ws_url}')

		try:
			async with websockets.connect(ws_url, ssl=ssl_context) as websocket:
				print('   ✅ WebSocket connection successful!')

				# Send test message
				test_msg = {'type': 'test', 'endpoint': endpoint}
				await websocket.send(json.dumps(test_msg))
				print('   📤 Test message sent')

				# Try to receive response
				try:
					response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
					print(f'   📥 Response: {response}')
				except TimeoutError:
					print('   ⏰ No response (normal for some endpoints)')

		except websockets.InvalidStatus as e:
			print(f'   ❌ HTTP {e.response.status_code}: {e.response.reason_phrase}')
			if hasattr(e.response, 'headers'):
				print(f'   📋 Headers: {dict(e.response.headers)}')
		except Exception as e:
			print(f'   ❌ Error: {type(e).__name__}: {e}')
	print()


async def test_different_protocols():
	"""Test different WebSocket protocols and URLs"""
	print('🔄 Testing different protocols and URLs...')

	token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VyX2VtYWlsIjoic3dheWFtamFpbjIzQGdudS5hYy5pbiIsImZpcnN0X25hbWUiOiJTd2F5YW0iLCJsYXN0X25hbWUiOiJKYWluIiwiYnVzaW5lc3MiOjIsImV4cCI6MTc1Mjc3Mjg5OCwiaWF0IjoxNzUyNzcyMjk4LCJpc3MiOiJtYWluLUJ1Z093bCJ9.pHP-4ij9V1eTf_In2olgKLker9afZl01W9lG9LgQdaU'

	test_urls = [
		f'wss://stg.bugowl.helpchat.social/agent/LiveStreaming/?token={token}',
		f'ws://stg.bugowl.helpchat.social/agent/LiveStreaming/?token={token}',
		f'wss://stg.bugowl.helpchat.social:443/agent/LiveStreaming/?token={token}',
		f'wss://stg.bugowl.helpchat.social/LiveStreaming/?token={token}',  # Without /agent prefix
	]

	ssl_context = ssl.create_default_context()

	for url in test_urls:
		print(f'   🔗 Testing: {url}')
		try:
			# Use different SSL context based on protocol
			use_ssl = ssl_context if url.startswith('wss://') else None

			async with websockets.connect(url, ssl=use_ssl) as websocket:
				print('   ✅ Connection successful!')
				break  # Stop on first successful connection
		except Exception as e:
			print(f'   ❌ Failed: {type(e).__name__}: {e}')
	print()


async def main():
	print('🧪 Comprehensive WebSocket Connectivity Test')
	print('=' * 60)

	# Test HTTP endpoints first
	await test_http_endpoints()

	# Test WebSocket endpoints
	await test_websocket_endpoints()

	# Test different protocols
	await test_different_protocols()

	print('📋 Summary:')
	print('- If HTTP endpoints work but WebSocket fails with 404:')
	print('  → Check ASGI deployment (should use Daphne, not Gunicorn)')
	print('  → Check nginx WebSocket proxy configuration')
	print('  → Verify WebSocket routing patterns')
	print()
	print('- If all endpoints fail:')
	print('  → Check server deployment and accessibility')
	print('  → Verify domain and SSL configuration')


if __name__ == '__main__':
	try:
		asyncio.run(main())
	except KeyboardInterrupt:
		print('\n⚠️ Test interrupted by user')
		sys.exit(1)

	print('\n🏁 Test completed')
