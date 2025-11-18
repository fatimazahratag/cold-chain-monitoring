from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from django.conf import settings
from django.utils.timezone import localtime
from .models import Dht11
import requests

# ---------- API pour récupérer toutes les données ----------
def Dlist(request):
    """Récupère toutes les données DHT11 au format JSON"""
    all_data = Dht11.objects.all().values('temp', 'hum', 'dt')
    return JsonResponse({'data': list(all_data)})


# ---------- API pour ajouter une nouvelle mesure ----------
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import DHT11serialize

class DhtAddView(APIView):
    """Ajout d'une nouvelle mesure DHT11 via API POST"""
    def post(self, request):
        temp = request.data.get("temp")
        hum = request.data.get("hum")

        if temp is None or hum is None:
            return Response({"error": "Données manquantes"}, status=status.HTTP_400_BAD_REQUEST)

        dht = Dht11.objects.create(temp=temp, hum=hum)

        return Response({
            "id": dht.id,
            "temp": dht.temp,
            "hum": dht.hum,
            "dt": dht.dt
        }, status=status.HTTP_201_CREATED)


# ---------- Telegram helper ----------
def send_telegram(message):
    TOKEN = "8538031795:AAGPedXC6RA3k10hHt0PUh5edap9VM1Zats"
    CHAT_ID = "1151333491"  # <-- ton chat_id
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Erreur Telegram:", e)


# ---------- API pour envoyer un email et Telegram d'alerte ----------
def send_email_alert(request):
    """Envoie un email + Telegram si la température dépasse un seuil"""
    last = Dht11.objects.order_by('-dt').first()
    if not last:
        return HttpResponse("Aucune donnée disponible")

    SEUIL_TEMP = 23  # seuil pour test
    if last.temp >= SEUIL_TEMP:
        temp = last.temp
        hum = last.hum
        dt_str = localtime(last.dt).strftime("%d/%m/%Y %H:%M:%S")

        # Message Email
        sujet = "🚨 Alerte DHT11"
        message_email = (
            f"Alerte : la température a atteint {temp:.1f}°C "
            f"et l’humidité {hum:.1f}% le {dt_str}.\n\n"
            f"Veuillez vérifier le capteur DHT11.\n"
            f"Ça fonctionne, je suis Tagmouti Fatima Zahra, GI5C !"
        )

        # Envoi Email
        try:
            send_mail(
                subject=sujet,
                message=message_email,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=["rahimasaoudi65@gmail.com"],  # change si besoin
                fail_silently=False,
            )
        except Exception as e:
            return HttpResponse(f"❌ Erreur lors de l’envoi de l’email : {e}")

        # Message Telegram
        message_telegram = f"🚨 Alerte DHT11!\nTempérature: {temp}°C\nHumidité: {hum}%\nHeure: {dt_str}"
        send_telegram(message_telegram)

        return HttpResponse("✅ Email et Telegram d’alerte envoyés avec succès !")
    else:
        return HttpResponse(f"Aucune alerte : température actuelle = {last.temp}°C")


# ---------- API pour envoyer un email de test ----------
def send_test_email(request):
    """Envoi d’un email simple de test"""
    send_mail(
        subject='Sujet de test',
        message='Ceci est un email de test envoyé depuis Django.',
        from_email='tagmoutifatimazahra08@gmail.com',
        recipient_list=['rahimasaoudi65@gmail.com'],
        fail_silently=False,
    )
    return HttpResponse("📧 Email de test envoyé avec succès !")
