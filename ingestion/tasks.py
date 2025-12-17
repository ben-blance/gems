from celery import shared_task
from django.utils import timezone
from datetime import datetime
import json
from .models import RawTick, ProcessedBar
from django.db import transaction
import pandas as pd
from decimal import Decimal

@shared_task
def ingest_tick_batch(tick_data_list):
    ticks_to_create = []
    symbols = set()
    for tick in tick_data_list:
        ts = datetime.fromisoformat(tick['ts'].replace('Z', '+00:00'))
        ticks_to_create.append(RawTick(
            symbol=tick['symbol'],
            timestamp=ts,
            price=Decimal(str(tick['price'])),
            size=Decimal(str(tick['size']))
        ))
        symbols.add(tick['symbol'])
    
    with transaction.atomic():
        RawTick.objects.bulk_create(ticks_to_create, ignore_conflicts=True)
    
    for symbol in symbols:
        process_ticks_to_bars.delay(symbol, '1s', lookback_minutes=2)
    
    return len(ticks_to_create)

@shared_task
def process_ticks_to_bars(symbol, timeframe='1s', lookback_minutes=5):
    try:
        from_time = timezone.now() - timezone.timedelta(minutes=lookback_minutes)
        
        ticks = RawTick.objects.filter(
            symbol=symbol,
            timestamp__gte=from_time
        ).values('timestamp', 'price', 'size').order_by('timestamp')
        
        tick_list = list(ticks)
        print(f"Found {len(tick_list)} ticks for {symbol} from {from_time}")
        
        if not tick_list:
            return 0
        
        df = pd.DataFrame(tick_list)
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        df.set_index('timestamp', inplace=True)
        df['price'] = df['price'].astype(float)
        df['size'] = df['size'].astype(float)
        
        print(f"DataFrame shape: {df.shape}, index range: {df.index.min()} to {df.index.max()}")
        
        bars = df['price'].resample(timeframe).ohlc()
        volume = df['size'].resample(timeframe).sum()
        tick_count = df['price'].resample(timeframe).count()
        
        bars['volume'] = volume
        bars['tick_count'] = tick_count
        bars = bars.dropna()
        
        print(f"Created {len(bars)} bars after resampling")
        
        bars_to_create = []
        for ts, row in bars.iterrows():
            bars_to_create.append(ProcessedBar(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=ts.to_pydatetime(),
                open=Decimal(str(row['open'])),
                high=Decimal(str(row['high'])),
                low=Decimal(str(row['low'])),
                close=Decimal(str(row['close'])),
                volume=Decimal(str(row['volume'])),
                tick_count=int(row['tick_count'])
            ))
        
        with transaction.atomic():
            for bar in bars_to_create:
                ProcessedBar.objects.update_or_create(
                    symbol=bar.symbol,
                    timeframe=bar.timeframe,
                    timestamp=bar.timestamp,
                    defaults={
                        'open': bar.open,
                        'high': bar.high,
                        'low': bar.low,
                        'close': bar.close,
                        'volume': bar.volume,
                        'tick_count': bar.tick_count
                    }
                )
        
        print(f"Successfully saved {len(bars_to_create)} bars to database")
        return len(bars_to_create)
        
    except Exception as e:
        print(f"ERROR in process_ticks_to_bars: {e}")
        import traceback
        traceback.print_exc()
        raise

@shared_task
def process_ndjson_file(file_path):
    ticks = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                ticks.append(json.loads(line))
    
    batch_size = 1000
    for i in range(0, len(ticks), batch_size):
        batch = ticks[i:i+batch_size]
        ingest_tick_batch.delay(batch)
    
    return len(ticks)