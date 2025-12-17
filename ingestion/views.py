from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .tasks import ingest_tick_batch, process_ticks_to_bars, process_ndjson_file
from .models import RawTick, ProcessedBar
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os

@csrf_exempt
@require_http_methods(["POST"])
def ingest_ticks(request):
    try:
        data = json.loads(request.body)
        ticks = data.get('ticks', [])
        
        if not ticks:
            return JsonResponse({'error': 'No ticks provided'}, status=400)
        
        task = ingest_tick_batch.delay(ticks)
        return JsonResponse({
            'status': 'processing',
            'task_id': task.id,
            'tick_count': len(ticks)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def upload_ndjson(request):
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        file = request.FILES['file']
        file_path = default_storage.save(f'uploads/{file.name}', ContentFile(file.read()))
        full_path = os.path.join(default_storage.location, file_path)
        
        task = process_ndjson_file.delay(full_path)
        
        return JsonResponse({
            'status': 'processing',
            'task_id': task.id,
            'filename': file.name
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["POST"])
def trigger_bar_processing(request):
    try:
        data = json.loads(request.body)
        symbol = data.get('symbol')
        timeframe = data.get('timeframe', '1s')
        
        if not symbol:
            return JsonResponse({'error': 'Symbol required'}, status=400)
        
        task = process_ticks_to_bars.delay(symbol, timeframe)
        
        return JsonResponse({
            'status': 'processing',
            'task_id': task.id,
            'symbol': symbol,
            'timeframe': timeframe
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_ticks(request):
    symbol = request.GET.get('symbol')
    limit = int(request.GET.get('limit', 100))
    
    query = RawTick.objects.all()
    if symbol:
        query = query.filter(symbol=symbol)
    
    ticks = query[:limit]
    
    data = [{
        'symbol': t.symbol,
        'timestamp': t.timestamp.isoformat(),
        'price': float(t.price),
        'size': float(t.size)
    } for t in ticks]
    
    return JsonResponse({'ticks': data, 'count': len(data)})

@require_http_methods(["GET"])
def get_bars(request):
    symbol = request.GET.get('symbol')
    timeframe = request.GET.get('timeframe', '1s')
    limit = int(request.GET.get('limit', 100))
    
    query = ProcessedBar.objects.all()
    if symbol:
        query = query.filter(symbol=symbol)
    query = query.filter(timeframe=timeframe)
    
    bars = query[:limit]
    
    data = [{
        'symbol': b.symbol,
        'timeframe': b.timeframe,
        'timestamp': b.timestamp.isoformat(),
        'open': float(b.open),
        'high': float(b.high),
        'low': float(b.low),
        'close': float(b.close),
        'volume': float(b.volume),
        'tick_count': b.tick_count
    } for b in bars]
    
    return JsonResponse({'bars': data, 'count': len(data)})

@require_http_methods(["GET"])
def stats(request):
    tick_count = RawTick.objects.count()
    bar_count = ProcessedBar.objects.count()
    symbols = list(RawTick.objects.values_list('symbol', flat=True).distinct())
    
    return JsonResponse({
        'tick_count': tick_count,
        'bar_count': bar_count,
        'symbols': symbols
    })