from celery.result import AsyncResult
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .tasks import health_check_task


class HealthCheckView(APIView):
	permission_classes = [AllowAny]
	authentication_classes = []  # Disable authentication entirely for this view

	def get(self, request):
		print('API: INSIDE AGENT API HEALTH CHECK VIEW')
		return Response({'status': 'healthy', 'message': 'AGENT SERVICE: API is working'}, status=status.HTTP_200_OK)


class CeleryHealthCheckView(APIView):
	permission_classes = [AllowAny]
	authentication_classes = []  # Disable authentication entirely for this view

	def get(self, request):
		try:
			print('CELERY: INSIDE AGENT CELERY HEALTH CHECK VIEW')
			# Create a test task
			task = health_check_task.delay()
			# Wait for the task to complete
			result = AsyncResult(task.id)
			result.get(timeout=5)  # Wait up to 5 seconds
			return Response(
				{'status': 'healthy', 'message': 'AGENT SERVICE: Celery is working'},
				status=status.HTTP_200_OK,
			)
		except Exception as e:
			return Response(
				{'status': 'unhealthy', 'error': str(e)},
				status=status.HTTP_503_SERVICE_UNAVAILABLE,
			)
