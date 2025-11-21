from django.core.mail import send_mail
from django.conf import settings
import requests
from datetime import datetime

from django.test import Client


def send_telegram(text: str) -> bool:
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": chat_id, "text": text})
        return r.ok
    except Exception:
        return False

def send_email(subject: str, message: str, recipient_list=None) -> bool:
    if recipient_list is None:
        recipient_list = [settings.EMAIL_HOST_USER]
    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list, fail_silently=False)
        return True
    except Exception as e:
        print("Email send error:", e)
        return False

def send_alert_view(temp: float, hum: float, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now()
    ts_str = timestamp.strftime("%d/%m/%Y %H:%M:%S")
    message = (
        f"Alerte : la température a atteint {temp:.1f}°C et l’humidité {hum:.1f}% le {ts_str}.\n\n"
        "Veuillez vérifier le capteur DHT11.\n\n"
        "Ça fonctionne, je suis Tagmouti Fatima Zahra, GI5C !"
    )
    recipient_email = "rahimasaoudi65@gmail.com"  # email spécifique
    send_email("Alerte DHT11", message, recipient_list=[recipient_email])
    send_telegram(message)



def send_whatsapp(message: str) -> bool:
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            body=message,
            to=settings.MY_WHATSAPP_NUMBER
        )
        return True
    except Exception as e:
        print("Erreur WhatsApp:", e)
        return False
