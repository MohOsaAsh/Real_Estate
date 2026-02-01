# ====================================
# 3. audit_log/urls.py
# ====================================

from django.urls import path
from . import views

app_name = 'audit_log'

urlpatterns = [
    path('', views.audit_dashboard, name='dashboard'),
    path('logs/', views.audit_logs_list, name='logs_list'),
    path('logs/<int:pk>/', views.audit_log_detail, name='log_detail'),
    path('reports/', views.audit_reports, name='reports'),
    path('api/stats/', views.audit_api_stats, name='api_stats'),
]
