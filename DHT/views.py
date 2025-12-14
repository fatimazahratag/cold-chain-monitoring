import json
from django.core.exceptions import PermissionDenied
def admin_only(view_func):
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped

from django import forms
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.core.mail import send_mail
from DHT.views_tickets import User
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render, redirect
from .models import Alert, CustomUser, Ticket, Threshold, Dht11
from django.utils import timezone
from .models import (
    Dht11, Ticket, Sensor, Threshold, AuditLog
)
from .serializers import TicketSerializer

# ───────────────────────────────
# 🔥 UTILITIES
# ───────────────────────────────
from .utils import send_telegram, send_whatsapp, send_email

from DHT.models import Seuil, Comment, Dht11, Ticket
@admin_only
def dashboard_incidents(request):
    last = Dht11.objects.order_by('-dt').first()
    last_incident = Ticket.objects.order_by('-created_at').first()
    total_incidents = Ticket.objects.count()

    # Récupérer le dernier seuil créé
    seuil = Seuil.objects.order_by('-created_at').first()
    temp_min = seuil.temp_min if seuil else None
    temp_max = seuil.temp_max if seuil else None

    if request.method == "POST":
        Comment.objects.create(
            user=request.user,
            content=request.POST.get("comment")
        )

    comments = Comment.objects.order_by("-created_at")[:5]

    return render(request, "DHT/dashboard_incidents.html", {
        "last": last,
        "last_incident": last_incident,
        "total_incidents": total_incidents,
        "temp_min": temp_min,
        "temp_max": temp_max,
        "comments": comments,
    })

# -----------------------------------------------------
# 🔥 FONCTION GÉNÉRALE : CRÉER UN INCIDENT AUTOMATIQUE
# -----------------------------------------------------
@admin_only
def create_incident(sensor, incident_type, temp=None, hum=None, description=""):
    ticket = Ticket.objects.create(
        sensor=sensor,
        incident_type=incident_type,
        temp=temp,
        hum=hum,
        description=description,
    )

    # Audit Log
    AuditLog.objects.create(
        action=f"Création automatique incident #{ticket.id} type {incident_type}"
    )

    return ticket

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


# -----------------------------------------------------
# 🔥 DASHBOARD
# -----------------------------------------------------
def dashboard(request):
    open_incidents = Ticket.objects.filter(status="open").count()
    return render(request, "DHT/dashboard.html", {
        "open_incidents": open_incidents
    })


# ───────────────────────────────
# 🔥 GRAPHIQUES
# ───────────────────────────────
def graph_temp(request):
    return render(request, "DHT/graph_temp.html")


def graph_hum(request):
    return render(request, "DHT/graph_hum.html")


# ───────────────────────────────
# 🔥 API LAST DATA
# ───────────────────────────────
def latest_data(request):
    last = Dht11.objects.order_by('-dt').first()

    if not last:
        return JsonResponse({"error": "Aucune donnée trouvée"}, status=404)

    return JsonResponse({
        "temperature": last.temp,
        "humidity": last.hum,
        "timestamp": last.dt.isoformat(),
        "sensor": last.sensor.name if last.sensor else "Aucun capteur",
    })


# ───────────────────────────────
# 🔥 API HISTORY
# ───────────────────────────────
def history_data(request):
    data = Dht11.objects.all().order_by('-id')[:30]
    history = [{
        "dt": d.dt.isoformat(),
        "temp": d.temp,
        "hum": d.hum
    } for d in reversed(data)]
    return JsonResponse({"history": history})


# ───────────────────────────────
# 🔥 API ESP8266 — ADD DATA + INCIDENT AUTOMATIQUE
# ───────────────────────────────
@csrf_exempt
@csrf_exempt
def api_add_dht(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=400)

    data = json.loads(request.body)

    temp = data.get("temp")
    hum = data.get("hum")

    sensor = Sensor.objects.first()  # peut être None

    dht = Dht11.objects.create(
        temp=temp,
        hum=hum,
        sensor=sensor
    )
def operator_alerts(request):
    alerts = Alert.objects.filter(
        operator=request.user
    ).order_by("-created_at")

    return render(request, "DHT/operator_alerts.html", {
        "alerts": alerts
    })
