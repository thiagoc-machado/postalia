from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class GenerationRequest(models.Model):
    class GenerationType(models.TextChoices):
        TEXT = "text", "Text"
        IMAGE = "image", "Image"
        CAROUSEL = "carousel", "Carousel"
        FULL_POST = "full_post", "Full post"
        IMAGE_PROMPT = "image_prompt", "Image prompt"
        VIDEO_FUTURE = "video_future", "Video future"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        BLOCKED = "blocked", "Blocked"

    class OutputFormat(models.TextChoices):
        FEED_SQUARE = "feed_square", "Feed square"
        FEED_PORTRAIT = "feed_portrait", "Feed portrait"
        STORY = "story", "Story"
        REEL_COVER = "reel_cover", "Reel cover"
        CAROUSEL = "carousel", "Carousel"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="generation_requests")
    brand = models.ForeignKey("brands.Brand", on_delete=models.CASCADE, related_name="generation_requests")
    template = models.ForeignKey(
        "brands.BrandTemplate", on_delete=models.SET_NULL, related_name="generation_requests", null=True, blank=True
    )
    generation_type = models.CharField(max_length=20, choices=GenerationType.choices)
    output_format = models.CharField(max_length=30, choices=OutputFormat.choices, default=OutputFormat.FEED_SQUARE)
    prompt_input = models.TextField()
    generated_text = models.TextField(blank=True, default="")
    generated_payload = models.JSONField(default=dict, blank=True)
    generated_image_url = models.URLField(blank=True, default="")
    ai_provider = models.CharField(max_length=50, blank=True, default="")
    ai_model = models.CharField(max_length=100, blank=True, default="")
    points_spent = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
