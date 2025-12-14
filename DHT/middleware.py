from django.shortcuts import redirect

class AdminRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # غير /admin/ بالضبط
        if request.path == "/admin/":

            # خاص يكون مسجل
            if request.user.is_authenticated:

                # staff ولا superuser
                if request.user.is_staff:
                    return redirect("/admin/custom-dashboard/")

                # user عادي → ممنوع
                return redirect("/403/")

        return self.get_response(request)
