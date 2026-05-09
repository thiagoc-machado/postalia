from rest_framework import serializers

from django.conf import settings

from .models import PostExport


class PostExportSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    def get_file(self, obj):
        url = obj.file.url
        if url.startswith("/"):
            return f"{settings.APP_BASE_URL}{url}"
        return url

    class Meta:
        model = PostExport
        fields = ["id", "user", "brand", "generation_request", "export_type", "file", "has_watermark", "created_at"]
