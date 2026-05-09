from __future__ import annotations

from rest_framework import permissions
from rest_framework.generics import ListAPIView

from .models import PostExport
from .serializers import PostExportSerializer


class ExportListView(ListAPIView):
    serializer_class = PostExportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PostExport.objects.filter(user=self.request.user).select_related("brand", "generation_request")
