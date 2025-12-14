from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model

from .models import Ticket, AuditLog

User = get_user_model()

# ----------------------------------------------------
# 📋 LISTE DES INCIDENTS
# ----------------------------------------------------
@login_required
def tickets_list(request):
    tickets = Ticket.objects.all().order_by('-created_at')
    return render(request, 'DHT/tickets_list.html', {'tickets': tickets})


# ----------------------------------------------------
# 🔎 DETAIL D’UN INCIDENT
# ----------------------------------------------------
@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    if request.method == "POST":  
        old = ticket.status
        new = request.POST.get("status")

        ticket.status = new
        ticket.save()

        AuditLog.objects.create(
            user=request.user,
            action=f"Changement statut ticket #{ticket.id}: {old} → {new}"
        )

        messages.success(request, "Statut mis à jour.")
        return redirect('ticket_detail', ticket_id=ticket.id)

    return render(request, 'DHT/ticket_detail.html', {'ticket': ticket})


# ----------------------------------------------------
# 👤 ASSIGNATION D’UN INCIDENT
# ----------------------------------------------------
@login_required
def ticket_assign(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    # 🔹 Assignation simple : assigner le ticket à l'utilisateur connecté
    ticket.assigned_to = request.user
    ticket.status = "in_progress"
    ticket.save()

    AuditLog.objects.create(
        user=request.user,
        action=f"Ticket #{ticket.id} assigné à {request.user.username}"
    )

    messages.success(request, "Ticket assigné.")
    return redirect('ticket_detail', ticket_id=ticket.id)


# ----------------------------------------------------
# ✅ CLÔTURE D’UN TICKET
# ----------------------------------------------------
@login_required
def ticket_close(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    ticket.status = "closed"
    ticket.save()

    AuditLog.objects.create(
        user=request.user,
        action=f"Ticket #{ticket.id} clôturé."
    )

    messages.success(request, "Ticket clôturé.")
    return redirect('tickets_list')
