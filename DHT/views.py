import json

from django.contrib import messages

from .models import Dht11

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import send_telegram, send_email, send_alert_view
from django.shortcuts import redirect
from django.http import HttpResponse

from .models import Dht11

# Dashboard
def dashboard(request):
    return render(request, "DHT/dashboard.html")

# Graph pages
def graph_temp(request):
    return render(request, "DHT/graph_temp.html")

def graph_hum(request):
    return render(request, "DHT/graph_hum.html")

# Latest reading
def latest_data(request):
    last = Dht11.objects.last()
    return JsonResponse({
        "temperature": last.temp,
        "humidity": last.hum,
        "timestamp": last.dt.isoformat()
    })

# Last 30 readings
def history_data(request):
    data = Dht11.objects.all().order_by('-id')[:30]
    history = [{
        "dt": d.dt.isoformat(),
        "temp": d.temp,
        "hum": d.hum
    } for d in reversed(data)]
    return JsonResponse({"history": history})

@csrf_exempt
def api_add_dht(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            temp = data.get("temp")
            hum = data.get("hum")

            Dht11.objects.create(
                temp=temp,
                hum=hum
            )

            return JsonResponse({"status": "success"}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "POST only"}, status=405)

def send_email_alert(request):
    latest = Dht11.objects.order_by('-dt').first()
    if latest:
        message_text = (
            f"Alerte : la température a atteint {latest.temp:.1f}°C et l’humidité {latest.hum:.1f}% le "
            f"{latest.dt.strftime('%d/%m/%Y %H:%M:%S')}.\n\n"
            "Veuillez vérifier le capteur DHT11.\n\n"
            "Ça fonctionne, je suis Tagmouti Fatima Zahra, GI5C !"
        )
        send_email("Alerte DHT11", message_text, recipient_list=["rahimasaoudi65@gmail.com"])
        messages.success(request, "Email envoyé avec succès !")
    else:
        messages.error(request, "Aucune donnée disponible.")
    return redirect('dashboard')  # Redirige vers la page dashboard

def send_telegram_alert(request):
    latest = Dht11.objects.order_by('-dt').first()
    if latest:
        message_text = (
            f"Alerte : la température a atteint {latest.temp:.1f}°C et l’humidité {latest.hum:.1f}% le "
            f"{latest.dt.strftime('%d/%m/%Y %H:%M:%S')}.\n\n"
            "Veuillez vérifier le capteur DHT11.\n\n"
            "Ça fonctionne, je suis Tagmouti Fatima Zahra, GI5C !"
        )
        send_telegram(message_text)
        messages.success(request, "Telegram envoyé avec succès !")
    else:
        messages.error(request, "Aucune donnée disponible.")
    return redirect('dashboard')
