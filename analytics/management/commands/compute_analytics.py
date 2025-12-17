from django.core.management.base import BaseCommand
from analytics.tasks import compute_spread_analytics, compute_price_stats

class Command(BaseCommand):
    help = 'Manually trigger analytics computation'

    def add_arguments(self, parser):
        parser.add_argument('--symbol1', type=str, default='BTCUSDT')
        parser.add_argument('--symbol2', type=str, default='ETHUSDT')
        parser.add_argument('--timeframe', type=str, default='1s')
        parser.add_argument('--window', type=int, default=60)

    def handle(self, *args, **options):
        symbol1 = options['symbol1']
        symbol2 = options['symbol2']
        timeframe = options['timeframe']
        window = options['window']
        
        self.stdout.write(f'Computing spread analytics for {symbol1}/{symbol2}...')
        result = compute_spread_analytics(symbol1, symbol2, timeframe, window)
        self.stdout.write(self.style.SUCCESS(f'Created {result} analytics records'))
        
        self.stdout.write(f'\nComputing price stats for {symbol1}...')
        result1 = compute_price_stats(symbol1, timeframe)
        self.stdout.write(self.style.SUCCESS(f'Created {result1} stats records'))
        
        self.stdout.write(f'\nComputing price stats for {symbol2}...')
        result2 = compute_price_stats(symbol2, timeframe)
        self.stdout.write(self.style.SUCCESS(f'Created {result2} stats records'))