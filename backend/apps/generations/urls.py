from django.urls import path

from .views import GenerationExportView, GenerationListCreateView, GenerationPreviewView

urlpatterns = [
    path("generations/", GenerationListCreateView.as_view(), name="generations"),
    path("generations/preview/", GenerationPreviewView.as_view(), name="generation-preview"),
    path("generations/<int:pk>/export/", GenerationExportView.as_view(), name="generation-export"),
]
