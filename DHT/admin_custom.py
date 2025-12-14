from django.contrib.admin.sites import AdminSite
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse

class CustomAdminLoginView(LoginView):
    template_name = "admin/login.html"

    def get_success_url(self):
        """Toujours rediriger vers custom dashboard pour le staff."""
        if self.request.user.is_staff:
            return reverse("admin_custom_dashboard")
        return super().get_success_url()

class CustomAdminSite(AdminSite):
    def login(self, request, extra_context=None):
        return CustomAdminLoginView.as_view(
            extra_context=extra_context
        )(request)

custom_admin_site = CustomAdminSite(name="custom_admin")
