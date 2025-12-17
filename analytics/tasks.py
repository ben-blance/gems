from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from django.db import transaction

@shared_task
def compute_spread_analytics(symbol1, symbol2, timeframe='1s', window=60, lookback_minutes=10):
    try:
        from ingestion.models import ProcessedBar
        from analytics.models import SpreadAnalytics
        
        from_time = timezone.now() - timedelta(minutes=lookback_minutes)
        
        bars1 = ProcessedBar.objects.filter(
            symbol=symbol1,
            timeframe=timeframe,
            timestamp__gte=from_time
        ).order_by('timestamp').values('timestamp', 'close')
        
        bars2 = ProcessedBar.objects.filter(
            symbol=symbol2,
            timeframe=timeframe,
            timestamp__gte=from_time
        ).order_by('timestamp').values('timestamp', 'close')
        
        df1 = pd.DataFrame(list(bars1))
        df2 = pd.DataFrame(list(bars2))
        
        if len(df1) < window or len(df2) < window:
            return 0
        
        df1['close'] = df1['close'].astype(float)
        df2['close'] = df2['close'].astype(float)
        
        df1['timestamp'] = pd.to_datetime(df1['timestamp'])
        df2['timestamp'] = pd.to_datetime(df2['timestamp'])
        
        df1.set_index('timestamp', inplace=True)
        df2.set_index('timestamp', inplace=True)
        
        all_timestamps = df1.index.union(df2.index).sort_values()
        df1 = df1.reindex(all_timestamps, method='ffill')
        df2 = df2.reindex(all_timestamps, method='ffill')
        
        merged = pd.DataFrame({
            'close_1': df1['close'],
            'close_2': df2['close']
        }).dropna()
        
        print(f"After merge: {len(merged)} rows (from {len(df1)} and {len(df2)})")
        
        if len(merged) < window:
            return 0
        
        X = merged['close_2'].values.reshape(-1, 1)
        y = merged['close_1'].values
        
        X_with_const = np.column_stack([np.ones(len(X)), X])
        hedge_ratio = np.linalg.lstsq(X_with_const, y, rcond=None)[0][1]
        
        spread = merged['close_1'] - hedge_ratio * merged['close_2']
        
        rolling_mean = spread.rolling(window=window).mean()
        rolling_std = spread.rolling(window=window).std()
        
        z_score = (spread - rolling_mean) / rolling_std
        
        correlation = merged['close_1'].rolling(window=window).corr(merged['close_2'])
        
        adf_result = None
        is_cointegrated = False
        if len(spread) >= window:
            try:
                adf_result = adfuller(spread.dropna()[-window:])
                is_cointegrated = adf_result[1] < 0.05
            except:
                pass
        
        symbol_pair = f"{symbol1}_{symbol2}"
        analytics_to_create = []
        
        for idx, row in merged.iloc[-50:].iterrows():
            if pd.isna(z_score.loc[idx]):
                continue
                
            analytics_to_create.append(SpreadAnalytics(
                symbol_pair=symbol_pair,
                timestamp=idx,
                timeframe=timeframe,
                symbol1_price=Decimal(str(row['close_1'])),
                symbol2_price=Decimal(str(row['close_2'])),
                hedge_ratio=Decimal(str(hedge_ratio)),
                spread=Decimal(str(spread.loc[idx])),
                z_score=Decimal(str(z_score.loc[idx])),
                rolling_mean=Decimal(str(rolling_mean.loc[idx])),
                rolling_std=Decimal(str(rolling_std.loc[idx])),
                correlation=Decimal(str(correlation.loc[idx])) if not pd.isna(correlation.loc[idx]) else None,
                adf_statistic=Decimal(str(adf_result[0])) if adf_result else None,
                adf_pvalue=Decimal(str(adf_result[1])) if adf_result else None,
                is_cointegrated=is_cointegrated
            ))
        
        with transaction.atomic():
            for analytics in analytics_to_create:
                SpreadAnalytics.objects.update_or_create(
                    symbol_pair=analytics.symbol_pair,
                    timeframe=analytics.timeframe,
                    timestamp=analytics.timestamp,
                    defaults={
                        'symbol1_price': analytics.symbol1_price,
                        'symbol2_price': analytics.symbol2_price,
                        'hedge_ratio': analytics.hedge_ratio,
                        'spread': analytics.spread,
                        'z_score': analytics.z_score,
                        'rolling_mean': analytics.rolling_mean,
                        'rolling_std': analytics.rolling_std,
                        'correlation': analytics.correlation,
                        'adf_statistic': analytics.adf_statistic,
                        'adf_pvalue': analytics.adf_pvalue,
                        'is_cointegrated': analytics.is_cointegrated
                    }
                )
        
        check_alerts.delay(symbol_pair, timeframe)
        
        return len(analytics_to_create)
        
    except Exception as e:
        print(f"ERROR in compute_spread_analytics: {e}")
        import traceback
        traceback.print_exc()
        return 0

