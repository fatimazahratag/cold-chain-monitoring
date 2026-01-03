from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views  # <- ajouté

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('DHT.urls')),  # ton app DHT
    # Login/logout
    path('login/', auth_views.LoginView.as_view(template_name='dht/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]
