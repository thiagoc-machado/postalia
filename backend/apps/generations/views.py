from __future__ import annotations

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.common.rates import GenerationThrottle
from apps.exports.serializers import PostExportSerializer
from apps.exports.services import export_generation
from apps.brands.services import can_use_brand_for_generation

from .models import GenerationRequest
from .serializers import GenerationCreateSerializer, GenerationRequestSerializer
from .services import create_generation, list_user_generations


class GenerationListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [GenerationThrottle]

    def get(self, request):
        serializer = GenerationRequestSerializer(list_user_generations(request.user), many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = GenerationCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        brand = serializer.validated_data["brand"]
        template = serializer.validated_data.get("template")
        if brand.user_id != request.user.id:
            return Response({"detail": "You do not own this brand."}, status=status.HTTP_403_FORBIDDEN)
        if template and template.brand_id != brand.id:
            return Response({"detail": "Template does not belong to the selected brand."}, status=status.HTTP_403_FORBIDDEN)
        try:
            generation = create_generation(request.user, serializer.validated_data)
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        output = GenerationRequestSerializer(generation).data
        return Response(output, status=status.HTTP_201_CREATED)


class GenerationPreviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = GenerationCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        brand = serializer.validated_data["brand"]
        template = serializer.validated_data.get("template")
        if brand.user_id != request.user.id:
            return Response({"detail": "You do not own this brand."}, status=status.HTTP_403_FORBIDDEN)
        if template and template.brand_id != brand.id:
            return Response({"detail": "Template does not belong to the selected brand."}, status=status.HTTP_403_FORBIDDEN)
        allowed, reason = can_use_brand_for_generation(request.user, brand)
        if not allowed:
            return Response({"detail": reason or "This brand is not available on your current plan."}, status=status.HTTP_403_FORBIDDEN)
        from .services import preview_generation
        try:
            return Response(preview_generation(request.user, serializer.validated_data))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)


class GenerationExportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk: int):
        generation = get_object_or_404(
            GenerationRequest.objects.select_related("brand", "template"),
            pk=pk,
            user=request.user,
        )
        export = export_generation(generation, request.user)
        return Response(PostExportSerializer(export).data, status=status.HTTP_201_CREATED)