@shared_task
def compute_price_stats(symbol, timeframe='1s', lookback_minutes=10):
    try:
        from ingestion.models import ProcessedBar
        from analytics.models import PriceStats
        
        from_time = timezone.now() - timedelta(minutes=lookback_minutes)
        
        bars = ProcessedBar.objects.filter(
            symbol=symbol,
            timeframe=timeframe,
            timestamp__gte=from_time
        ).order_by('timestamp').values('timestamp', 'close', 'high', 'low', 'volume')
        
        df = pd.DataFrame(list(bars))
        
        if len(df) < 2:
            return 0
        
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=20).std()
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['price_change_pct'] = (df['close'] - df['close'].shift(1)) / df['close'].shift(1) * 100
        df['high_low_range'] = df['high'] - df['low']
        
        df = df.dropna()
        
        stats_to_create = []
        for idx, row in df.iterrows():
            stats_to_create.append(PriceStats(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=row['timestamp'],
                returns=Decimal(str(row['returns'])),
                volatility=Decimal(str(row['volatility'])),
                volume_ma=Decimal(str(row['volume_ma'])),
                price_change_pct=Decimal(str(row['price_change_pct'])),
                high_low_range=Decimal(str(row['high_low_range']))
            ))
        
        with transaction.atomic():
            for stat in stats_to_create:
                PriceStats.objects.update_or_create(
                    symbol=stat.symbol,
                    timeframe=stat.timeframe,
                    timestamp=stat.timestamp,
                    defaults={
                        'returns': stat.returns,
                        'volatility': stat.volatility,
                        'volume_ma': stat.volume_ma,
                        'price_change_pct': stat.price_change_pct,
                        'high_low_range': stat.high_low_range
                    }
                )
        
        return len(stats_to_create)
        
    except Exception as e:
        print(f"ERROR in compute_price_stats: {e}")
        import traceback
        traceback.print_exc()
        return 0

@shared_task
def check_alerts(symbol_pair, timeframe):
    try:
        from analytics.models import SpreadAnalytics, Alert
        
        latest = SpreadAnalytics.objects.filter(
            symbol_pair=symbol_pair,
            timeframe=timeframe
        ).order_by('-timestamp').first()
        
        if not latest:
            return 0
        
        active_alerts = Alert.objects.filter(
            symbol_pair=symbol_pair,
            status='active'
        )
        
        triggered_count = 0
        
        for alert in active_alerts:
            condition = alert.condition
            triggered = False
            
            if alert.alert_type == 'zscore_high':
                if latest.z_score >= Decimal(str(condition['threshold'])):
                    triggered = True
                    
            elif alert.alert_type == 'zscore_low':
                if latest.z_score <= Decimal(str(condition['threshold'])):
                    triggered = True
            
            if triggered:
                alert.status = 'triggered'
                alert.triggered_at = timezone.now()
                alert.trigger_value = latest.z_score
                alert.save()
                triggered_count += 1
                print(f"Alert triggered: {alert.alert_type} for {symbol_pair}, z-score={latest.z_score}")
        
        return triggered_count
        
    except Exception as e:
        print(f"ERROR in check_alerts: {e}")
        return 0