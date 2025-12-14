from rest_framework import serializers
from .models import Dht11, Sensor, Threshold, Ticket, AuditLog

class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensor
        fields = ['id', 'name', 'location', 'is_active']

class ThresholdSerializer(serializers.ModelSerializer):
    sensor = SensorSerializer(read_only=True)
    sensor_id = serializers.PrimaryKeyRelatedField(write_only=True, source='sensor', queryset=Sensor.objects.all())

    class Meta:
        model = Threshold
        fields = ['id', 'sensor', 'sensor_id', 'temp_min', 'temp_max', 'hum_min', 'hum_max']

class DhtSerializer(serializers.ModelSerializer):
    sensor = SensorSerializer(read_only=True)
    sensor_id = serializers.PrimaryKeyRelatedField(write_only=True, source='sensor', queryset=Sensor.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Dht11
        fields = ['id', 'sensor', 'sensor_id', 'temp', 'hum', 'dt']

class TicketSerializer(serializers.ModelSerializer):
    sensor = SensorSerializer(read_only=True)
    sensor_id = serializers.PrimaryKeyRelatedField(write_only=True, source='sensor', queryset=Sensor.objects.all())

    class Meta:
        model = Ticket
        fields = ['id', 'sensor', 'sensor_id', 'incident_type', 'temp', 'hum', 'created_at', 'assigned_to', 'status', 'description']

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'timestamp']
