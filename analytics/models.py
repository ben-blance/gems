from django.db import models

class SpreadAnalytics(models.Model):
    symbol_pair = models.CharField(max_length=50, db_index=True)
    timestamp = models.DateTimeField(db_index=True)
    timeframe = models.CharField(max_length=3)
    
    symbol1_price = models.DecimalField(max_digits=20, decimal_places=8)
    symbol2_price = models.DecimalField(max_digits=20, decimal_places=8)
    
    hedge_ratio = models.DecimalField(max_digits=10, decimal_places=6)
    spread = models.DecimalField(max_digits=20, decimal_places=8)
    z_score = models.DecimalField(max_digits=10, decimal_places=4)
    
    rolling_mean = models.DecimalField(max_digits=20, decimal_places=8)
    rolling_std = models.DecimalField(max_digits=20, decimal_places=8)
    
    correlation = models.DecimalField(max_digits=5, decimal_places=4, null=True)
    adf_statistic = models.DecimalField(max_digits=10, decimal_places=6, null=True)
    adf_pvalue = models.DecimalField(max_digits=10, decimal_places=6, null=True)
    is_cointegrated = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'spread_analytics'
        ordering = ['-timestamp']
        unique_together = [['symbol_pair', 'timeframe', 'timestamp']]
        indexes = [
            models.Index(fields=['symbol_pair', 'timeframe', 'timestamp']),
        ]

class Alert(models.Model):
    ALERT_TYPES = [
        ('zscore_high', 'Z-Score High'),
        ('zscore_low', 'Z-Score Low'),
        ('correlation_break', 'Correlation Break'),
        ('volume_spike', 'Volume Spike'),
        ('price_movement', 'Price Movement'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('triggered', 'Triggered'),
        ('expired', 'Expired'),
    ]
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    symbol_pair = models.CharField(max_length=50, db_index=True)
    condition = models.JSONField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', db_index=True)
    
    triggered_at = models.DateTimeField(null=True, blank=True)
    trigger_value = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'alerts'
        ordering = ['-created_at']

class PriceStats(models.Model):
    symbol = models.CharField(max_length=20, db_index=True)
    timeframe = models.CharField(max_length=3)
    timestamp = models.DateTimeField(db_index=True)
    
    returns = models.DecimalField(max_digits=10, decimal_places=6)
    volatility = models.DecimalField(max_digits=10, decimal_places=6)
    volume_ma = models.DecimalField(max_digits=20, decimal_places=8)
    
    price_change_pct = models.DecimalField(max_digits=10, decimal_places=4)
    high_low_range = models.DecimalField(max_digits=20, decimal_places=8)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'price_stats'
        ordering = ['-timestamp']
        unique_together = [['symbol', 'timeframe', 'timestamp']]