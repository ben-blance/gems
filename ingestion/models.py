from django.db import models

class RawTick(models.Model):
    symbol = models.CharField(max_length=20, db_index=True)
    timestamp = models.DateTimeField(db_index=True)
    price = models.DecimalField(max_digits=20, decimal_places=8)
    size = models.DecimalField(max_digits=20, decimal_places=8)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'raw_ticks'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
        ]

class ProcessedBar(models.Model):
    TIMEFRAME_CHOICES = [
        ('1s', '1 Second'),
        ('1m', '1 Minute'),
        ('5m', '5 Minutes'),
    ]
    
    symbol = models.CharField(max_length=20, db_index=True)
    timeframe = models.CharField(max_length=3, choices=TIMEFRAME_CHOICES)
    timestamp = models.DateTimeField(db_index=True)
    open = models.DecimalField(max_digits=20, decimal_places=8)
    high = models.DecimalField(max_digits=20, decimal_places=8)
    low = models.DecimalField(max_digits=20, decimal_places=8)
    close = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=20, decimal_places=8)
    tick_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'processed_bars'
        ordering = ['-timestamp']
        unique_together = [['symbol', 'timeframe', 'timestamp']]
        indexes = [
            models.Index(fields=['symbol', 'timeframe', 'timestamp']),
        ]