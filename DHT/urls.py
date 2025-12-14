from django.urls import path, include
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth import views as auth_views
from rest_framework import routers

from . import views, views_tickets, api_views, views_audit, admin_views
from DHT.admin_views import add_operator, admin_dashboard as custom_dashboard_view

# -------------------- API Router --------------------
router = routers.DefaultRouter()
router.register(r'sensors', api_views.SensorViewSet)
router.register(r'thresholds', api_views.ThresholdViewSet)
router.register(r'dht', api_views.DhtViewSet)
router.register(r'tickets', api_views.TicketViewSet)

# -------------------- Custom error pages --------------------
def forbidden_403(request):
    return render(request, "403.html", status=403)

# -------------------- URL Patterns --------------------
urlpatterns = [
path('operator/dashboard/', views.operator_dashboard, name='operator_dashboard'),
# urls.py
# urls.py
path('operator/portal/', views.open_operator_dashboard, name='open_operator_dashboard'),

    # ---------- CUSTOM ADMIN (DOIT VENIR AVANT admin.site.urls) ----------
# urls.py
    path('custom/add-operator/', admin_views.add_operator, name='add_operator'),
    path('custom/list-operators/', admin_views.list_operators, name='list_operators'),
    path('admin/custom-dashboard/', login_required(custom_dashboard_view), name='admin_custom_dashboard'),
    path('admin/export-incidents/', admin_views.export_incidents_csv, name='export_incidents_csv'),
    path('admin/assign-ticket/<int:ticket_id>/', admin_views.assign_ticket, name='assign_ticket'),
    path('admin/add-comment/<int:ticket_id>/', admin_views.add_comment, name='add_comment'),
    path('custom/edit-operator/<int:user_id>/', admin_views.edit_operator, name='edit_operator'),

    # ---------- DJANGO ADMIN ----------
    path('admin/', admin.site.urls),

    # ---------- LOGIN / LOGOUT ----------
    path('admin/login/', auth_views.LoginView.as_view(template_name='admin/login.html'), name='login'),
    path('admin/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    # ---------- FRONTEND DASHBOARD ----------
    path('', views.home, name='home'),
    path('redirect-dashboard/', views.redirect_dashboard, name='redirect_dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('operator/dashboard/', views.operator_dashboard, name='operator_dashboard'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    # ---------- API ----------
    path('api/dht/add/', views.api_add_dht, name='api_add_dht'),
    path('api/latest/', views.latest_data, name='latest'),
    path('api/history/', views.history_data, name='history'),
    path('api/', include(router.urls)),

    # ---------- GRAPHS ----------
    path('graph/temp/', views.graph_temp, name='graph_temp'),
    path('graph/hum/', views.graph_hum, name='graph_hum'),

    # ---------- ALERTS ----------
    path('alerts/email/', views.send_email_alert, name='send_email_alert'),
    path('alerts/telegram/', views.send_telegram_alert, name='send_telegram_alert'),

    # ---------- TICKET SYSTEM ----------
    path('tickets/', views_tickets.tickets_list, name='tickets_list'),
    path('tickets/<int:ticket_id>/', views_tickets.ticket_detail, name='ticket_detail'),
    path('tickets/<int:ticket_id>/assign/', views_tickets.ticket_assign, name='ticket_assign'),
    path('tickets/<int:ticket_id>/close/', views_tickets.ticket_close, name='ticket_close'),

    # ---------- INCIDENTS ----------
    path('incidents/', views.dashboard_incidents, name='dashboard_incidents'),
    path('incidents/list/', views.incidents_list, name='incidents_list'),
    path('incident/<int:pk>/detail/', views.incident_detail_modal, name='incident_detail_modal'),
    path('incidents/<int:ticket_id>/assign/', views.assign_ticket, name='assign_ticket'),
    path('incidents/<int:ticket_id>/close/', views.close_ticket, name='close_ticket'),
    path('ticket/<int:ticket_id>/assign-ajax/', views.assign_ticket_ajax, name='assign_ticket_ajax'),
    path('ticket/<int:ticket_id>/close-ajax/', views.close_ticket_ajax, name='close_ticket_ajax'),

    # ---------- AUDIT ----------
    path('audit/', views_audit.audit_log_list, name='audit_list'),

    # ---------- ERROR PAGE ----------
    path('403/', forbidden_403, name='forbidden_403'),
]
