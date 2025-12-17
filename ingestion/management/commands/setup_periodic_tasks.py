from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

class Command(BaseCommand):
    help = 'Setup periodic tasks for bar processing and analytics'

    def handle(self, *args, **options):
        schedule_1m, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES,
        )
        
        schedule_5m, _ = IntervalSchedule.objects.get_or_create(
            every=5,
            period=IntervalSchedule.MINUTES,
        )
        
        schedule_30s, _ = IntervalSchedule.objects.get_or_create(
            every=30,
            period=IntervalSchedule.SECONDS,
        )
        
        PeriodicTask.objects.get_or_create(
            interval=schedule_1m,
            name='Process 1m bars for BTCUSDT',
            defaults={
                'task': 'ingestion.tasks.process_ticks_to_bars',
                'args': json.dumps(['BTCUSDT', '1m', 10])
            }
        )
        
        PeriodicTask.objects.get_or_create(
            interval=schedule_1m,
            name='Process 1m bars for ETHUSDT',
            defaults={
                'task': 'ingestion.tasks.process_ticks_to_bars',
                'args': json.dumps(['ETHUSDT', '1m', 10])
            }
        )
        
        PeriodicTask.objects.get_or_create(
            interval=schedule_5m,
            name='Process 5m bars for BTCUSDT',
            defaults={
                'task': 'ingestion.tasks.process_ticks_to_bars',
                'args': json.dumps(['BTCUSDT', '5m', 30])
            }
        )
        
        PeriodicTask.objects.get_or_create(
            interval=schedule_5m,
            name='Process 5m bars for ETHUSDT',
            defaults={
                'task': 'ingestion.tasks.process_ticks_to_bars',
                'args': json.dumps(['ETHUSDT', '5m', 30])
            }
        )
        
        PeriodicTask.objects.get_or_create(
            interval=schedule_30s,
            name='Compute spread analytics BTCUSDT/ETHUSDT',
            defaults={
                'task': 'analytics.tasks.compute_spread_analytics',
                'args': json.dumps(['BTCUSDT', 'ETHUSDT', '1s', 60, 5])
            }
        )
        
        PeriodicTask.objects.get_or_create(
            interval=schedule_1m,
            name='Compute price stats BTCUSDT',
            defaults={
                'task': 'analytics.tasks.compute_price_stats',
                'args': json.dumps(['BTCUSDT', '1s', 5])
            }
        )
        
        PeriodicTask.objects.get_or_create(
            interval=schedule_1m,
            name='Compute price stats ETHUSDT',
            defaults={
                'task': 'analytics.tasks.compute_price_stats',
                'args': json.dumps(['ETHUSDT', '1s', 5])
            }
        )
        
        self.stdout.write(self.style.SUCCESS('Periodic tasks setup complete!'))