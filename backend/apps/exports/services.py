from __future__ import annotations

import textwrap
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image, ImageDraw, ImageFont

from apps.subscriptions.services import get_user_subscription

from .models import PostExport


def _output_size(output_format: str) -> tuple[int, int]:
    mapping = {
        "feed_square": (1080, 1080),
        "feed_portrait": (1080, 1350),
        "story": (1080, 1920),
        "reel_cover": (1080, 1920),
        "carousel": (1080, 1080),
    }
    return mapping.get(output_format, (1080, 1080))


def export_generation(generation_request, user) -> PostExport:
    subscription = get_user_subscription(user)
    has_watermark = subscription.plan.has_watermark
    width, height = _output_size(generation_request.output_format)
    image = Image.new("RGB", (width, height), color=(18, 24, 38))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    lines = textwrap.wrap(generation_request.generated_text or generation_request.prompt_input[:500], width=48)
    y = 80
    for line in lines[:20]:
        draw.text((60, y), line, fill=(245, 245, 245), font=font)
        y += 28

    brand_line = generation_request.brand.name
    if generation_request.brand.instagram_handle:
        brand_line += f" @{generation_request.brand.instagram_handle}"
    draw.text((60, height - 140), brand_line, fill=(180, 220, 255), font=font)
    if has_watermark:
        draw.text((60, height - 100), "Created with Postalia", fill=(255, 205, 90), font=font)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    file_name = f"exports/export-{generation_request.id}.png"
    file = ContentFile(buffer.getvalue(), name=f"export-{generation_request.id}.png")
    path = default_storage.save(file_name, file)
    return PostExport.objects.create(
        user=user,
        brand=generation_request.brand,
        generation_request=generation_request,
        export_type=PostExport.ExportType.PNG,
        file=path,
        has_watermark=has_watermark,
    )
