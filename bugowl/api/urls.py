"""
URL configuration for bugowl_websocket project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

from .views import CeleryHealthCheckView, HealthCheckView

urlpatterns = [
	path('agent/sys/bop/', admin.site.urls),
	path('agent/health_api/', HealthCheckView.as_view(), name='health_api'),
	path('agent/health_celery/', CeleryHealthCheckView.as_view(), name='health_celery'),
	path('agent/testcase/', include('testcase.urls')),
	# path("agent/testask/", include("testask.urls")),
	# path("agent/teststep/", include("teststep.urls")),
]
