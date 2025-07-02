from urllib.parse import parse_qs

import jwt
from channels.middleware import BaseMiddleware
from django.conf import settings
from jwt import ExpiredSignatureError, InvalidTokenError


class JWTAuthMiddleware(BaseMiddleware):
	"""
	Middleware that authenticates WebSocket connections using JWT tokens.
	"""

	async def __call__(self, scope, receive, send):
		token = self._get_token_from_scope(scope)

		if token:
			try:
				payload = jwt.decode(token, settings.AGENT_SERVER_SECRET_KEY, algorithms=['HS256'])

				for field in ['user_id', 'user_email', 'first_name', 'last_name']:
					if field not in payload:
						raise ValueError(f'Missing field: {field}')

				scope['user'] = payload
				scope['auth_error'] = None

			except ExpiredSignatureError:
				scope['user'] = None
				scope['auth_error'] = 'Token has expired.'
			except InvalidTokenError:
				scope['user'] = None
				scope['auth_error'] = 'Invalid token.'
			except ValueError as e:
				scope['user'] = None
				scope['auth_error'] = str(e)
		else:
			scope['user'] = None
			scope['auth_error'] = 'Token not provided.'

		return await super().__call__(scope, receive, send)

	def _get_token_from_scope(self, scope):
		headers = dict(scope.get('headers', []))
		auth_header = headers.get(b'authorization', b'').decode('utf-8')
		if auth_header.startswith('Token '):
			return auth_header[6:]

		# fallback to query param
		query_string = scope.get('query_string', b'').decode('utf-8')
		query_params = parse_qs(query_string)
		token_list = query_params.get('token', [])
		if token_list:
			return token_list[0]

		return None
