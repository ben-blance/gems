from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('compute-spread/', views.compute_spread, name='compute_spread'),
    path('compute-stats/', views.compute_stats, name='compute_stats'),
    path('spread/', views.get_spread_analytics, name='get_spread_analytics'),
    path('stats/', views.get_price_stats, name='get_price_stats'),
    path('alerts/', views.get_alerts, name='get_alerts'),
    path('alerts/create/', views.create_alert, name='create_alert'),
    path('alerts/<int:alert_id>/delete/', views.delete_alert, name='delete_alert'),
]