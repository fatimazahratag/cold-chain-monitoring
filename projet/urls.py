from django.contrib import admin
from django.urls import path, include
from DHT.admin_views import admin_dashboard, export_incidents_csv
from DHT.admin_custom import custom_admin_site
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Custom dashboard & CSV
    path('admin/custom-dashboard/', admin_dashboard, name='admin_custom_dashboard'),
    path('admin/export-incidents/', export_incidents_csv, name='export_incidents_csv'),

    # Admin standard ou custom
    path('admin/', custom_admin_site.urls),

    # login/logout
    path('admin/login/', auth_views.LoginView.as_view(template_name='admin/login.html'), name='login'),

    # Tes urls DHT normales
    path('', include('DHT.urls')),
]
