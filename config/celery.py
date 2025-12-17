import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# # Explicit imports to ensure tasks are discovered
# from analytics import tasks as analytics_tasks  # noqa
# from ingestion import tasks as ingestion_tasks  # noqa