from django.urls import path

from .views import ExportListView

urlpatterns = [
    path("exports/", ExportListView.as_view(), name="exports"),
]
