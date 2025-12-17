from django.core.management.base import BaseCommand
from ingestion.models import RawTick
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Check what data exists in the database'

    def handle(self, *args, **options):
        total_ticks = RawTick.objects.count()
        self.stdout.write(f'Total ticks: {total_ticks}')
        
        if total_ticks == 0:
            self.stdout.write(self.style.ERROR('No ticks in database!'))
            return
        
        symbols = RawTick.objects.values_list('symbol', flat=True).distinct()
        self.stdout.write(f'Symbols: {list(symbols)}')
        
        for symbol in symbols:
            count = RawTick.objects.filter(symbol=symbol).count()
            oldest = RawTick.objects.filter(symbol=symbol).order_by('timestamp').first()
            newest = RawTick.objects.filter(symbol=symbol).order_by('-timestamp').first()
            
            self.stdout.write(f'\n{symbol}:')
            self.stdout.write(f'  Count: {count}')
            if oldest and newest:
                self.stdout.write(f'  Oldest: {oldest.timestamp}')
                self.stdout.write(f'  Newest: {newest.timestamp}')
                self.stdout.write(f'  Time span: {newest.timestamp - oldest.timestamp}')
        
        now = timezone.now()
        last_10m = RawTick.objects.filter(timestamp__gte=now - timedelta(minutes=10)).count()
        self.stdout.write(f'\nTicks in last 10 minutes: {last_10m}')
        
        last_1m = RawTick.objects.filter(timestamp__gte=now - timedelta(minutes=1)).count()
        self.stdout.write(f'Ticks in last 1 minute: {last_1m}')