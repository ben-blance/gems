from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('analytics.urls')),
    path('api/ingestion/', include('ingestion.urls')),
    path('api/analytics/', include('analytics.urls')),
]