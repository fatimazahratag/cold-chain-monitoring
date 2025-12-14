from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils.timezone import localtime
from .models import Dht11, Threshold, Ticket, AuditLog
from .utils import send_telegram, send_email  # adapte selon où tu as ces helpers

@receiver(post_save, sender=Dht11)
def create_ticket_on_threshold(sender, instance: Dht11, created, **kwargs):
    if not created:
        return

    # Récupère thresholds du sensor si existant, sinon global default
    thresholds = Threshold.objects.filter(sensor=instance.sensor).first()
    if thresholds is None:
        # valeurs par défaut si pas de thresholds définis
        temp_min, temp_max = 2.0, 8.0
        hum_min, hum_max = 0.0, 100.0
    else:
        temp_min, temp_max = thresholds.temp_min, thresholds.temp_max
        hum_min, hum_max = thresholds.hum_min, thresholds.hum_max

    incident = None
    if instance.temp is not None:
        if instance.temp > temp_max:
            incident = ('temp_high', f'Température élevée {instance.temp}°C > {temp_max}°C')
        elif instance.temp < temp_min:
            incident = ('temp_low', f'Température basse {instance.temp}°C < {temp_min}°C')

    if instance.hum is not None and incident is None:
        if instance.hum > hum_max:
            incident = ('hum_high', f'Humidité élevée {instance.hum}% > {hum_max}%')
        elif instance.hum < hum_min:
            incident = ('hum_low', f'Humidité basse {instance.hum}% < {hum_min}%')

    if incident:
        incident_type, description = incident
        ticket = Ticket.objects.create(
            sensor = instance.sensor,
            incident_type = incident_type,
            temp = instance.temp,
            hum = instance.hum,
            description = description
        )

        # Audit log
        AuditLog.objects.create(action=f"Ticket créé automatiquement: {ticket.id} - {description}")

        # Send alerts (email + telegram)
        try:
            # email: utilise la fonction send_email définie dans utils ou django.core.mail
            subject = "Alerte automatique - Cold Chain"
            body = f"{description}\nSensor: {instance.sensor}\nTime: {localtime(instance.dt)}"
            # send_email(subject, body, recipient_list=[...]) or:
            from django.core.mail import send_mail
            send_mail(
                subject=subject,
                message=body,
                from_email=getattr(settings, 'EMAIL_HOST_USER', None),
                recipient_list=getattr(settings, 'ALERT_RECIPIENTS', ['rahimasaoudi65@gmail.com']),
                fail_silently=True,
            )
        except Exception as e:
            AuditLog.objects.create(action=f"Erreur envoi email auto pour ticket {ticket.id}: {e}")

        try:
            send_telegram(f"⚠️ {description} (ticket #{ticket.id})")
        except Exception as e:
            AuditLog.objects.create(action=f"Erreur envoi telegram auto pour ticket {ticket.id}: {e}")
