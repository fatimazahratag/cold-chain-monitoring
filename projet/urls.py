from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('DHT.urls')),  # all API endpoints prefixed with /api/
    path('', include('DHT.urls')),      # for dashboard (optional, or use another file)
]
