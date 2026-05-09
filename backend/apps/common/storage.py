from __future__ import annotations

import uuid
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image, ImageDraw, ImageFont


def create_placeholder_image(text: str, size: tuple[int, int] = (1080, 1080)) -> ContentFile:
    image = Image.new("RGB", size, color=(18, 24, 38))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    lines = _wrap_text(text, 40)
    y = size[1] // 4
    for line in lines:
        draw.text((60, y), line, fill=(245, 245, 245), font=font)
        y += 24
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=f"placeholder-{uuid.uuid4().hex}.png")


def save_generated_file(file_content: ContentFile, folder: str) -> str:
    path = default_storage.save(f"{folder}/{file_content.name}", file_content)
    url = default_storage.url(path)
    if url.startswith("/"):
        return f"{settings.APP_BASE_URL}{url}"
    return url


def _wrap_text(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        if len(" ".join(current + [word])) <= width:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines
