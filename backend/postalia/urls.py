from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

def healthz(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("healthz/", healthz),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.brands.urls")),
    path("api/", include("apps.subscriptions.urls")),
    path("api/", include("apps.credits.urls")),
    path("api/", include("apps.generations.urls")),
    path("api/", include("apps.payments.urls")),
    path("api/", include("apps.referrals.urls")),
    path("api/", include("apps.ads.urls")),
    path("api/", include("apps.exports.urls")),
    path("api/", include("apps.staff.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
