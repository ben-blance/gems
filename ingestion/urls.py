from django.urls import path
from . import views

urlpatterns = [
    path('ingest/', views.ingest_ticks, name='ingest_ticks'),
    path('upload/', views.upload_ndjson, name='upload_ndjson'),
    path('process-bars/', views.trigger_bar_processing, name='trigger_bar_processing'),
    path('ticks/', views.get_ticks, name='get_ticks'),
    path('bars/', views.get_bars, name='get_bars'),
    path('stats/', views.stats, name='stats'),
]