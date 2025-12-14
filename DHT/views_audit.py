from django.shortcuts import render
from .models import AuditLog

def audit_log_list(request):
    logs = AuditLog.objects.all().order_by('-timestamp')
    return render(request, "DHT/audit_list.html", {"logs": logs})
