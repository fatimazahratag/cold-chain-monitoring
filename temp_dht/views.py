from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.utils.timezone import localtime
from django.http import JsonResponse, HttpResponse
from django.db.models import Avg, Count, Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
import csv
from datetime import datetime, timedelta
from django.conf import settings

from DHT.models import Dht11, Incident, SystemLog
from DHT.utils import (
    log_temperature_alert, 
    log_humidity_alert, 
    log_incident_created,
    log_incident_resolved,
    log_user_activity,
    log_system_start,
    log_data_received
)

# Import pour les emails
from DHT.email_notifications import EmailNotificationSystem, AsyncEmailSender

# ========== DÉCORATEURS PERSONNALISÉS ==========

def superuser_required(view_func):
    """Décorateur pour exiger un superuser (admin)"""
    decorated_view_func = user_passes_test(
        lambda u: u.is_active and u.is_superuser,
        login_url='operator_dashboard',
        redirect_field_name=None
    )(view_func)
    return decorated_view_func

def staff_or_superuser_required(view_func):
    """Décorateur pour staff (opérateur) OU superuser (admin)"""
    decorated_view_func = user_passes_test(
        lambda u: u.is_active and (u.is_staff or u.is_superuser),
        login_url='home',
        redirect_field_name=None
    )(view_func)
    return decorated_view_func

# ========== VUES D'AUTHENTIFICATION ==========

def login_view(request):
    """Vue de connexion"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Loguer la connexion
            log_user_activity(f"s'est connecté", user)
            
            # CORRECTION : Redirection selon le type d'utilisateur
            if user.is_superuser:  # Uniquement superuser pour admin
                return redirect('admin_dashboard')
            else:  # Tous les autres (staff et normaux) vers opérateur
                return redirect('operator_dashboard')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect')
    
    return render(request, 'DHT/login.html')

@login_required
def logout_view(request):
    """Vue de déconnexion"""
    user = request.user
    # Loguer la déconnexion
    log_user_activity(f"s'est déconnecté", user)
    
    logout(request)
    return redirect('home')

# ========== VUES PUBLIQUES ==========

def home(request):
    """Page publique d'accueil"""
    last_data = Dht11.objects.order_by('-dt').first()
    context = {
        "temperature": last_data.temp if last_data else None,
        "humidity": last_data.humidity if last_data else None,
        "date": localtime(last_data.dt) if last_data else None
    }
    return render(request, "DHT/home.html", context)

@login_required
def dashboard(request):
    """Redirection vers le dashboard approprié"""
    user = request.user
    # CORRECTION : Distinguer mieux admin et opérateur
    if user.is_superuser:  # Uniquement superuser pour admin
        return redirect('admin_dashboard')
    else:  # Tous les autres (staff et normaux) vers opérateur
        return redirect('operator_dashboard')

# ========== API ==========

@login_required
def latest_data(request):
    """API dernier relevé"""
    last_data = Dht11.objects.order_by('-dt').first()
    if last_data:
        data = {
            "temp": last_data.temp,
            "humidity": last_data.humidity,
            "dt": localtime(last_data.dt).isoformat(),
        }
        # Loguer la récupération de données
        log_data_received(last_data.temp, last_data.humidity)
    else:
        data = {"temp": None, "humidity": None, "dt": None}
    return JsonResponse(data)

# ========== EXPORT CSV ==========

@login_required
@staff_or_superuser_required
def export_logs_csv(request):
    """Exporter les logs en CSV"""
    # Récupérer tous les logs
    logs = SystemLog.objects.all().order_by('-created_at')
    
    # Créer la réponse HTTP avec le type CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    filename = f'logs_systeme_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Créer le writer CSV
    writer = csv.writer(response, delimiter=';')
    
    # Écrire l'en-tête
    writer.writerow([
        'Date', 'Heure', 'Niveau', 'Catégorie', 'Message', 
        'Détails', 'Utilisateur'
    ])
    
    # Écrire les données
    for log in logs:
        writer.writerow([
            log.created_at.strftime("%d/%m/%Y"),
            log.created_at.strftime("%H:%M:%S"),
            log.get_level_display(),
            log.get_category_display(),
            log.message,
            log.details or '',
            log.user.username if log.user else ''
        ])
    
    # Loguer l'export
    log_user_activity(f"a exporté les logs système", request.user)
    
    return response

