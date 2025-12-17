from django.core.management.base import BaseCommand
from ingestion.models import ProcessedBar
from django.utils import timezone
from datetime import timedelta
import pandas as pd

class Command(BaseCommand):
    help = 'Debug spread analytics data alignment'

    def handle(self, *args, **options):
        from_time = timezone.now() - timedelta(minutes=10)
        
        btc_bars = ProcessedBar.objects.filter(
            symbol='BTCUSDT',
            timeframe='1s',
            timestamp__gte=from_time
        ).order_by('timestamp')
        
        eth_bars = ProcessedBar.objects.filter(
            symbol='ETHUSDT',
            timeframe='1s',
            timestamp__gte=from_time
        ).order_by('timestamp')
        
        self.stdout.write(f'BTC bars: {btc_bars.count()}')
        self.stdout.write(f'ETH bars: {eth_bars.count()}')
        
        if btc_bars.exists():
            first_btc = btc_bars.first()
            last_btc = btc_bars.last()
            self.stdout.write(f'BTC range: {first_btc.timestamp} to {last_btc.timestamp}')
        
        if eth_bars.exists():
            first_eth = eth_bars.first()
            last_eth = eth_bars.last()
            self.stdout.write(f'ETH range: {first_eth.timestamp} to {last_eth.timestamp}')
        
        btc_ts = set(btc_bars.values_list('timestamp', flat=True))
        eth_ts = set(eth_bars.values_list('timestamp', flat=True))
        
        common_ts = btc_ts.intersection(eth_ts)
        self.stdout.write(f'Common timestamps: {len(common_ts)}')
        
        if len(common_ts) < 60:
            self.stdout.write(self.style.WARNING('Not enough aligned data for spread analytics'))
            self.stdout.write('Need at least 60 common timestamps')
        else:
            self.stdout.write(self.style.SUCCESS('Enough data for spread analytics'))