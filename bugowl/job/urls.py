from django.urls import path

from . import views

urlpatterns = [
	path('execute-job/', views.ExecuteJob.as_view(), name='execute_job'),
	path('test-case/detail/', views.JobTestCaseDetailView.as_view(), name='job_test_case_detail'),
	path('test-case/detail/public/', views.JobTestCasePublicDetailView.as_view(), name='job_test_case_public_detail'),
	path('<str:job_uuid>/detail/', views.JobDetailView.as_view(), name='job_detail'),
	path('<str:job_uuid>/detail/public/', views.JobPublicDetailView.as_view(), name='job_detail_public'),
	path('cancel-job/', views.CancelJobAPIView.as_view(), name='cancel_job'),
]
