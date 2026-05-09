from __future__ import annotations

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .models import Brand, BrandTemplate
from .serializers import BrandCreateSerializer, BrandSerializer, BrandTemplateSerializer, BrandUpdateSerializer
from .services import can_create_brand


class IsBrandOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_authenticated and obj.user_id == request.user.id)


class BrandViewSet(viewsets.ModelViewSet):
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAuthenticated, IsBrandOwner]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        return Brand.objects.filter(user=self.request.user).prefetch_related("templates")

    def get_serializer_class(self):
        if self.action == "create":
            return BrandCreateSerializer
        if self.action in {"update", "partial_update"}:
            return BrandUpdateSerializer
        return BrandSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        allowed, message = can_create_brand(request.user)
        if not allowed:
            raise PermissionDenied(message)
        brand = serializer.save()
        output = BrandSerializer(brand, context={"request": request})
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["get", "post"], url_path="templates")
    def templates(self, request, pk=None):
        brand = self.get_object()
        if request.method == "GET":
            serializer = BrandTemplateSerializer(brand.templates.all(), many=True)
            return Response(serializer.data)
        serializer = BrandTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(brand=brand)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