def mark_alert_read(request, alert_id):
    alert = Alert.objects.get(id=alert_id, operator=request.user)
    alert.is_read = True
    alert.save()

    AuditLog.objects.create(
        user=request.user,
        action=f"Alerte {alert.counter_value} lue"
    )

    return redirect("operator_alerts")

    # ----- Vérification seuil -----
    if sensor:
        thresholds = Threshold.objects.filter(sensor=sensor).first()

        if thresholds:
            if temp > thresholds.temp_max:
                create_incident(sensor, "temp_high", temp, hum, "Température dépasse le seuil.")

            elif temp < thresholds.temp_min:
                create_incident(sensor, "temp_low", temp, hum, "Température trop basse.")

            if hum > thresholds.hum_max:
                create_incident(sensor, "hum_high", temp, hum, "Humidité dépasse le seuil.")

            elif hum < thresholds.hum_min:
                create_incident(sensor, "hum_low", temp, hum, "Humidité trop faible.")

    return JsonResponse({"status": "ok", "id": dht.id})

# ───────────────────────────────
# 🔥 ALERTE EMAIL MANUELLE
# ───────────────────────────────
def send_email_alert(request):
    last = Dht11.objects.order_by('-dt').first()
    if not last:
        return HttpResponse("Aucune donnée disponible")

    subject = "🚨 Alerte DHT11"
    msg = f"Temp : {last.temp}°C\nHumidité : {last.hum}%"

    send_mail(subject, msg, settings.EMAIL_HOST_USER, ["rahimasaoudi65@gmail.com"])
    send_telegram("🚨 ALERTE envoyée !")

    return HttpResponse("Email envoyé + Telegram envoyé + Incident créé")


# ───────────────────────────────
# 🔥 TICKETS – LISTE
# ───────────────────────────────
@admin_only
def incidents_list(request):
    incidents = Ticket.objects.order_by('-created_at')  # rename tickets -> incidents
    return render(request, "DHT/incidents_list.html", {"incidents": incidents})
@admin_only
def audit_logs(request):
    logs = AuditLog.objects.order_by('-timestamp')
    return render(request, "DHT/audit_logs.html", {"logs": logs})

# ───────────────────────────────
# 🔥 TICKET DETAIL + UPDATE STATUS
# ───────────────────────────────
@admin_only
def incident_detail_modal(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    return render(request, "DHT/incident_detail_modal.html", {
        "ticket": ticket
    })
@admin_only
def incident_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if request.method == "POST":
        old_status = ticket.status
        new_status = request.POST.get("status")

        ticket.status = new_status
        ticket.save()

        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action=f"Ticket #{ticket.id} : {old_status} → {new_status}"
        )

        return redirect("incident_detail", ticket_id)

    return render(request, "DHT/incident_detail.html", {"ticket": ticket})

from django.http import JsonResponse
@admin_only
def assign_ticket_ajax(request, ticket_id):
    ticket = Ticket.objects.get(id=ticket_id)
    ticket.assigned_to = request.user
    ticket.status = "in_progress"
    ticket.save()

    return JsonResponse({
        "status": "ok",
        "new_status": "in_progress"
    })
@admin_only
def close_ticket_ajax(request, ticket_id):
    ticket = Ticket.objects.get(id=ticket_id)
    ticket.status = "closed"
    ticket.save()

    return JsonResponse({
        "status": "ok",
        "new_status": "closed"
    })

# ───────────────────────────────
# 🔥 ASSIGNATION
# ───────────────────────────────
@admin_only
def assign_ticket(request, ticket_id):
    ticket = Ticket.objects.get(id=ticket_id)
    user = request.user

    ticket.assigned_to = user
    ticket.status = "in_progress"
    ticket.save()

    AuditLog.objects.create(
        user=user,
        action=f"Ticket #{ticket.id} assigné."
    )

    return redirect("dashboard_incidents")


# ───────────────────────────────
# 🔥 CLÔTURE TICKET
# ───────────────────────────────
@admin_only
def close_ticket(request, ticket_id):
    ticket = Ticket.objects.get(id=ticket_id)
    ticket.status = "closed"
    ticket.save()

    AuditLog.objects.create(
        user=request.user,
        action=f"Ticket #{ticket.id} clôturé."
    )

    return redirect("dashboard_incidents")


# ───────────────────────────────
# 🔥 API REST – LISTE TICKETS
# ───────────────────────────────
class TicketListView(APIView):
    def get(self, request):
        tickets = Ticket.objects.order_by("-created_at")
        serializer = TicketSerializer(tickets, many=True)
        return Response(serializer.data)


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # if staff (admin) go to admin custom dashboard
            if user.is_active and user.is_staff:
                return redirect(reverse("admin_custom_dashboard"))
            # regular logged-in users -> app dashboard
            return redirect(reverse("dashboard"))
        else:
            messages.error(request, "Nom d’utilisateur ou mot de passe invalide.")
    return render(request, "login.html")


def incidents_list_view(request):
    incidents = Ticket.objects.all().order_by('-created_at')
    return render(request, "DHT/incidents_list.html", {"incidents": incidents})

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
@admin_only
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès !")
            return redirect('dashboard')
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'DHT/profile_edit.html', {'form': form})
def home(request):
    return render(request, 'home.html')
