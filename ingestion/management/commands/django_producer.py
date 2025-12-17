from django.core.management.base import BaseCommand
import asyncio
import websockets
import json
from datetime import datetime
from ingestion.tasks import ingest_tick_batch

class Command(BaseCommand):
    help = 'Connect to Binance WebSocket and ingest ticks via Celery'

    def add_arguments(self, parser):
        parser.add_argument('--symbols', type=str, default='btcusdt,ethusdt', help='Comma-separated symbols')
        parser.add_argument('--batch-size', type=int, default=100, help='Batch size for ingestion')

    def handle(self, *args, **options):
        symbols = options['symbols'].split(',')
        batch_size = options['batch_size']
        
        self.stdout.write(f'Starting producer for symbols: {symbols}')
        asyncio.run(self.start_producer(symbols, batch_size))

    async def start_producer(self, symbols, batch_size):
        tasks = [self.consume_symbol(symbol, batch_size) for symbol in symbols]
        await asyncio.gather(*tasks)

    async def consume_symbol(self, symbol, batch_size):
        symbol = symbol.strip().lower()
        url = f'wss://fstream.binance.com/ws/{symbol}@trade'
        
        batch = []
        
        async for websocket in websockets.connect(url):
            try:
                self.stdout.write(f'Connected to {symbol}')
                async for message in websocket:
                    data = json.loads(message)
                    
                    if data.get('e') == 'trade':
                        tick = {
                            'symbol': data['s'],
                            'ts': datetime.fromtimestamp(data['T'] / 1000).isoformat() + 'Z',
                            'price': float(data['p']),
                            'size': float(data['q'])
                        }
                        batch.append(tick)
                        
                        if len(batch) >= batch_size:
                            ingest_tick_batch.delay(batch.copy())
                            self.stdout.write(f'Dispatched batch of {len(batch)} ticks for {symbol}')
                            batch.clear()
                            
            except websockets.ConnectionClosed:
                self.stdout.write(f'Connection closed for {symbol}, reconnecting...')
                await asyncio.sleep(1)
            except Exception as e:
                self.stdout.write(f'Error for {symbol}: {e}')
                await asyncio.sleep(1)