import logging

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .tasks import health_check_task

logger = logging.getLogger(settings.ENV)


class HealthCheckView(APIView):
	permission_classes = [AllowAny]
	authentication_classes = []  # Disable authentication entirely for this view

	def get(self, request):
		logger.info('HealthCheckView GET request received')
		print('API: INSIDE AGENT API HEALTH CHECK VIEW')
		logger.info('Health check completed successfully')
		return Response({'status': 'healthy', 'message': 'AGENT SERVICE: API is working'}, status=status.HTTP_200_OK)


class CeleryHealthCheckView(APIView):
	permission_classes = [AllowAny]
	authentication_classes = []  # Disable authentication entirely for this view

	def get(self, request):
		logger.info('CeleryHealthCheckView GET request received')
		try:
			print('CELERY: INSIDE AGENT CELERY HEALTH CHECK VIEW')
			logger.info('Creating Celery health check task')
			# Create a test task
			task = health_check_task.delay()
			# Wait for the task to complete
			print('AGENT: Waiting for Celery task to complete...')
			logger.info('Waiting for Celery task to complete with timeout=5s')
			# result = AsyncResult(task.id)
			result = task.get(timeout=5)  # Wait up to 5 seconds
			if result:
				logger.info('Celery health check task completed successfully')
				return Response(
					{'status': 'healthy', 'message': 'AGENT SERVICE: Celery is working'},
					status=status.HTTP_200_OK,
				)
			else:
				logger.warning('Celery health check task did not return True')
				return Response(
					{'status': 'unhealthy', 'message': 'AGENT SERVICE: Celery task did not return True'},
					status=status.HTTP_503_SERVICE_UNAVAILABLE,
				)
		except Exception as e:
			logger.error('AGENT SERVICE: Celery health check failed: %s', str(e), exc_info=True)
			print(f'AGENT: Error in Celery health check: {e}')
			return Response(
				{'status': 'unhealthy', 'error': str(e)},
				status=status.HTTP_503_SERVICE_UNAVAILABLE,
			)
