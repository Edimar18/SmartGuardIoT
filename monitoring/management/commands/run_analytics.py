from django.core.management.base import BaseCommand
from django.db.models import Avg, Max, Min, Count, Sum, F, Q, StdDev
from django.db.models.functions import ExtractHour, TruncHour
from monitoring.models import Building, Sensor, EnergyReading, Anomaly, Alert


class Command(BaseCommand):
    help = 'Run SmartGuard analytics queries'

    def handle(self, *args, **kwargs):
        self.q1_highest_energy_spikes()
        self.q2_high_risk_time_periods()
        self.q3_anomaly_by_building_type()
        self.q4_power_factor_vs_faults()
        self.q5_alert_effectiveness()

    def q1_highest_energy_spikes(self):
        """Q1: Which appliances/sensors contribute the highest energy spikes per building?"""
        self.stdout.write('\n📌 Q1: Highest Energy Spikes Per Building')
        results = (
            EnergyReading.objects
            .values('sensor__building__name', 'sensor__name', 'sensor__sensor_type')
            .annotate(
                max_spike=Max('power_usage'),
                avg_power=Avg('power_usage'),
                spike_ratio=Max('power_usage') / Avg('power_usage'),
            )
            .order_by('sensor__building__name', '-max_spike')
        )
        for r in results:
            self.stdout.write(
                f"  🏢 {r['sensor__building__name']} | {r['sensor__name']} "
                f"| Max: {r['max_spike']:.1f}W | Avg: {r['avg_power']:.1f}W | Ratio: {r['spike_ratio']:.2f}x"
            )

    def q2_high_risk_time_periods(self):
        """Q2: What time periods show the highest risk of electrical overload?"""
        self.stdout.write('\n📌 Q2: Highest Risk Time Periods (by hour of day)')
        results = (
            EnergyReading.objects
            .annotate(hour=ExtractHour('timestamp'))
            .values('hour')
            .annotate(
                avg_power=Avg('power_usage'),
                max_power=Max('power_usage'),
                reading_count=Count('id'),
            )
            .order_by('-avg_power')
        )
        for r in results[:5]:
            self.stdout.write(
                f"  ⏰ Hour {r['hour']:02d}:00 | Avg: {r['avg_power']:.1f}W | Max: {r['max_power']:.1f}W"
            )

    def q3_anomaly_by_building_type(self):
        """Q3: How does anomaly detection vary across different building types?"""
        self.stdout.write('\n📌 Q3: Anomaly Detection by Building Type')
        results = (
            Anomaly.objects
            .values('sensor__building__building_type', 'anomaly_type', 'severity')
            .annotate(count=Count('id'))
            .order_by('sensor__building__building_type', '-count')
        )
        for r in results:
            self.stdout.write(
                f"  🏷 {r['sensor__building__building_type']:15} | {r['anomaly_type']:10} | {r['severity']:8} | Count: {r['count']}"
            )

    def q4_power_factor_vs_faults(self):
        """Q4: Correlation between low power factor and fault occurrence"""
        self.stdout.write('\n📌 Q4: Power Factor vs Fault Occurrence')
        # Sensors with avg low power factor AND high fault count
        results = (
            Sensor.objects
            .annotate(
                avg_pf=Avg('readings__power_factor'),
                fault_count=Count(
                    'anomalies',
                    filter=Q(anomalies__anomaly_type__in=['fault', 'overload'])
                ),
            )
            .filter(avg_pf__isnull=False)
            .order_by('avg_pf')
        )
        for s in results:
            pf_label = '⚠️ LOW' if s.avg_pf < 0.85 else '✅ OK'
            self.stdout.write(
                f"  {pf_label} {s.name:30} | Avg PF: {s.avg_pf:.3f} | Faults: {s.fault_count}"
            )

    def q5_alert_effectiveness(self):
        """Q5: How effective are alerts in reducing energy consumption?"""
        self.stdout.write('\n📌 Q5: Alert Effectiveness')
        total = Alert.objects.count()
        acknowledged = Alert.objects.filter(status='acknowledged').count()
        avg_response = Alert.objects.filter(
            status='acknowledged', response_time_minutes__isnull=False
        ).aggregate(avg_rt=Avg('response_time_minutes'))

        resolved_after_alert = Anomaly.objects.filter(
            resolved=True, alerts__status='acknowledged'
        ).distinct().count()

        self.stdout.write(f"  Total Alerts: {total}")
        self.stdout.write(f"  Acknowledged: {acknowledged} ({100*acknowledged//total if total else 0}%)")
        self.stdout.write(f"  Avg Response Time: {avg_response['avg_rt']:.1f} min")
        self.stdout.write(f"  Anomalies Resolved After Alert: {resolved_after_alert}")