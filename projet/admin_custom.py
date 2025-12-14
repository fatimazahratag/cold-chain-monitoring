from django.contrib.admin.sites import AdminSite
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse

class CustomAdminLoginView(LoginView):
    template_name = "admin/login.html"

    def form_valid(self, form):
        user = form.get_user()
        if user.is_staff:
            return redirect(reverse("admin_custom_dashboard"))
        return super().form_valid(form)

class CustomAdminSite(AdminSite):
    def login(self, request, extra_context=None):
        return CustomAdminLoginView.as_view(
            extra_context=extra_context
        )(request)

custom_admin_site = CustomAdminSite(name="custom_admin")
