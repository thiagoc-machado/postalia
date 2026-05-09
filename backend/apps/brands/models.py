from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Brand(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="brands")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    niche = models.CharField(max_length=255)
    target_audience = models.TextField(blank=True, default="")
    tone_of_voice = models.CharField(max_length=100, blank=True, default="")
    description = models.TextField(blank=True, default="")
    products_services = models.TextField(blank=True, default="")
    website = models.URLField(blank=True, default="")
    website_context = models.JSONField(default=dict, blank=True)
    instagram_handle = models.CharField(max_length=100, blank=True, default="")
    logo = models.ImageField(upload_to="brands/logos/", blank=True, null=True)
    primary_color = models.CharField(max_length=20, blank=True, default="")
    secondary_color = models.CharField(max_length=20, blank=True, default="")
    language = models.CharField(max_length=10, default="en")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("user", "name")]
        ordering = ["-is_default", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "brand"
            candidate = base_slug
            index = 1
            while Brand.objects.filter(user=self.user, slug=candidate).exclude(pk=self.pk).exists():
                index += 1
                candidate = f"{base_slug}-{index}"
            self.slug = candidate
        super().save(*args, **kwargs)


class BrandTemplate(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="templates")
    name = models.CharField(max_length=255)
    base_prompt = models.TextField()
    visual_style = models.TextField(blank=True, default="")
    copywriting_style = models.TextField(blank=True, default="")
    forbidden_topics = models.TextField(blank=True, default="")
    preferred_cta = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("brand", "name")]
        ordering = ["-created_at"]
