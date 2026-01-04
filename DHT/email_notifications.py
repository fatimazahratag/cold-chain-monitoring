# DHT/email_notifications.py
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
import logging
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailNotificationSystem:
    """Système de notifications email pour ColdChain"""
    
    def __init__(self):
        self.admin_email = settings.ALERT_EMAIL_ADMIN
        self.operator_email = settings.ALERT_EMAIL_OPERATOR
        self.from_email = settings.DEFAULT_FROM_EMAIL
        
        # Vérifier la configuration
        self.enabled = bool(settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD)
        if not self.enabled:
            logger.warning("Email notifications are disabled. Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in settings.")
    
    def _get_context(self, temperature, humidity, timestamp, is_high=True):
        """Générer le contexte pour les templates"""
        alert_type = "HAUTE" if is_high else "BASSE"
        threshold = settings.ALERT_TEMP_HIGH if is_high else settings.ALERT_TEMP_LOW
        ecart = abs(temperature - threshold)
        
        return {
            'temperature': f"{temperature:.1f}",
            'humidity': f"{humidity:.1f}",
            'timestamp': timestamp,
            'is_high': is_high,
            'alert_type': alert_type,
            'threshold': f"{threshold:.1f}",
            'ecart': f"{ecart:.1f}",
            'low_threshold': f"{settings.ALERT_TEMP_LOW:.1f}",
            'high_threshold': f"{settings.ALERT_TEMP_HIGH:.1f}",
            'dashboard_url': "http://localhost:8000/dashboard/",
            'sensor_id': "DHT-001",
            'year': datetime.now().year,
        }
    
    def send_temperature_alert(self, temperature, humidity, timestamp, is_high=True):
        """
        Envoyer une alerte email pour température anormale
        """
        if not self.enabled:
            logger.error("Cannot send email: Email notifications disabled")
            return False
        
        try:
            # Sujet de l'email
            alert_type = "HAUTE" if is_high else "BASSE"
            subject = f"🚨 ALERTE TEMPÉRATURE {alert_type} - {temperature:.1f}°C - ColdChain"
            
            # Message texte simple
            text_message = f"""
            ===========================================
            🚨 ALERTE SYSTÈME COLDCHAIN 🚨
            ===========================================
            
            TYPE D'ALERTE: Température {alert_type}
            
            📊 DONNÉES ACTUELLES:
            • Température: {temperature:.1f}°C
            • Humidité: {humidity:.1f}%
            • Heure: {timestamp.strftime('%d/%m/%Y à %H:%M:%S')}
            
            ⚠️ SEUIL DÉPASSÉ:
            • Seuil {'maximum' if is_high else 'minimum'}: {settings.ALERT_TEMP_HIGH if is_high else settings.ALERT_TEMP_LOW}°C
            • Écart: {abs(temperature - (settings.ALERT_TEMP_HIGH if is_high else settings.ALERT_TEMP_LOW)):.1f}°C {'au-dessus' if is_high else 'en-dessous'}
            
            📈 PLAGE NORMALE:
            • Min: {settings.ALERT_TEMP_LOW}°C
            • Max: {settings.ALERT_TEMP_HIGH}°C
            
            🚑 ACTION REQUISE:
            • Vérifier immédiatement l'équipement
            • Contrôler la chaîne de froid
            • Documenter l'incident
            
            ===========================================
            Cet email est envoyé automatiquement.
            ===========================================
            """
            
            # Destinataires
            recipient_list = [self.admin_email, self.operator_email]
            
            # Envoyer l'email
            send_mail(
                subject=subject,
                message=text_message,
                from_email=self.from_email,
                recipient_list=recipient_list,
                fail_silently=False,
            )
            
            logger.info(f"Email alert sent to {recipient_list} - Temp: {temperature}°C")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}", exc_info=True)
            return False
    
    def send_incident_created(self, incident):
        """Envoyer un email de création d'incident"""
        if not self.enabled:
            return False
        
        try:
            subject = f"📋 Incident #{incident.id} Créé - ColdChain"
            
            text_message = f"""
            ===========================================
            📋 NOUVEL INCIDENT SIGNALÉ
            ===========================================
            
            ID Incident: #{incident.id}
            Statut: {incident.statut.upper()}
            
            📊 DONNÉES MESURÉES:
            • Température: {incident.dht.temp:.1f}°C
            • Humidité: {incident.dht.humidity:.1f}%
            • Heure mesure: {incident.dht.dt.strftime('%d/%m/%Y %H:%M:%S')}
            
            👤 CRÉÉ PAR:
            • Utilisateur: {incident.created_by.username if incident.created_by else 'Système'}
            • Date création: {incident.dt_creation.strftime('%d/%m/%Y %H:%M:%S')}
            
            📝 COMMENTAIRE:
            • {incident.commentaire or 'Aucun commentaire'}
            
            ===========================================
            Veuillez traiter cet incident dans le dashboard.
            ===========================================
            """
            
            send_mail(
                subject=subject,
                message=text_message,
                from_email=self.from_email,
                recipient_list=[self.admin_email, self.operator_email],
                fail_silently=False,
            )
            
            logger.info(f"Incident creation email sent for incident #{incident.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send incident email: {e}")
            return False
    
    def send_incident_resolved(self, incident, resolved_by):
        """Envoyer un email de résolution d'incident"""
        if not self.enabled:
            return False
        
        try:
            subject = f"✅ Incident #{incident.id} Résolu - ColdChain"
            
            text_message = f"""
            ===========================================
            ✅ INCIDENT RÉSOLU
            ===========================================
            
            ID Incident: #{incident.id}
            Statut: {incident.statut.upper()}
            
            📊 DONNÉES ORIGINALES:
            • Température: {incident.dht.temp:.1f}°C
            • Heure: {incident.dht.dt.strftime('%d/%m/%Y %H:%M:%S')}
            
            👤 RÉSOLU PAR:
            • Utilisateur: {resolved_by.username if resolved_by else 'Système'}
            • Date résolution: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            
            💬 COMMENTAIRE:
            • {incident.commentaire or 'Aucun commentaire'}
            
            ===========================================
            L'incident a été marqué comme résolu.
            ===========================================
            """
            
            send_mail(
                subject=subject,
                message=text_message,
                from_email=self.from_email,
                recipient_list=[self.admin_email, self.operator_email],
                fail_silently=False,
            )
            
            logger.info(f"Incident resolution email sent for incident #{incident.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send resolution email: {e}")
            return False

