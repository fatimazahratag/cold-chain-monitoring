from django.urls import path
from . import views, api
from .views import send_whatsapp_alert

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/dht/add/', views.api_add_dht, name='api_add_dht'),

    # Graph pages
    path('graph/temp/', views.graph_temp, name='graph_temp'),
    path('graph/hum/', views.graph_hum, name='graph_hum'),

    # API
    path('latest/', views.latest_data, name='latest'),
    path('history/', views.history_data, name='history'),

    # Email alert
    path('send_email_alert/', views.send_email_alert, name='send_email_alert'),
    path('send_telegram_alert/', views.send_telegram_alert, name='send_telegram_alert'),
    path('send-whatsapp-alert/', views.send_whatsapp_alert, name='send_whatsapp_alert'),
    path("auto-alert/", send_whatsapp_alert),

]
