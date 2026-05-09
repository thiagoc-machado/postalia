from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class PostExport(models.Model):
    class ExportType(models.TextChoices):
        PNG = "png", "PNG"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="post_exports")
    brand = models.ForeignKey("brands.Brand", on_delete=models.CASCADE, related_name="exports")
    generation_request = models.ForeignKey(
        "generations.GenerationRequest", on_delete=models.CASCADE, related_name="exports"
    )
    export_type = models.CharField(max_length=20, choices=ExportType.choices, default=ExportType.PNG)
    file = models.FileField(upload_to="exports/")
    has_watermark = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
