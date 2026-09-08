from django.urls import path

from .admin_views import report_home


app_name = 'reports_admin'

urlpatterns = [
    path('', report_home, name='home'),
]