@login_required
@staff_or_superuser_required
def export_incidents_csv(request):
    """Exporter les incidents en CSV"""
    incidents = Incident.objects.all().order_by('-dt_creation')
    
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    filename = f'incidents_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response, delimiter=';')
    
    # Écrire l'en-tête
    writer.writerow([
        'ID', 'Statut', 'Date création', 'Température (°C)', 'Humidité (%)',
        'Date mesure', 'Créé par', 'Cause', 'Commentaire', 'Accusé réception'
    ])
    
    # Écrire les données
    for incident in incidents:
        # Déterminer la cause
        if incident.dht.temp > settings.ALERT_TEMP_HIGH:
            cause = f'Température trop élevée (> {settings.ALERT_TEMP_HIGH}°C)'
        elif incident.dht.temp < settings.ALERT_TEMP_LOW:
            cause = f'Température trop basse (< {settings.ALERT_TEMP_LOW}°C)'
        else:
            cause = 'Anomalie détectée'
        
        writer.writerow([
            incident.id,
            incident.get_statut_display(),
            incident.dt_creation.strftime("%d/%m/%Y %H:%M:%S"),
            incident.dht.temp,
            incident.dht.humidity,
            incident.dht.dt.strftime("%d/%m/%Y %H:%M:%S"),
            incident.created_by.username if incident.created_by else 'Système',
            cause,
            incident.commentaire or '',
            'Oui' if incident.accuse_reception else 'Non'
        ])
    
    log_user_activity(f"a exporté les incidents", request.user)
    
    return response

# ========== FONCTION DE CRÉATION D'INCIDENTS ==========

def check_and_create_incidents(request):
    """Vérifier et créer des incidents automatiquement avec envoi d'emails"""
    incidents_created = []
    
    # Récupérer la dernière donnée
    last_data = Dht11.objects.order_by('-dt').first()
    
    if not last_data:
        return incidents_created
    
    # Vérifier si la température est problématique
    if last_data.temp < settings.ALERT_TEMP_LOW or last_data.temp > settings.ALERT_TEMP_HIGH:
        # Vérifier s'il n'existe pas déjà un incident pour cette donnée
        existing_incident = Incident.objects.filter(dht=last_data).exists()
        
        if not existing_incident:
            # Déterminer le type de problème
            if last_data.temp > settings.ALERT_TEMP_HIGH:
                problem_type = "Température trop élevée"
                threshold = f"> {settings.ALERT_TEMP_HIGH}°C"
                is_high = True
            else:
                problem_type = "Température trop basse"
                threshold = f"< {settings.ALERT_TEMP_LOW}°C"
                is_high = False
            
            # Créer l'incident
            incident = Incident.objects.create(
                dht=last_data,
                statut='ouvert',
                created_by=request.user if request.user.is_authenticated else None,
                commentaire=f"{problem_type}: {last_data.temp}°C (Seuil: {threshold})"
            )
            
            # Loguer
            log_incident_created(incident, request.user if request.user.is_authenticated else None)
            log_temperature_alert(last_data.temp)
            
            incidents_created.append(incident)
            
            # ENVOYER EMAIL AUTOMATIQUE EN ASYNCHRONE
            try:
                # 1. Envoyer l'alerte température (asynchrone)
                AsyncEmailSender.send_temperature_alert_async(
                    temperature=last_data.temp,
                    humidity=last_data.humidity,
                    timestamp=last_data.dt,
                    is_high=is_high
                )
                
                # 2. Envoyer l'email de création d'incident (asynchrone)
                AsyncEmailSender.send_incident_email_async(incident, 'created')
                
                # Message d'information
                messages.success(request, 
                    f"✅ Incident #{incident.id} créé : {problem_type} ({last_data.temp}°C)")
                messages.info(request, 
                    f"📧 Email envoyé à l'admin et l'opérateur")
                
            except Exception as e:
                # Loguer l'erreur mais continuer
                log_user_activity(f"Erreur envoi email: {str(e)}", 
                    request.user if request.user.is_authenticated else None)
                messages.warning(request, 
                    f"Incident créé mais erreur email: {e}")
    
    return incidents_created

