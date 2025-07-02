import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class AuthenticatedUser:
	def __init__(self, user_id, user_email, first_name, last_name, is_authenticated):
		self.user_id = user_id
		self.user_email = user_email
		self.first_name = first_name
		self.last_name = last_name
		self.is_authenticated = is_authenticated


class JWTAuthentication(BaseAuthentication):
	def authenticate(self, request):
		auth_header = request.headers.get('Authorization')
		if not auth_header:
			raise AuthenticationFailed('Authorization header is missing.')

		if not auth_header.startswith('Token '):
			raise AuthenticationFailed('Invalid token format. Expected "Token <token>".')

		token = auth_header.split(' ')[1]

		try:
			payload = jwt.decode(token, settings.AGENT_SERVER_SECRET_KEY, algorithms=['HS256'])
		except jwt.ExpiredSignatureError:
			raise AuthenticationFailed('Token has expired.')
		except jwt.InvalidTokenError:
			raise AuthenticationFailed('Invalid token.')

		user_id = payload.get('user_id')
		user_email = payload.get('user_email')
		first_name = payload.get('first_name')
		last_name = payload.get('last_name')

		if not all([user_id, user_email, first_name, last_name]):
			raise AuthenticationFailed('Token payload is missing user details.')

		user = AuthenticatedUser(
			user_id=user_id, user_email=user_email, first_name=first_name, last_name=last_name, is_authenticated=True
		)

		return (user, token)
