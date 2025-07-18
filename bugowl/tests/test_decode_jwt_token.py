#!/usr/bin/env python3
"""
Decode JWT token to check expiration and contents
"""

import json
from datetime import datetime, timezone

import jwt


def decode_jwt_token():
	token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VyX2VtYWlsIjoic3dheWFtamFpbjIzQGdudS5hYy5pbiIsImZpcnN0X25hbWUiOiJTd2F5YW0iLCJsYXN0X25hbWUiOiJKYWluIiwiYnVzaW5lc3MiOjIsImV4cCI6MTc1Mjc3Mjg5OCwiaWF0IjoxNzUyNzcyMjk4LCJpc3MiOiJtYWluLUJ1Z093bCJ9.pHP-4ij9V1eTf_In2olgKLker9afZl01W9lG9LgQdaU'

	print('🔍 JWT Token Analysis')
	print('=' * 50)

	try:
		# Decode without verification to see contents
		decoded_payload = jwt.decode(token, options={'verify_signature': False})

		print('📋 Token Payload:')
		print(json.dumps(decoded_payload, indent=2))
		print()

		# Check expiration
		exp_timestamp = decoded_payload.get('exp')
		iat_timestamp = decoded_payload.get('iat')

		if exp_timestamp:
			exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
			current_datetime = datetime.now(timezone.utc)

			print('⏰ Token Timestamps:')
			print(f'   Issued at (iat): {datetime.fromtimestamp(iat_timestamp, tz=timezone.utc) if iat_timestamp else "N/A"}')
			print(f'   Expires at (exp): {exp_datetime}')
			print(f'   Current time: {current_datetime}')
			print()

			if current_datetime > exp_datetime:
				print('❌ TOKEN IS EXPIRED!')
				time_diff = current_datetime - exp_datetime
				print(f'   Expired {time_diff} ago')
			else:
				time_diff = exp_datetime - current_datetime
				print(f'✅ Token is valid for {time_diff} more')

		print()
		print('🔑 Token Details:')
		print(f'   User ID: {decoded_payload.get("user_id")}')
		print(f'   User Email: {decoded_payload.get("user_email")}')
		print(f'   Business: {decoded_payload.get("business")}')
		print(f'   Issuer: {decoded_payload.get("iss")}')

		# Check required fields
		required_fields = ['user_id', 'user_email', 'first_name', 'last_name']
		missing_fields = [field for field in required_fields if field not in decoded_payload]

		if missing_fields:
			print(f'⚠️ Missing required fields: {missing_fields}')
		else:
			print('✅ All required fields present')

	except jwt.InvalidTokenError as e:
		print(f'❌ Invalid token: {e}')
	except Exception as e:
		print(f'❌ Error decoding token: {e}')


if __name__ == '__main__':
	decode_jwt_token()
