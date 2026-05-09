from __future__ import annotations

from io import BytesIO
import html
import ipaddress
import re
import socket
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

from apps.accounts.models import User
from apps.subscriptions.services import get_user_subscription

from .models import Brand


def get_default_brand(user: User) -> Brand | None:
    return Brand.objects.filter(user=user, is_default=True).first() or Brand.objects.filter(user=user).first()


def can_create_brand(user: User) -> tuple[bool, str | None]:
    subscription = get_user_subscription(user)
    current = Brand.objects.filter(user=user).count()
    if current >= subscription.plan.brand_limit:
        return False, f"Brand limit reached for {subscription.plan.code} plan."
    return True, None


def can_use_brand_for_generation(user: User, brand: Brand) -> tuple[bool, str | None]:
    if brand.user_id != user.id:
        return False, "You do not own this brand."
    subscription = get_user_subscription(user)
    owned_brands = Brand.objects.filter(user=user).count()
    if owned_brands > subscription.plan.brand_limit and not brand.is_default:
        return False, "Select your default brand or upgrade your plan to use this brand."
    return True, None


def refresh_brand_website_context(brand: Brand) -> dict[str, Any]:
    context = extract_website_context(brand.website)
    brand.website_context = context
    brand.save(update_fields=["website_context", "updated_at"])
    return context


def normalize_brand_logo(uploaded_file, *, size: int = 1024) -> ContentFile:
    try:
        with Image.open(uploaded_file) as image:
            image = ImageOps.exif_transpose(image)
            if image.mode not in {"RGBA", "RGB"}:
                image = image.convert("RGBA")
            else:
                image = image.convert("RGBA")
            squared = ImageOps.fit(image, (size, size), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    except UnidentifiedImageError as exc:
        raise ValueError("Invalid logo image.") from exc

    buffer = BytesIO()
    squared.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    stem = Path(getattr(uploaded_file, "name", "logo")).stem or "logo"
    filename = f"{re.sub(r'[^a-zA-Z0-9_-]+', '-', stem).strip('-').lower() or 'logo'}.png"
    return ContentFile(buffer.getvalue(), name=filename)


def extract_website_context(website: str) -> dict[str, Any]:
    normalized = (website or "").strip()
    if not normalized:
        return {"status": "empty"}
    parsed = urlsplit(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return {"status": "invalid", "source_url": normalized}
    if not _is_public_hostname(parsed.hostname, parsed.port, parsed.scheme):
        return {"status": "blocked", "source_url": normalized, "error": "Private or local hosts are not allowed."}
    try:
        response = httpx.get(
            normalized,
            timeout=getattr(settings, "WEBSITE_CONTEXT_TIMEOUT_SECONDS", 5.0),
            follow_redirects=True,
            headers={"User-Agent": "PostaliaBot/1.0"},
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return {"status": "unavailable", "source_url": normalized, "error": exc.__class__.__name__}

    html_content = response.text[:250000]
    title = _extract_tag_content(html_content, "title")
    description = _extract_meta_content(html_content, ("description", "og:description"))
    og_title = _extract_meta_content(html_content, ("og:title",))
    og_image = _extract_meta_content(html_content, ("og:image", "twitter:image"))
    theme_color = _extract_meta_content(html_content, ("theme-color",))
    colors = _extract_colors(html_content, limit=6)
    text_excerpt = _extract_text_excerpt(html_content)
    summary_parts = [
        part
        for part in [
            og_title or title,
            description,
            f"Colors: {', '.join(colors)}" if colors else "",
            text_excerpt,
        ]
        if part
    ]
    return {
        "status": "captured",
        "source_url": normalized,
        "hostname": parsed.hostname,
        "title": og_title or title,
        "description": description,
        "og_image": og_image,
        "theme_color": theme_color,
        "colors": colors,
        "text_excerpt": text_excerpt,
        "summary": " | ".join(summary_parts[:4]),
    }


def format_website_context(context: dict[str, Any] | None) -> str:
    if not context or not isinstance(context, dict):
        return ""
    if context.get("status") != "captured":
        return ""
    parts = [
        f"Website title: {context.get('title') or ''}".strip(),
        f"Website description: {context.get('description') or ''}".strip(),
        f"Website colors: {', '.join(context.get('colors') or [])}".strip(),
        f"Website excerpt: {context.get('text_excerpt') or ''}".strip(),
    ]
    return "\n".join(part for part in parts if part and not part.endswith(":"))


def _is_public_hostname(hostname: str, port: int | None, scheme: str) -> bool:
    try:
        infos = socket.getaddrinfo(hostname, port or (443 if scheme == "https" else 80), type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False
    for info in infos:
        address = info[4][0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            return False
        if any(
            [
                ip.is_private,
                ip.is_loopback,
                ip.is_link_local,
                ip.is_reserved,
                ip.is_multicast,
                ip.is_unspecified,
            ]
        ):
            return False
    return True


def _extract_tag_content(html_content: str, tag: str) -> str:
    match = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", html_content, flags=re.I | re.S)
    if not match:
        return ""
    return html.unescape(_clean_text(match.group(1)))


def _extract_meta_content(html_content: str, names: tuple[str, ...]) -> str:
    for name in names:
        patterns = [
            rf'<meta[^>]+(?:name|property)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:name|property)=["\']{re.escape(name)}["\']',
        ]
        for pattern in patterns:
            match = re.search(pattern, html_content, flags=re.I | re.S)
            if match:
                return html.unescape(_clean_text(match.group(1)))
    return ""


def _extract_colors(html_content: str, limit: int = 5) -> list[str]:
    colors: list[str] = []
    for match in re.findall(r"#(?:[0-9a-fA-F]{3}){1,2}\b", html_content):
        normalized = match.lower()
        if normalized not in colors:
            colors.append(normalized)
        if len(colors) >= limit:
            break
    return colors


def _extract_text_excerpt(html_content: str) -> str:
    cleaned = re.sub(r"(?is)<script.*?</script>", " ", html_content)
    cleaned = re.sub(r"(?is)<style.*?</style>", " ", cleaned)
    cleaned = re.sub(r"(?is)<noscript.*?</noscript>", " ", cleaned)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = html.unescape(cleaned)
    cleaned = _clean_text(cleaned)
    return cleaned[:260]


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
