from django.db import models
from django.utils import timezone


class Building(models.Model):
    BUILDING_TYPES = [
        ('residential', 'Residential'),
        ('school', 'School'),
        ('commercial', 'Commercial'),
        ('government', 'Government'),
    ]
    name = models.CharField(max_length=200)
    building_type = models.CharField(max_length=20, choices=BUILDING_TYPES)
    address = models.TextField()
    total_floors = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.building_type})"

    class Meta:
        ordering = ['name']


class Sensor(models.Model):
    SENSOR_TYPES = [
        ('main_panel', 'Main Panel'),
        ('appliance', 'Appliance'),
        ('hvac', 'HVAC'),
        ('lighting', 'Lighting'),
    ]
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='sensors')
    name = models.CharField(max_length=100)
    sensor_type = models.CharField(max_length=20, choices=SENSOR_TYPES)
    location_in_building = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    installed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} @ {self.building.name}"


class EnergyReading(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='readings')
    timestamp = models.DateTimeField()
    current = models.FloatField()       # Amperes
    voltage = models.FloatField()       # Volts
    power_usage = models.FloatField()   # Watts
    power_factor = models.FloatField()  # 0.0–1.0
    frequency = models.FloatField(default=60.0)  # Hz

    class Meta:
        ordering = ['-timestamp']
        indexes = [models.Index(fields=['sensor', 'timestamp'])]

    def __str__(self):
        return f"{self.sensor} @ {self.timestamp}: {self.power_usage}W"


class Anomaly(models.Model):
    ANOMALY_TYPES = [
        ('spike', 'Power Spike'),
        ('overload', 'Overload'),
        ('low_pf', 'Low Power Factor'),
        ('fault', 'Electrical Fault'),
        ('unusual', 'Unusual Pattern'),
    ]
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='anomalies')
    energy_reading = models.ForeignKey(EnergyReading, on_delete=models.SET_NULL, null=True, blank=True)
    anomaly_type = models.CharField(max_length=20, choices=ANOMALY_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    detected_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.anomaly_type} [{self.severity}] @ {self.sensor}"


class Alert(models.Model):
    ALERT_STATUS = [
        ('sent', 'Sent'),
        ('acknowledged', 'Acknowledged'),
        ('dismissed', 'Dismissed'),
    ]
    anomaly = models.ForeignKey(Anomaly, on_delete=models.CASCADE, related_name='alerts')
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ALERT_STATUS, default='sent')
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    response_time_minutes = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Alert for {self.anomaly} – {self.status}"