@login_required
@staff_or_superuser_required
def test_email_view(request):
    """Interface pour tester les emails"""
    
    if request.method == 'POST':
        test_type = request.POST.get('test_type')
        temperature = float(request.POST.get('temperature', 9.5))
        
        notifier = EmailNotificationSystem()
        
        if test_type == 'high_temp':
            # Test température haute
            success = notifier.send_temperature_alert(
                temperature=temperature,
                humidity=65.2,
                timestamp=timezone.now(),
                is_high=True
            )
            message = f"Test température haute ({temperature}°C) envoyé !"
            
        elif test_type == 'low_temp':
            # Test température basse
            success = notifier.send_temperature_alert(
                temperature=temperature,
                humidity=70.5,
                timestamp=timezone.now(),
                is_high=False
            )
            message = f"Test température basse ({temperature}°C) envoyé !"
            
        elif test_type == 'incident':
            # Test création d'incident
            last_data = Dht11.objects.order_by('-dt').first()
            if last_data:
                incident = Incident.objects.create(
                    dht=last_data,
                    statut='ouvert',
                    created_by=request.user,
                    commentaire="Incident de test"
                )
                success = notifier.send_incident_created(incident)
                message = "Test incident créé envoyé !"
            else:
                success = False
                message = "Aucune donnée disponible pour créer un incident"
        
        if success:
            messages.success(request, f"✅ {message}")
        else:
            messages.error(request, f"❌ {message} - Vérifiez la configuration email")
        
        return redirect('test_email_view')
    
    # Vérifier la configuration email
    email_config = {
        'enabled': bool(settings.EMAIL_HOST_USER),
        'host': settings.EMAIL_HOST,
        'port': settings.EMAIL_PORT,
        'admin_email': settings.ALERT_EMAIL_ADMIN,
        'operator_email': settings.ALERT_EMAIL_OPERATOR,
        'from_email': settings.DEFAULT_FROM_EMAIL,
    }
    
    context = {
        'email_config': email_config,
        'temp_high': settings.ALERT_TEMP_HIGH,
        'temp_low': settings.ALERT_TEMP_LOW,
        'user': request.user,
    }
    
    return render(request, 'DHT/test_email.html', context)

# ========== DASHBOARD OPÉRATEUR ==========

