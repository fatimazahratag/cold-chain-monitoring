from rest_framework import viewsets, permissions
from .models import Sensor, Threshold, Dht11, Ticket
from .serializers import SensorSerializer, ThresholdSerializer, DhtSerializer, TicketSerializer

class SensorViewSet(viewsets.ModelViewSet):
    queryset = Sensor.objects.all()
    serializer_class = SensorSerializer
    permission_classes = [permissions.AllowAny]

class ThresholdViewSet(viewsets.ModelViewSet):
    queryset = Threshold.objects.all()
    serializer_class = ThresholdSerializer
    permission_classes = [permissions.AllowAny]

class DhtViewSet(viewsets.ModelViewSet):
    queryset = Dht11.objects.all().order_by('-dt')
    serializer_class = DhtSerializer
    permission_classes = [permissions.AllowAny]

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all().order_by('-created_at')
    serializer_class = TicketSerializer
    permission_classes = [permissions.AllowAny]
