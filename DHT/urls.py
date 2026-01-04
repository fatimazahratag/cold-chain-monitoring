from django.urls import path
from . import views
from django.shortcuts import redirect

def redirect_root(request):
    return redirect('home')  # 'home' correspond au name='home' de path('api/home/', ...)

urlpatterns = [
    path('', redirect_root),
    path('api/home/', views.home, name='home'),  # page home accessible sur /api/home
    path('api/dashboard/', views.dashboard, name='dashboard'),
    path('api/latest/', views.latest_data, name='latest_data'),  # ← ajouté
    path('api/operator/', views.operator_dashboard, name='operator_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('nettoyer-doublons/', views.nettoyer_incidents_doublons, name='nettoyer_doublons'),
    path('system-logs/', views.system_logs_view, name='system_logs'),
    path('alert-history/', views.alert_history_view, name='alert_history'),
    path('clear-logs/', views.clear_logs_view, name='clear_logs'),
    path('export-logs-csv/', views.export_logs_csv, name='export_logs_csv'),
    path('export-incidents-csv/', views.export_incidents_csv, name='export_incidents_csv'),
    path('test-email/', views.test_email_view, name='test_email'),
 ]

