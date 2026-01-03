# DHT/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Incident
from .email_notifications import EmailNotificationSystem
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Incident)
def send_email_on_incident_creation(sender, instance, created, **kwargs):
    """
    Envoyer un email automatiquement quand un incident est créé
    """
    if created:  # Seulement à la création, pas à la modification
        try:
            logger.info(f"Nouvel incident créé #{instance.id}, envoi d'email...")
            
            notifier = EmailNotificationSystem()
            
            # Envoyer l'alerte température
            is_high = instance.dht.temp > 8  # Vérifiez vos seuils
            notifier.send_temperature_alert(
                temperature=instance.dht.temp,
                humidity=instance.dht.humidity,
                timestamp=instance.dht.dt,
                is_high=is_high
            )
            
            # Envoyer l'email spécifique incident
            notifier.send_incident_created(instance)
            
            logger.info(f"Emails envoyés pour l'incident #{instance.id}")
            
        except Exception as e:
            logger.error(f"Erreur envoi email incident #{instance.id}: {str(e)}")