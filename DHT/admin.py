from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect

from DHT.models import CustomUser

class MyAdminSite(admin.AdminSite):
    site_header = "Cold Chain Admin"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('custom-dashboard-link/', self.admin_view(self.redirect_to_dashboard))
        ]
        return custom_urls + urls

    def redirect_to_dashboard(self, request):
        return redirect('/admin/custom-dashboard/')  # ton custom dashboard

# Remplacer le site admin par défaut si nécessaire
# admin_site = MyAdminSite(name='myadmin')
# admin_site.register(...)  # enregistrer tes modèles ici si tu utilises admin_site
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active')
    list_filter = ('role',)
    search_fields = ('username', 'email')
