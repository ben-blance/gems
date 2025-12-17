from django.core.management.base import BaseCommand
from ingestion.tasks import process_ticks_to_bars

class Command(BaseCommand):
    help = 'Manually trigger bar processing'

    def add_arguments(self, parser):
        parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Symbol to process')
        parser.add_argument('--timeframe', type=str, default='1s', help='Timeframe (1s, 1m, 5m)')
        parser.add_argument('--lookback', type=int, default=10, help='Lookback minutes')

    def handle(self, *args, **options):
        symbol = options['symbol']
        timeframe = options['timeframe']
        lookback = options['lookback']
        
        self.stdout.write(f'Processing bars for {symbol} ({timeframe})...')
        
        result = process_ticks_to_bars(symbol, timeframe, lookback)
        
        self.stdout.write(self.style.SUCCESS(f'Created {result} bars'))