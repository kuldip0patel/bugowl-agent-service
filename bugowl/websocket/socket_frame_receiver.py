import asyncio
import base64
import json  # Import json module

import cv2
import numpy as np
import websockets


async def receive_frames():
	token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo1NSwidXNlcl9lbWFpbCI6InRpcnRoLmtvdGhhcmlAc29tYWl5YS5lZHUiLCJmaXJzdF9uYW1lIjoiVGlydGgiLCJsYXN0X25hbWUiOiJLb3RoYXJpIiwiYnVzaW5lc3MiOjQzLCJleHAiOjE3NTI3NTY3NDYsImlhdCI6MTc1Mjc1NjE0NiwiaXNzIjoibWFpbi1CdWdPd2wifQ.0J8oirgU_9VCaYz_J-QF6vp6cAWBUwSCxQk12PWQD00'
	uri = f'ws://localhost:8020/agent/LiveStreaming/?token={token}'  # Update with the correct WebSocket URL

	headers = {'Authorization': f'Token {token}'}

	async with websockets.connect(uri) as websocket:
		print('Connected to WebSocket server.')

		while True:
			try:
				message = await websocket.recv()
				data = json.loads(message)

				if data.get('type') == 'browser_frame':
					frame_b64 = data.get('frame')
					if frame_b64:
						# Decode the base64 frame
						frame_bytes = base64.b64decode(frame_b64)
						np_frame = np.frombuffer(frame_bytes, dtype=np.uint8)
						frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

						if frame is not None:
							# Display the frame
							cv2.imshow('Live Streaming', frame)

							# Exit on pressing 'q'
							if cv2.waitKey(1) & 0xFF == ord('q'):
								break
						else:
							print('Received an invalid frame.')
			except Exception as e:
				print(f'Error receiving frame: {e}')
				break

		cv2.destroyAllWindows()


if __name__ == '__main__':
	asyncio.run(receive_frames())
