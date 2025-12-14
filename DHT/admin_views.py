from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Ticket, Dht11, Sensor, AuditLog, CustomUser, Comment
from django.http import HttpResponse
import csv
from django.contrib.auth.decorators import login_required, user_passes_test

# =========================================================
# ADMIN DASHBOARD
# =========================================================
@staff_member_required(login_url='/admin/login/')
def admin_dashboard(request):
    # Stats générales
    total_incidents = Ticket.objects.count()
    open_incidents = Ticket.objects.filter(status="open").count()
    sensors_count = Sensor.objects.count()

    # Derniers tickets et commentaires
    last_incidents = Ticket.objects.order_by("-created_at")[:8]
    recent_audit = AuditLog.objects.order_by("-timestamp")[:8]

    # Dernière mesure
    last_measure = Dht11.objects.order_by("-dt").first()

    context = {
        "total_incidents": total_incidents,
        "open_incidents": open_incidents,
        "last_incidents": last_incidents,
        "last_measure": last_measure,
        "sensors_count": sensors_count,
        "recent_audit": recent_audit,
    }
    return render(request, "admin/custom_dashboard.html", context)

# =========================================================
# EXPORT INCIDENTS CSV
# =========================================================
@staff_member_required
def export_incidents_csv(request):
    qs = Ticket.objects.order_by("-created_at")
    r = HttpResponse(content_type="text/csv")
    r["Content-Disposition"] = "attachment; filename=incidents.csv"
    writer = csv.writer(r)

    writer.writerow([
        "id", "type", "sensor", "temp", "hum", "status",
        "assigned_to", "created_at", "description"
    ])

    for t in qs:
        writer.writerow([
            t.id,
            t.get_incident_type_display(),
            t.sensor.name if t.sensor else "N/A",
            t.temp,
            t.hum,
            t.status,
            t.assigned_to.username if t.assigned_to else "",
            t.created_at.isoformat(),
            t.description or ""
        ])
    return r

# =========================================================
# ASSIGN TICKET TO OPERATOR
# =========================================================
@staff_member_required
def assign_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    operators = CustomUser.objects.filter(role='operator')

    if request.method == "POST":
        operator_id = request.POST.get("operator_id")
        operator = get_object_or_404(CustomUser, id=operator_id)
        ticket.assigned_to = operator
        ticket.save()

        # Log action
        AuditLog.objects.create(
            user=request.user,
            action=f"Assigned ticket {ticket.id} to {operator.username}"
        )
        messages.success(request, f"Ticket {ticket.id} assigné à {operator.username}")
        return redirect("admin_dashboard")

    context = {
        "ticket": ticket,
        "operators": operators
    }
    return render(request, "admin/assign_ticket.html", context)

# =========================================================
# ADD COMMENT TO TICKET
# =========================================================
@staff_member_required
def add_comment(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if request.method == "POST":
        content = request.POST.get("content")
        if content:
            Comment.objects.create(
                user=request.user,
                content=content
            )
            AuditLog.objects.create(
                user=request.user,
                action=f"Added comment to ticket {ticket.id}"
            )
            messages.success(request, "Commentaire ajouté avec succès")
        return redirect("admin_dashboard")

    context = {
        "ticket": ticket
    }
    return render(request, "admin/add_comment.html", context)
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import CustomUser, AuditLog

@staff_member_required(login_url='/admin/login/')
def add_operator(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if username and email and password:
            operator = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='operator',
                is_staff=True
            )
            AuditLog.objects.create(
                user=request.user,
                action=f"Added operator {username}"
            )
            messages.success(request, f"Opérateur {username} ajouté avec succès")
            return redirect('admin_custom_dashboard')

    return render(request, "admin/add_operator.html")
@staff_member_required(login_url='/admin/login/')
def list_operators(request):
    operators = CustomUser.objects.filter(role='operator')
    context = {
        'operators': operators
    }
    return render(request, 'admin/list_operators.html', context)

# admin_views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import CustomUser

def edit_operator(request, user_id):
    operator = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == "POST":
        operator.username = request.POST.get("username")
        operator.email = request.POST.get("email")
        # Si tu veux gérer le password
        password = request.POST.get("password")
        if password:
            operator.set_password(password)
        operator.save()
        messages.success(request, f"Opérateur {operator.username} mis à jour !")
        return redirect("list_operators")

    context = {"operator": operator}
    return render(request, "admin/edit_operator.html", context)

