# GEMS 




## Architecture Overview

This Django-based ingestion system follows a pipeline architecture:

![gems](https://github.com/user-attachments/assets/35f051af-c9a0-4e54-95ce-5ec58877813b)

**Raw Data → Celery Queue → PostgreSQL → Bar Processing → Analytics**

### Components

1. **Django Producer** (`django_producer.py`): Connects to Binance WebSocket streams, batches ticks, and dispatches to Celery
2. **Celery Workers**: Process tick ingestion and bar aggregation tasks asynchronously
3. **Redis**: Message broker for Celery task queue
4. **PostgreSQL**: Canonical storage for raw ticks and processed bars

## Setup

### Prerequisites
- Python 3.10+
- PostgreSQL
- Redis

### Installation

```bash
chmod +x setup.sh
./setup.sh
```

Or manually:

```bash
pip install -r requirements.txt
createdb quant_db
python manage.py migrate
mkdir -p media/uploads
```

## Running

Start services in separate terminals:

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Celery Worker
celery -A config worker -l info

# Terminal 3: Celery Beat (for periodic bar processing)
celery -A config beat -l info

# Terminal 4: Django Producer
python manage.py django_producer --symbols=btcusdt,ethusdt --batch-size=100

# Terminal 5: Django Server
python manage.py runserver
```

### Initial Setup (run once)

```bash
# Install new dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations analytics
python manage.py migrate

# Setup periodic tasks for 1m and 5m bars
python manage.py setup_periodic_tasks
```

### Manual Analytics Computation (for testing)

```bash
# Compute spread analytics between BTC/ETH
python manage.py compute_analytics --symbol1=BTCUSDT --symbol2=ETHUSDT --timeframe=1s --window=60
```

### Test Analytics API

```bash
# Compute spread
curl -X POST http://localhost:8000/api/analytics/compute-spread/ \
  -H "Content-Type: application/json" \
  -d '{"symbol1": "BTCUSDT", "symbol2": "ETHUSDT", "timeframe": "1s", "window": 60}'

# Get spread analytics
curl "http://localhost:8000/api/analytics/spread/?symbol1=BTCUSDT&symbol2=ETHUSDT&timeframe=1s&limit=50"

# Create alert for z-score > 2
curl -X POST http://localhost:8000/api/analytics/alerts/create/ \
  -H "Content-Type: application/json" \
  -d '{"alert_type": "zscore_high", "symbol_pair": "BTCUSDT_ETHUSDT", "condition": {"threshold": 2.0}}'

# Get active alerts
curl "http://localhost:8000/api/analytics/alerts/?status=active"
```

## API Endpoints

### Ingestion
- `POST /api/ingestion/ingest/` - Ingest tick batch (JSON body with `ticks` array)
- `POST /api/ingestion/upload/` - Upload NDJSON file
- `POST /api/ingestion/process-bars/` - Trigger bar processing (body: `{symbol, timeframe}`)
- `GET /api/ingestion/ticks/?symbol=BTCUSDT&limit=100` - Retrieve raw ticks
- `GET /api/ingestion/bars/?symbol=BTCUSDT&timeframe=1s&limit=100` - Retrieve bars
- `GET /api/ingestion/stats/` - System statistics

### Analytics
- `POST /api/analytics/compute-spread/` - Compute spread analytics (body: `{symbol1, symbol2, timeframe, window}`)
- `POST /api/analytics/compute-stats/` - Compute price stats (body: `{symbol, timeframe}`)
- `GET /api/analytics/spread/?symbol1=BTCUSDT&symbol2=ETHUSDT&timeframe=1s&limit=100` - Get spread analytics
- `GET /api/analytics/stats/?symbol=BTCUSDT&timeframe=1s&limit=100` - Get price stats
- `POST /api/analytics/alerts/create/` - Create alert (body: `{alert_type, symbol_pair, condition}`)
- `GET /api/analytics/alerts/?status=active&symbol_pair=BTCUSDT_ETHUSDT` - Get alerts
- `DELETE /api/analytics/alerts/<id>/delete/` - Delete alert

## Data Models

### RawTick
- Stores individual trade ticks from WebSocket
- Fields: symbol, timestamp, price, size
- Indexed on (symbol, timestamp)

### ProcessedBar
- Aggregated OHLCV bars at multiple timeframes (1s, 1m, 5m)
- Fields: symbol, timeframe, timestamp, OHLC, volume, tick_count
- Unique constraint on (symbol, timeframe, timestamp)

## Design Philosophy

**Loose Coupling**: Producer, worker, storage, and API layers are independent  
**Scalability**: Add more workers or switch data sources without code changes  
**Extensibility**: Easy to add new timeframes, analytics, or data feeds  
**Clarity**: Minimal abstractions, straightforward pipeline flow
