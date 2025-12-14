from django.db import models
from django.contrib.auth.models import AbstractUser


# =========================================================
#  CUSTOM USER MODEL (ADMIN / OPERATOR)
# =========================================================
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('operator', 'Operator'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='operator')

    def __str__(self):
        return f"{self.username} ({self.role})"


# =========================================================
#  SENSOR
# =========================================================
class Sensor(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=150, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.location})"


# =========================================================
#  THRESHOLDS
# =========================================================
class Threshold(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, null=True, blank=True)
    temp_min = models.FloatField(default=2.0)
    temp_max = models.FloatField(default=8.0)
    hum_min = models.FloatField(default=0.0)
    hum_max = models.FloatField(default=100.0)

    def __str__(self):
        return f"Thresholds for {self.sensor.name}"


# =========================================================
#  INCIDENT / TICKET
# =========================================================
class Ticket(models.Model):
    @property
    def my_comment(self):
        return self.comments.order_by('-created_at').first()

    INCIDENT_TYPES = [
        ('temp_high', 'Température élevée'),
        ('temp_low', 'Température basse'),
        ('hum_high', 'Humidité élevée'),
        ('hum_low', 'Humidité basse'),
        ('sensor_off', 'Capteur offline'),
        ('other', 'Autre'),
    ]

    STATUS = [
        ('open', 'Ouvert'),
        ('in_progress', 'En cours'),
        ('closed', 'Clos'),
    ]

    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, null=True, blank=True)
    incident_type = models.CharField(max_length=50, choices=INCIDENT_TYPES)
    temp = models.FloatField(null=True, blank=True)
    hum = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # 🔥 assigné à opérateur (CustomUser)
    assigned_to = models.ForeignKey(
        "CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets"
    )

    status = models.CharField(max_length=20, choices=STATUS, default='open')
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_incident_type_display()} - {self.sensor.name} @ {self.created_at}"


# =========================================================
#  AUDIT LOG
# =========================================================
class AuditLog(models.Model):
    user = models.ForeignKey(
        "CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    action = models.CharField(max_length=300)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.timestamp} - {self.action}"


# =========================================================
#  DHT SENSOR READINGS
# =========================================================
class Dht11(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, null=True, blank=True)
    temp = models.FloatField(null=True)
    hum = models.FloatField(null=True)
    dt = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.dt}: {self.temp}°C / {self.hum}%"
# class Comment(models.Model):
#     ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
#     user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
#     content = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.ticket.id} - {self.created_at}"
class Comment(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,   # autorise les anciennes lignes à ne pas avoir de ticket
        blank=True
    )
    user_name = models.CharField(max_length=100, default="unknown")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_name} - Ticket #{self.ticket.id if self.ticket else 'N/A'}"


class Alert(models.Model):
    operator = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'operator'}
    )

    counter_value = models.IntegerField()
    message = models.CharField(max_length=255)

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alerte → {self.operator.username} ({self.counter_value})"
class Seuil(models.Model):
    temp_min = models.FloatField()
    temp_max = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Seuil {self.temp_min}°C - {self.temp_max}°C"