from .models import SystemLog
from django.contrib.auth.models import User
from django.utils import timezone
import json

def create_system_log(level, category, message, details=None, user=None):
    """
    Crée un log système
    """
    log = SystemLog.objects.create(
        level=level,
        category=category,
        message=message,
        details=details if details else {},
        user=user
    )
    return log

def log_temperature_alert(temp, normal_range_min=2, normal_range_max=8):
    """Log une alerte de température"""
    if temp > normal_range_max:
        message = f"Température élevée détectée: {temp}°C"
        details = {
            'temperature': temp,
            'threshold': normal_range_max,
            'type': 'high_temperature'
        }
        return create_system_log('warning', 'temperature', message, details)
    elif temp < normal_range_min:
        message = f"Température basse détectée: {temp}°C"
        details = {
            'temperature': temp,
            'threshold': normal_range_min,
            'type': 'low_temperature'
        }
        return create_system_log('warning', 'temperature', message, details)
    return None

def log_humidity_alert(humidity, normal_range_min=40, normal_range_max=90):
    """Log une alerte d'humidité"""
    if humidity > normal_range_max:
        message = f"Humidité élevée détectée: {humidity}%"
        details = {
            'humidity': humidity,
            'threshold': normal_range_max,
            'type': 'high_humidity'
        }
        return create_system_log('warning', 'humidity', message, details)
    elif humidity < normal_range_min:
        message = f"Humidité basse détectée: {humidity}%"
        details = {
            'humidity': humidity,
            'threshold': normal_range_min,
            'type': 'low_humidity'
        }
        return create_system_log('warning', 'humidity', message, details)
    return None

def log_incident_created(incident, user=None):
    """Log la création d'un incident"""
    message = f"Incident #{incident.id} créé - Température: {incident.dht.temp}°C"
    details = {
        'incident_id': incident.id,
        'temperature': incident.dht.temp,
        'humidity': incident.dht.humidity,
        'status': incident.statut
    }
    return create_system_log('warning', 'incident', message, details, user)

def log_incident_resolved(incident, user=None):
    """Log la résolution d'un incident"""
    message = f"Incident #{incident.id} résolu"
    details = {
        'incident_id': incident.id,
        'temperature': incident.dht.temp,
        'resolved_by': user.username if user else None
    }
    return create_system_log('info', 'incident', message, details, user)

def log_user_activity(action, user, details=None):
    """Log une activité utilisateur"""
    message = f"Utilisateur {user.username} - {action}"
    return create_system_log('info', 'user', message, details, user)

def log_system_start():
    """Log le démarrage du système"""
    return create_system_log('info', 'system', 'Système démarré avec succès')

def log_data_received(temp, humidity):
    """Log la réception de nouvelles données"""
    message = f"Nouvelles données reçues: {temp}°C, {humidity}%"
    details = {
        'temperature': temp,
        'humidity': humidity
    }
    return create_system_log('info', 'system', message, details)