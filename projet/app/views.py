from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

class AdminLoginRedirect(LoginView):
    template_name = "admin/login.html"

    def get_success_url(self):
        return reverse_lazy("admin_custom_dashboard")
