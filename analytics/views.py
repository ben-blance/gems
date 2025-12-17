from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .tasks import compute_spread_analytics, compute_price_stats
from .models import SpreadAnalytics, PriceStats, Alert
from django.shortcuts import render

def dashboard(request):
    return render(request, 'dashboard.html')

@csrf_exempt
@require_http_methods(["POST"])
def compute_spread(request):
    try:
        data = json.loads(request.body)
        symbol1 = data.get('symbol1', 'BTCUSDT')
        symbol2 = data.get('symbol2', 'ETHUSDT')
        timeframe = data.get('timeframe', '1s')
        window = data.get('window', 60)
        
        task = compute_spread_analytics.delay(symbol1, symbol2, timeframe, window)
        
        return JsonResponse({
            'status': 'processing',
            'task_id': task.id,
            'symbol_pair': f"{symbol1}_{symbol2}"
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def compute_stats(request):
    try:
        data = json.loads(request.body)
        symbol = data.get('symbol', 'BTCUSDT')
        timeframe = data.get('timeframe', '1s')
        
        task = compute_price_stats.delay(symbol, timeframe)
        
        return JsonResponse({
            'status': 'processing',
            'task_id': task.id,
            'symbol': symbol
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_spread_analytics(request):
    symbol1 = request.GET.get('symbol1', 'BTCUSDT')
    symbol2 = request.GET.get('symbol2', 'ETHUSDT')
    symbol_pair = f"{symbol1}_{symbol2}"
    timeframe = request.GET.get('timeframe', '1s')
    limit = int(request.GET.get('limit', 100))
    
    analytics = SpreadAnalytics.objects.filter(
        symbol_pair=symbol_pair,
        timeframe=timeframe
    ).order_by('-timestamp')[:limit]
    
    data = [{
        'timestamp': a.timestamp.isoformat(),
        'symbol1_price': float(a.symbol1_price),
        'symbol2_price': float(a.symbol2_price),
        'hedge_ratio': float(a.hedge_ratio),
        'spread': float(a.spread),
        'z_score': float(a.z_score),
        'rolling_mean': float(a.rolling_mean),
        'rolling_std': float(a.rolling_std),
        'correlation': float(a.correlation) if a.correlation else None,
        'adf_statistic': float(a.adf_statistic) if a.adf_statistic else None,
        'adf_pvalue': float(a.adf_pvalue) if a.adf_pvalue else None,
        'is_cointegrated': a.is_cointegrated
    } for a in analytics]
    
    return JsonResponse({'analytics': data[::-1], 'count': len(data)})

@require_http_methods(["GET"])
def get_price_stats(request):
    symbol = request.GET.get('symbol', 'BTCUSDT')
    timeframe = request.GET.get('timeframe', '1s')
    limit = int(request.GET.get('limit', 100))
    
    stats = PriceStats.objects.filter(
        symbol=symbol,
        timeframe=timeframe
    ).order_by('-timestamp')[:limit]
    
    data = [{
        'timestamp': s.timestamp.isoformat(),
        'returns': float(s.returns),
        'volatility': float(s.volatility),
        'volume_ma': float(s.volume_ma),
        'price_change_pct': float(s.price_change_pct),
        'high_low_range': float(s.high_low_range)
    } for s in stats]
    
    return JsonResponse({'stats': data[::-1], 'count': len(data)})

@csrf_exempt
@require_http_methods(["POST"])
def create_alert(request):
    try:
        data = json.loads(request.body)
        
        alert = Alert.objects.create(
            alert_type=data['alert_type'],
            symbol_pair=data['symbol_pair'],
            condition=data['condition']
        )
        
        return JsonResponse({
            'id': alert.id,
            'alert_type': alert.alert_type,
            'symbol_pair': alert.symbol_pair,
            'status': alert.status
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_alerts(request):
    status = request.GET.get('status')
    symbol_pair = request.GET.get('symbol_pair')
    
    alerts = Alert.objects.all()
    
    if status:
        alerts = alerts.filter(status=status)
    if symbol_pair:
        alerts = alerts.filter(symbol_pair=symbol_pair)
    
    alerts = alerts.order_by('-created_at')[:50]
    
    data = [{
        'id': a.id,
        'alert_type': a.alert_type,
        'symbol_pair': a.symbol_pair,
        'condition': a.condition,
        'status': a.status,
        'triggered_at': a.triggered_at.isoformat() if a.triggered_at else None,
        'trigger_value': float(a.trigger_value) if a.trigger_value else None,
        'created_at': a.created_at.isoformat()
    } for a in alerts]
    
    return JsonResponse({'alerts': data, 'count': len(data)})

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_alert(request, alert_id):
    try:
        alert = Alert.objects.get(id=alert_id)
        alert.delete()
        return JsonResponse({'status': 'deleted'})
    except Alert.DoesNotExist:
        return JsonResponse({'error': 'Alert not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)