@login_required
def operator_dashboard(request):
    """Dashboard opérateur : dernière lecture, incidents, graphique avec filtre dynamique"""

    # Dernière lecture
    last_data = Dht11.objects.order_by('-dt').first()
    if not last_data:
        last_data = Dht11(temp=0, humidity=0, dt=timezone.now())

    # Filtre GET
    filter_option = request.GET.get('filter', 'today')
    now = timezone.now()

    # Calcul mois dernier
    last_month = now.month - 1 if now.month > 1 else 12
    last_month_year = now.year if now.month > 1 else now.year - 1

    # Filtrage des données
    if filter_option == 'today':
        recent_data = Dht11.objects.filter(dt__date=now.date()).order_by('dt')
    elif filter_option == 'month':
        recent_data = Dht11.objects.filter(dt__year=now.year, dt__month=now.month).order_by('dt')
    elif filter_option == 'last_month':
        recent_data = Dht11.objects.filter(dt__year=last_month_year, dt__month=last_month).order_by('dt')
    else:
        recent_data = Dht11.objects.all().order_by('dt')

    data_count = recent_data.count()

    # CORRECTION : Créer automatiquement des incidents pour les données problématiques
    # CETTE FONCTION ENVOIE AUSSI LES EMAILS AUTOMATIQUEMENT
    incidents_created = check_and_create_incidents(request)
    
    if incidents_created:
        for incident in incidents_created:
            print(f"⚠️ Incident #{incident.id} créé automatiquement: {incident.dht.temp}°C")
            print(f"   Email envoyé à: {settings.ALERT_EMAIL_ADMIN}, {settings.ALERT_EMAIL_OPERATOR}")

    # EXPORT CSV
    if 'export' in request.GET and request.GET['export'] == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        filename = f'donnees_capteur_{filter_option}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Date', 'Heure', 'Température (°C)', 'Humidité (%)'])
        
        for data in recent_data:
            date_str = localtime(data.dt).strftime("%d/%m/%Y")
            time_str = localtime(data.dt).strftime("%H:%M:%S")
            writer.writerow([date_str, time_str, data.temp, data.humidity])
        
        log_user_activity(f"a exporté les données ({filter_option})", request.user)
        
        return response

    # Graphique : prendre toutes les données filtrées
    MAX_POINTS = 100
    if recent_data.count() > MAX_POINTS:
        step = max(recent_data.count() // MAX_POINTS, 1)
        graph_data = list(recent_data)[::step]
    else:
        graph_data = recent_data

    temps = [float(d.temp) for d in graph_data]
    humid = [float(d.humidity) for d in graph_data]
    dates = [d.dt.strftime("%Y-%m-%d %H:%M") for d in graph_data]

    # Incidents
    open_incident = Incident.objects.filter(statut='ouvert').order_by('-dt_creation').first()
    all_incidents = Incident.objects.all().order_by('-dt_creation')
    open_incidents_count = Incident.objects.filter(statut='ouvert').count()

    # POST pour résolution d'incident
    if request.method == "POST" and 'resolve_incident' in request.POST:
        incident_id = request.POST.get('resolve_incident')
        try:
            incident = Incident.objects.get(id=incident_id)
            
            accuse_name = f"accuse_{incident.id}"
            commentaire_name = f"commentaire_{incident.id}"
            
            incident.accuse_reception = accuse_name in request.POST
            incident.commentaire = request.POST.get(commentaire_name, incident.commentaire)
            incident.statut = 'ferme'
            incident.save()
            
            # Envoyer email de résolution
            try:
                notifier = EmailNotificationSystem()
                notifier.send_incident_resolved(incident, request.user)
            except:
                pass  # Ne pas bloquer si email échoue
            
            log_incident_resolved(incident, request.user)
            log_user_activity(f"a résolu l'incident #{incident.id}", request.user)
            
            messages.success(request, f"✅ Incident #{incident.id} résolu avec succès.")
            
        except Incident.DoesNotExist:
            messages.error(request, "Incident non trouvé")
        
        return redirect(f'{request.path}?filter={filter_option}')

    context = {
        "last_data": last_data,
        "incident": open_incident,
        "incidents": all_incidents,
        "open_incidents_count": open_incidents_count,
        "temps": temps,
        "humid": humid,
        "dates": dates,
        "filter_option": filter_option,
        "last_month_name": now.replace(month=last_month, year=last_month_year).strftime("%B %Y"),
        "data_count": data_count,
        "user": request.user,
    }
    return render(request, "DHT/operator_dashboard.html", context)

# ========== DASHBOARD ADMIN ==========

@login_required
@superuser_required
def admin_dashboard(request):
    """Dashboard administrateur simplifié - UNIQUEMENT pour superusers"""
    
    # Dernière mesure
    last_data = Dht11.objects.order_by('-dt').first()
    if not last_data:
        last_data = Dht11(temp=0, humidity=0, dt=timezone.now())
    
    # Incidents ouverts
    open_incidents = Incident.objects.filter(statut='ouvert').order_by('-dt_creation')
    
    # Statistiques
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # Moyenne température aujourd'hui
    today_data = Dht11.objects.filter(dt__date=today)
    today_avg_result = today_data.aggregate(avg_temp=Avg('temp'))
    today_avg_temp = today_avg_result['avg_temp'] or 0
    
    # Moyenne température hier
    yesterday_data = Dht11.objects.filter(dt__date=yesterday)
    yesterday_avg_result = yesterday_data.aggregate(avg_temp=Avg('temp'))
    yesterday_avg_temp = yesterday_avg_result['avg_temp'] or 0
    
    # Calcul du changement
    temp_change = 0
    if yesterday_avg_temp and today_avg_temp:
        temp_change = ((today_avg_temp - yesterday_avg_temp) / yesterday_avg_temp) * 100
    
    # Nombre total de mesures
    total_measures = Dht11.objects.count()
    
    # Mesures aujourd'hui
    measures_today = today_data.count()
    
    # Statistiques logs
    total_logs = SystemLog.objects.count()
    logs_today = SystemLog.objects.filter(created_at__date=today).count()
    
    context = {
        'last_data': last_data,
        'open_incidents': open_incidents,
        'open_incidents_count': open_incidents.count(),
        'total_incidents': Incident.objects.count(),
        'today_avg_temp': round(today_avg_temp, 1),
        'temp_change': round(temp_change, 1),
        'total_measures': total_measures,
        'measures_today': measures_today,
        'total_logs': total_logs,
        'logs_today': logs_today,
        'user': request.user,
    }
    
    return render(request, 'DHT/admin_dashboard.html', context)

# ========== GESTION DES LOGS ==========

@login_required
@staff_or_superuser_required
def system_logs_view(request):
    """Page des logs système"""
    # Filtres
    level_filter = request.GET.get('level', 'all')
    category_filter = request.GET.get('category', 'all')
    date_filter = request.GET.get('date', 'today')
    
    # Base queryset
    logs = SystemLog.objects.all()
    
    # Appliquer les filtres
    if level_filter != 'all':
        logs = logs.filter(level=level_filter)
    
    if category_filter != 'all':
        logs = logs.filter(category=category_filter)
    
    if date_filter == 'today':
        today = timezone.now().date()
        logs = logs.filter(created_at__date=today)
    elif date_filter == 'week':
        week_ago = timezone.now() - timedelta(days=7)
        logs = logs.filter(created_at__gte=week_ago)
    elif date_filter == 'month':
        month_ago = timezone.now() - timedelta(days=30)
        logs = logs.filter(created_at__gte=month_ago)
    
    # Statistiques par niveau
    info_count = SystemLog.objects.filter(level='info').count()
    warning_count = SystemLog.objects.filter(level='warning').count()
    error_count = SystemLog.objects.filter(level='error').count()
    critical_count = SystemLog.objects.filter(level='critical').count()
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(logs, 50)
    try:
        logs_page = paginator.page(page)
    except PageNotAnInteger:
        logs_page = paginator.page(1)
    except EmptyPage:
        logs_page = paginator.page(paginator.num_pages)
    
    # Statistiques
    total_logs = SystemLog.objects.count()
    logs_today = SystemLog.objects.filter(created_at__date=timezone.now().date()).count()
    
    context = {
        'logs': logs_page,
        'total_logs': total_logs,
        'logs_today': logs_today,
        'info_count': info_count,
        'warning_count': warning_count,
        'error_count': error_count,
        'critical_count': critical_count,
        'level_filter': level_filter,
        'category_filter': category_filter,
        'date_filter': date_filter,
        'user': request.user,
    }
    
    return render(request, 'DHT/system_logs.html', context)

@login_required
@staff_or_superuser_required
def alert_history_view(request):
    """Historique des incidents"""
    # Récupérer tous les incidents
    incidents = Incident.objects.all().order_by('-dt_creation')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(incidents, 20)
    try:
        incidents_page = paginator.page(page)
    except PageNotAnInteger:
        incidents_page = paginator.page(1)
    except EmptyPage:
        incidents_page = paginator.page(paginator.num_pages)
    
    # Statistiques
    total_alerts = incidents.count()
    unresolved_incidents = incidents.filter(statut='ouvert').count()
    
    context = {
        'incidents': incidents_page,
        'total_alerts': total_alerts,
        'unresolved_incidents': unresolved_incidents,
        'user': request.user,
    }
    
    return render(request, 'DHT/alert_history.html', context)
    
@login_required
@staff_or_superuser_required
def clear_logs_view(request):
    """Vider les anciens logs"""
    if request.method == 'POST':
        month_ago = timezone.now() - timedelta(days=30)
        
        old_logs_count = SystemLog.objects.filter(created_at__lt=month_ago).count()
        
        if old_logs_count > 0:
            SystemLog.objects.filter(created_at__lt=month_ago).delete()
            messages.success(request, f'{old_logs_count} anciens logs (plus de 30 jours) ont été supprimés.')
            log_user_activity(f"a nettoyé {old_logs_count} anciens logs", request.user)
        else:
            messages.info(request, 'Aucun log ancien à supprimer.')
        
        return redirect('system_logs')
    
    month_ago = timezone.now() - timedelta(days=30)
    old_logs_count = SystemLog.objects.filter(created_at__lt=month_ago).count()
    total_logs = SystemLog.objects.count()
    
    context = {
        'old_logs_count': old_logs_count,
        'total_logs': total_logs,
        'user': request.user,
    }
    
    return render(request, 'DHT/clear_logs.html', context)

# ========== UTILITAIRES ==========

@login_required
def nettoyer_incidents_doublons(request):
    """Supprime les incidents en double pour les mêmes données"""
    dht_ids_avec_doublons = Incident.objects.values('dht_id').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    incidents_a_supprimer = []
    
    for dht_info in dht_ids_avec_doublons:
        dht_id = dht_info['dht_id']
        incidents = Incident.objects.filter(dht_id=dht_id).order_by('-dt_creation')
        
        for incident in incidents[1:]:
            incidents_a_supprimer.append(incident.id)
    
    if incidents_a_supprimer:
        Incident.objects.filter(id__in=incidents_a_supprimer).delete()
        messages.success(request, f"{len(incidents_a_supprimer)} incidents en double supprimés.")
        log_user_activity(f"a nettoyé {len(incidents_a_supprimer)} incidents en double", request.user)
    else:
        messages.info(request, "Aucun doublon trouvé.")
    
    return redirect('operator_dashboard')

@login_required
@staff_or_superuser_required
def generate_test_logs(request):
    """Générer des logs de test (pour développement)"""
    if request.method == 'POST':
        log_system_start()
        log_temperature_alert(9.5)
        log_temperature_alert(1.5)
        log_humidity_alert(95)
        log_humidity_alert(35)
        log_user_activity("a généré des logs de test", request.user)
        
        messages.success(request, "Logs de test générés avec succès.")
        return redirect('system_logs')
    
    return render(request, 'DHT/generate_test_logs.html')

# ========== FONCTION DE TEST D'INCIDENTS ==========

@login_required
def test_incident_creation(request):
    """Test manuel de création d'incident avec email automatique"""
    # Récupérer la dernière donnée
    last_data = Dht11.objects.order_by('-dt').first()
    
    if not last_data:
        messages.error(request, "Aucune donnée disponible")
        return redirect('operator_dashboard')
    
    # Vérifier si un incident existe déjà
    existing_incident = Incident.objects.filter(dht=last_data).exists()
    
    if existing_incident:
        messages.warning(request, f"Un incident existe déjà pour la donnée #{last_data.id} ({last_data.temp}°C)")
    else:
        # Créer un incident de test
        incident = Incident.objects.create(
            dht=last_data,
            statut='ouvert',
            created_by=request.user,
            commentaire=f"Incident de test: {last_data.temp}°C"
        )
        
        log_incident_created(incident, request.user)
        log_temperature_alert(last_data.temp)
        
        # ENVOYER EMAIL AUTOMATIQUEMENT
        try:
            is_high = last_data.temp > settings.ALERT_TEMP_HIGH
            AsyncEmailSender.send_temperature_alert_async(
                temperature=last_data.temp,
                humidity=last_data.humidity,
                timestamp=last_data.dt,
                is_high=is_high
            )
            
            AsyncEmailSender.send_incident_email_async(incident, 'created')
            
            messages.success(request, f"✅ Incident de test créé: #{incident.id} pour {last_data.temp}°C")
            messages.info(request, "📧 Email envoyé automatiquement à l'admin et l'opérateur")
            
        except Exception as e:
            messages.success(request, f"Incident de test créé: #{incident.id} pour {last_data.temp}°C")
            messages.warning(request, f"Mais erreur email: {e}")
    
    return redirect('operator_dashboard')