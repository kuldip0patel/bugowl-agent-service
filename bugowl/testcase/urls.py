from django.urls import path

from . import views

urlpatterns = [
	path('execute-job/', views.ExecuteJob.as_view(), name='execute_job'),
]