from django.contrib.auth.decorators import login_required, user_passes_test

def operator_required(view_func):
    return user_passes_test(lambda u: u.is_active and u.role=='operator', login_url='/admin/login/')(view_func)

@operator_required
def operator_dashboard(request):
    tickets = request.user.assigned_tickets.all()  # tickets assignés
    return render(request, 'operator/dashboard.html', {'tickets': tickets})

@login_required
def redirect_dashboard(request):
    if request.user.is_superuser:
        return redirect('admin_custom_dashboard')  # custom admin dashboard
    elif request.user.role == 'operator':
        return redirect('operator_dashboard')  # custom operator dashboard
    else:
        return redirect('logout')  # sécurité
from .models import Comment

# def dashboard_incidents(request):
#     last = Dht11.objects.order_by('-dt').first()
#     last_incident = Ticket.objects.order_by('-created_at').first()
#     total_incidents = Ticket.objects.count()

#     if request.method == "POST":
#         Comment.objects.create(
#             user=request.user,
#             content=request.POST.get("comment")
#         )

#     comments = Comment.objects.order_by("-created_at")[:5]

#     return render(request, "DHT/dashboard_incidents.html", {
#         "last": last,
#         "last_incident": last_incident,
#         "total_incidents": total_incidents,
#         "comments": comments,
#     })
def send_alert_by_counter(counter_value):
    operator = CustomUser.objects.filter(
        role="operator"
    ).order_by("id").first()

    operators = list(CustomUser.objects.filter(role="operator").order_by("id"))

    if counter_value <= len(operators):
        operator = operators[counter_value - 1]

        Alert.objects.create(
            operator=operator,
            counter_value=counter_value,
            message=f"Alerte niveau {counter_value} – température hors seuil"
        )
# views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import Ticket, Comment

def open_operator_dashboard(request):
    operator_name = request.GET.get('name', '').strip()  # récupère le nom depuis le formulaire
    tickets = []

    if operator_name:
        # On filtre uniquement les tickets assignés à cet opérateur
        tickets = Ticket.objects.filter(assigned_to__username=operator_name).order_by('-created_at')

    if request.method == "POST":
        ticket_id = request.POST.get('ticket_id')
        content = request.POST.get('content')
        if ticket_id and content:
            ticket = get_object_or_404(Ticket, id=ticket_id)
            # On crée le commentaire avec le nom de l'opérateur
            Comment.objects.create(
                user_name=operator_name,
                content=content,
                ticket=ticket
            )
            # Redirection pour rafraîchir la page avec les tickets
            return redirect(f"{request.path}?name={operator_name}")

    return render(request, 'operator/operator_dashboard.html', {
        'tickets': tickets,
        'operator_name': operator_name
    })

from django.shortcuts import render, get_object_or_404, redirect
from .models import Ticket, Comment

def open_operator_dashboard(request):
    name = request.GET.get('name', '').strip()
    tickets = []

    if name:
        tickets = Ticket.objects.filter(
            assigned_to__username__iexact=name
        ).order_by('-created_at')

    return render(request, 'operator/operator_dashboard.html', {
        'tickets': tickets,
        'operator_name': name
    })
from django.shortcuts import render, get_object_or_404, redirect
from .models import Ticket, Comment

def operator_dashboard(request):
    # Récupère le nom de l'opérateur depuis le formulaire GET
    operator_name = request.GET.get('name', '').strip()
    tickets = Ticket.objects.filter(assigned_to__username__iexact=operator_name).order_by('-created_at') if operator_name else []

    # ----- POST : ajouter un commentaire ou changer le statut -----
    if request.method == 'POST':
        ticket_id = request.POST.get('ticket_id')
        content = request.POST.get('content')
        new_status = request.POST.get('status')

        if ticket_id:
            try:
                ticket = Ticket.objects.get(id=int(ticket_id))
            except Ticket.DoesNotExist:
                ticket = None

            if ticket:
                # 🔹 Ajouter un commentaire
                if content:
                    Comment.objects.create(
                        ticket=ticket,
                        user_name=operator_name,
                        content=content
                    )

                # 🔹 Mettre à jour le statut
                if new_status and new_status != ticket.status:
                    ticket.status = new_status
                    ticket.save()

        # Redirige pour que la page se recharge avec GET
        return redirect(f'{request.path}?name={operator_name}')

    # ----- GET : afficher les tickets -----
    return render(request, 'operator/operator_dashboard.html', {
        'tickets': tickets,
        'operator_name': operator_name
    })
