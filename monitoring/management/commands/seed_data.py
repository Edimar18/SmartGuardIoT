import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from monitoring.models import Building, Sensor, EnergyReading, Anomaly, Alert


class Command(BaseCommand):
    help = 'Seed SmartGuard IoT database with simulated data'

    def handle(self, *args, **kwargs):
        self.stdout.write('🌱 Seeding SmartGuard database...')
        self.create_buildings()
        self.stdout.write(self.style.SUCCESS('✅ Done!'))

    def create_buildings(self):
        buildings_data = [
            {'name': 'Sunrise Residence', 'building_type': 'residential', 'address': '123 Maple St', 'total_floors': 2},
            {'name': 'Greenfield Elementary', 'building_type': 'school', 'address': '456 Oak Ave', 'total_floors': 3},
            {'name': 'CityHall Complex', 'building_type': 'government', 'address': '1 Gov Plaza', 'total_floors': 5},
            {'name': 'TechPark Office', 'building_type': 'commercial', 'address': '789 Tech Blvd', 'total_floors': 4},
        ]
        for bd in buildings_data:
            building, _ = Building.objects.get_or_create(name=bd['name'], defaults=bd)
            self.stdout.write(f'  🏢 Building: {building.name}')
            self.create_sensors(building)

    def create_sensors(self, building):
        sensor_configs = [
            {'name': 'Main Panel Sensor', 'sensor_type': 'main_panel', 'location_in_building': 'Basement'},
            {'name': 'HVAC Sensor', 'sensor_type': 'hvac', 'location_in_building': 'Rooftop'},
            {'name': 'Lighting Sensor', 'sensor_type': 'lighting', 'location_in_building': 'Floor 1'},
        ]
        for sc in sensor_configs:
            sensor, _ = Sensor.objects.get_or_create(
                building=building, name=sc['name'], defaults=sc
            )
            self.create_readings(sensor)
            self.create_anomalies(sensor)

    def create_readings(self, sensor):
        if sensor.readings.count() >= 100:
            return
        readings = []
        now = timezone.now()
        for i in range(120):
            ts = now - timedelta(hours=i)
            # Simulate peak hours (8am-6pm) with higher usage
            hour = ts.hour
            base_power = 1500 if 8 <= hour <= 18 else 400
            power = base_power + random.gauss(0, 200)
            # Occasional spike
            if random.random() < 0.05:
                power *= random.uniform(2.5, 4.0)
            readings.append(EnergyReading(
                sensor=sensor,
                timestamp=ts,
                current=round(power / 220, 2),
                voltage=round(random.uniform(218, 222), 2),
                power_usage=round(abs(power), 2),
                power_factor=round(random.uniform(0.75, 1.0), 3),
                frequency=round(random.uniform(59.8, 60.2), 2),
            ))
        EnergyReading.objects.bulk_create(readings)
        self.stdout.write(f'    📊 Created {len(readings)} readings for {sensor.name}')

    def create_anomalies(self, sensor):
        if sensor.anomalies.count() >= 5:
            return
        anomaly_types = ['spike', 'overload', 'low_pf', 'fault', 'unusual']
        severities = ['low', 'medium', 'high', 'critical']
        for _ in range(random.randint(3, 6)):
            a_type = random.choice(anomaly_types)
            sev = random.choice(severities)
            anomaly = Anomaly.objects.create(
                sensor=sensor,
                anomaly_type=a_type,
                severity=sev,
                description=f"Auto-detected {a_type} on {sensor.name}",
                resolved=random.choice([True, False]),
            )
            Alert.objects.create(
                anomaly=anomaly,
                status=random.choice(['sent', 'acknowledged', 'dismissed']),
                response_time_minutes=round(random.uniform(1, 120), 1),
            )
        self.stdout.write(f'    🚨 Created anomalies for {sensor.name}')