class AsyncEmailSender:
    """Envoi d'emails asynchrone pour ne pas bloquer l'interface"""
    
    @staticmethod
    def send_temperature_alert_async(temperature, humidity, timestamp, is_high=True):
        """Envoyer une alerte email de manière asynchrone"""
        def send():
            try:
                notifier = EmailNotificationSystem()
                notifier.send_temperature_alert(
                    temperature=temperature,
                    humidity=humidity,
                    timestamp=timestamp,
                    is_high=is_high
                )
            except Exception as e:
                logger.error(f"Erreur email async: {e}")
        
        thread = threading.Thread(target=send)
        thread.daemon = True
        thread.start()
        logger.info(f"Thread email démarré pour température: {temperature}°C")
    
    @staticmethod
    def send_incident_email_async(incident, email_type='created'):
        """Envoyer un email d'incident de manière asynchrone"""
        def send():
            try:
                notifier = EmailNotificationSystem()
                if email_type == 'created':
                    notifier.send_incident_created(incident)
                elif email_type == 'resolved':
                    notifier.send_incident_resolved(incident, incident.created_by)
            except Exception as e:
                logger.error(f"Erreur email incident async: {e}")
        
        thread = threading.Thread(target=send)
        thread.daemon = True
        thread.start()
        logger.info(f"Thread email démarré pour incident #{incident.id}")