from django.db import models
from django.contrib.auth.models import User

class Dht11(models.Model):
    temp = models.FloatField()
    humidity = models.FloatField(default=0)
    dt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.temp}°C, {self.humidity}% @ {self.dt}"

class Incident(models.Model):
    STATUS_CHOICES = [
        ('ouvert', 'Ouvert'),
        ('ferme', 'Fermé'),
    ]
    dht = models.ForeignKey(Dht11, on_delete=models.CASCADE)
    statut = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ouvert')
    accuse_reception = models.BooleanField(default=False)
    commentaire = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    dt_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Incident {self.id} - {self.statut}"

class SystemLog(models.Model):
    LOG_LEVELS = [
        ('info', 'Information'),
        ('warning', 'Avertissement'),
        ('error', 'Erreur'),
        ('critical', 'Critique'),
    ]
    
    LOG_CATEGORIES = [
        ('system', 'Système'),
        ('temperature', 'Température'),
        ('humidity', 'Humidité'),
        ('incident', 'Incident'),
        ('user', 'Utilisateur'),
        ('sensor', 'Capteur'),
    ]
    
    level = models.CharField('Niveau', max_length=20, choices=LOG_LEVELS)
    category = models.CharField('Catégorie', max_length=20, choices=LOG_CATEGORIES)
    message = models.TextField('Message')
    details = models.JSONField('Détails', null=True, blank=True)
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Log système'
        verbose_name_plural = 'Logs système'
    
    def __str__(self):
        return f"[{self.level.upper()}] {self.message[:50]}..."