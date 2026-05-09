from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import re
import time
import textwrap
import unicodedata
import uuid
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from PIL import Image, ImageColor, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

BASE_DIR = Path("/data")
BASE_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Postalia Demo AI")
app.mount("/files", StaticFiles(directory=str(BASE_DIR)), name="files")


class TextRequest(BaseModel):
    prompt: str
    generation_type: str
    title: str | None = ""
    cta: str | None = ""


class ImageRequest(BaseModel):
    prompt: str
    output_format: str
    style: str = "realistic"


def _seed(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _thinking_delay(prompt: str, generation_type: str, style: str = "realistic") -> None:
    seed = int(_seed(f"{prompt}|{generation_type}|{style}"), 16)
    base = {
        "image": 2.2,
        "full_post": 1.9,
        "carousel": 1.4,
        "image_prompt": 0.85,
    }.get(generation_type, 0.8)
    style_key = (style or "").strip().lower()
    if style_key in {"realistic", "editorial", "premium_clean"}:
        base += 0.35
    if "website context" in prompt.lower():
        base += 0.25
    jitter = ((seed % 7) * 0.11) + random.uniform(0.05, 0.18)
    time.sleep(min(base + jitter, 3.2))


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _compact_hashtag(value: str, max_length: int = 28) -> str:
    tokens = re.findall(r"[a-z0-9]+", _strip_accents(value).lower())
    tokens = [
        token
        for token in tokens
        if token
        not in {
            "and",
            "the",
            "for",
            "with",
            "de",
            "da",
            "do",
            "del",
            "y",
            "e",
            "para",
            "por",
            "la",
            "el",
            "los",
            "las",
            "um",
            "uma",
            "uns",
            "unas",
        }
    ]
    if not tokens:
        return ""
    slug = "".join(tokens)
    return f"#{slug[:max_length]}"


def _tone_phrase(fields: dict[str, str]) -> str:
    for key in ("brand voice", "tone"):
        value = (fields.get(key) or "").strip()
        if value and not _is_generic_text(value):
            return value
    return "friendly"


def _variation_index(fields: dict[str, str], salt: str, size: int) -> int:
    basis = "|".join(
        [
            fields.get("brand", ""),
            fields.get("topic", ""),
            fields.get("product/service", ""),
            fields.get("campaign theme", ""),
            fields.get("special offer", ""),
            fields.get("objective", ""),
            fields.get("language", ""),
            fields.get("niche", ""),
            fields.get("audience", ""),
            fields.get("brand description", ""),
            fields.get("brand products/services", ""),
            fields.get("website title", ""),
            fields.get("website description", ""),
            fields.get("website excerpt", ""),
            fields.get("brand template", ""),
            salt,
        ]
    )
    return int(_seed(basis), 16) % max(size, 1)


def _build_hashtags(fields: dict[str, str], language: str) -> list[str]:
    tags: list[str] = ["#postalia"]
    brand = (fields.get("brand") or "").strip()
    niche = (fields.get("niche") or "").strip()
    audience = (fields.get("audience") or "").strip()
    subject = _resolve_subject(fields)
    instagram_handle = (fields.get("instagram handle") or "").strip().lstrip("@")

    for value in [brand, instagram_handle, niche, audience, subject]:
        tag = f"#{_slugify_hashtag(value)}" if value else ""
        if tag and tag not in tags:
            if len(tag) > 20 and value not in {brand, instagram_handle}:
                continue
            tags.append(tag)

    if _has_restaurant_context(fields):
        language_tags = {
            "es": ["#restaurantes", "#pedidosonline", "#qrcode", "#automatizacion", "#pedidosporqrcode", "#automacionderestaurantes"],
            "pt": ["#restaurantes", "#pedidosonline", "#qrcode", "#automacao", "#pedidosporqrcode", "#automacaodepedidos"],
            "en": ["#restaurants", "#onlineorders", "#qrcode", "#automation", "#restaurantautomation", "#ordersoftware"],
        }
    else:
        language_tags = {
            "es": ["#marketingdigital", "#negocios", "#crecimiento"],
            "pt": ["#marketingdigital", "#negociosdigitais", "#crescimento"],
            "en": ["#marketing", "#businessgrowth", "#contentstrategy"],
        }
    for tag in language_tags.get(language, language_tags["en"]):
        if tag not in tags:
            tags.append(tag)

    if _has_restaurant_context(fields):
        restaurant_tags = {
            "es": ["#automacionderestaurantes", "#pedidosporqrcode"],
            "pt": ["#automacaodepedidos", "#pedidosporqrcode"],
            "en": ["#restaurantautomation", "#ordersoftware"],
        }.get(language, [])
        for tag in restaurant_tags:
            if tag not in tags:
                tags.append(tag)

    return tags[:8]


def _package(prompt: str, title: str, cta: str) -> dict:
    seed = _seed(prompt)
    fields = _prompt_fields(prompt)
    language = (fields.get("language") or "en").lower()
    brand = (fields.get("brand") or "Postalia").strip() or "Postalia"
    niche = (fields.get("niche") or "brand").strip()
    audience = (fields.get("audience") or "your audience").strip()
    subject = _resolve_subject(fields)
    objective = (fields.get("objective") or "sell").strip()
    tone = _tone_phrase(fields)
    creative_angle = _resolve_creative_angle(fields)
    instagram_handle = (fields.get("instagram handle") or "").strip().lstrip("@")
    website_hint = fields.get("website title") or fields.get("website description") or fields.get("website excerpt") or ""
    cta_text = cta or {"es": "Solicita una demo", "pt": "Peça uma demonstração"}.get(language, "Book a demo")
    hashtags = _build_hashtags(fields, language)
    has_restaurant = _has_restaurant_context(fields)
    return {
        "title": title or f"Postalia Idea {seed}",
        "short_hook": _resolve_short_hook(fields),
        "caption": _caption_from_prompt(fields),
        "hashtags": hashtags,
        "carousel_slides": [
            {
                "es": "Slide 1: Menos filas",
                "pt": "Slide 1: Menos filas",
            }.get(language, "Slide 1: More orders"),
            {
                "es": "Slide 2: Menos errores",
                "pt": "Slide 2: Menos erros",
            }.get(language, "Slide 2: Less mistakes"),
            {
                "es": "Slide 3: QR, tablets y cocina sincronizada",
                "pt": "Slide 3: QR, tablets e cozinha sincronizada",
            }.get(language, "Slide 3: QR, tablets and kitchen sync"),
            {
                "es": "Slide 4: Control en tiempo real",
                "pt": "Slide 4: Controle em tempo real",
            }.get(language, "Slide 4: Real-time control"),
            f"Slide 5: {cta_text}",
        ],
        "image_prompt": (
            f"Premium Instagram publication for {brand} in the {niche} niche. "
            f"Create a real social ad with a strong hero headline, brand colors, "
            f"a clean poster-like layout, one primary product or operation mockup, support copy for {audience}, "
            f"and a CTA that emphasizes {objective}. "
            f"Style should feel {tone}, polished and ready to publish. "
            f"Reference the website context when available: {website_hint}. "
            f"Subject focus: {subject}. "
            f"{'Use QR ordering, kitchen sync and restaurant operation cues without sidebar dashboards or charts.' if has_restaurant else 'Use the strongest product or service cues from the brand context.'}"
            f"{f' Include the Instagram handle {instagram_handle} if it is visible in the brand context.' if instagram_handle else ''}"
        ),
        "call_to_action": cta_text,
        "recommended_design_notes": (
            f"Use {brand} colors when available. Keep the layout premium, high-contrast and aligned with {niche}. "
            "Include a clear headline, supporting UI or product mockup, and a strong CTA. "
            "Keep the visual tone consistent with the website and campaign context. "
            "If the brand serves restaurants, emphasize QR ordering, tablets, kitchen flow and operational control."
        ),
    }


def _format_size(output_format: str) -> tuple[int, int]:
    return {
        "feed_square": (1080, 1080),
        "feed_portrait": (1080, 1350),
        "story": (1080, 1920),
        "reel_cover": (1080, 1920),
        "carousel": (1080, 1080),
    }.get(output_format, (1080, 1080))


def _palette(seed: str) -> dict[str, tuple[int, int, int]]:
    base = int(seed[:6], 16)
    hues = [
        (base >> 0) & 0xFF,
        (base >> 8) & 0xFF,
        (base >> 16) & 0xFF,
    ]
    primary = (60 + hues[0] % 150, 70 + hues[1] % 120, 110 + hues[2] % 120)
    accent = (240 - hues[2] % 80, 120 + hues[0] % 100, 70 + hues[1] % 90)
    surface = (18, 24, 38)
    paper = (245, 246, 250)
    text = (240, 244, 248)
    muted = (182, 190, 205)
    return {
        "primary": primary,
        "accent": accent,
        "surface": surface,
        "paper": paper,
        "text": text,
        "muted": muted,
    }


def _style_profile(style: str, seed: str) -> dict[str, object]:
    style_key = (style or "realistic").strip().lower()
    base = _palette(seed)
    profiles: dict[str, dict[str, object]] = {
        "realistic": {"label": "Realistic", "palette": base, "mode": "clean"},
        "animated": {
            "label": "Animated",
            "palette": {"primary": (55, 125, 255), "accent": (255, 120, 168), "surface": (22, 28, 42), "paper": (251, 247, 255), "text": (245, 247, 255), "muted": (154, 162, 186)},
            "mode": "playful",
        },
        "cartoon": {
            "label": "Cartoon",
            "palette": {"primary": (255, 173, 31), "accent": (87, 105, 255), "surface": (28, 29, 35), "paper": (255, 252, 243), "text": (255, 255, 255), "muted": (126, 136, 152)},
            "mode": "playful",
        },
        "ghibli": {
            "label": "Ghibli inspired",
            "palette": {"primary": (86, 142, 100), "accent": (234, 189, 124), "surface": (28, 46, 38), "paper": (249, 246, 236), "text": (244, 247, 242), "muted": (145, 158, 148)},
            "mode": "warm",
        },
        "stick_figure": {
            "label": "Stick figure",
            "palette": {"primary": (52, 58, 72), "accent": (250, 142, 62), "surface": (20, 22, 27), "paper": (252, 252, 252), "text": (255, 255, 255), "muted": (120, 127, 141)},
            "mode": "minimal",
        },
        "isometric": {
            "label": "Isometric",
            "palette": {"primary": (58, 90, 194), "accent": (78, 203, 196), "surface": (19, 28, 45), "paper": (245, 248, 252), "text": (244, 247, 255), "muted": (149, 160, 180)},
            "mode": "clean",
        },
        "flat": {
            "label": "Flat design",
            "palette": {"primary": (36, 128, 106), "accent": (237, 106, 90), "surface": (26, 34, 30), "paper": (250, 250, 250), "text": (244, 247, 244), "muted": (130, 141, 134)},
            "mode": "minimal",
        },
        "minimal": {
            "label": "Minimal",
            "palette": {"primary": (34, 38, 54), "accent": (179, 139, 92), "surface": (18, 20, 28), "paper": (252, 251, 248), "text": (255, 255, 255), "muted": (132, 136, 147)},
            "mode": "minimal",
        },
        "three_d": {
            "label": "3D",
            "palette": {"primary": (100, 76, 255), "accent": (53, 201, 255), "surface": (24, 26, 42), "paper": (247, 248, 255), "text": (247, 249, 255), "muted": (152, 159, 186)},
            "mode": "glow",
        },
        "cyberpunk": {
            "label": "Cyberpunk",
            "palette": {"primary": (17, 242, 224), "accent": (255, 56, 168), "surface": (8, 12, 27), "paper": (14, 18, 34), "text": (240, 248, 255), "muted": (132, 143, 173)},
            "mode": "neon",
        },
        "editorial": {
            "label": "Editorial",
            "palette": {"primary": (28, 31, 40), "accent": (197, 165, 113), "surface": (22, 24, 30), "paper": (248, 244, 238), "text": (252, 252, 252), "muted": (137, 139, 145)},
            "mode": "luxury",
        },
        "premium_clean": {
            "label": "Premium clean",
            "palette": {"primary": (18, 54, 92), "accent": (239, 183, 88), "surface": (15, 24, 37), "paper": (251, 250, 247), "text": (247, 249, 255), "muted": (145, 153, 170)},
            "mode": "luxury",
        },
        "watercolor": {
            "label": "Watercolor",
            "palette": {"primary": (120, 144, 214), "accent": (239, 165, 188), "surface": (36, 42, 63), "paper": (252, 248, 245), "text": (246, 248, 255), "muted": (146, 151, 168)},
            "mode": "soft",
        },
    }
    profile = profiles.get(style_key, profiles["realistic"]).copy()
    profile["style_key"] = style_key
    if "palette" not in profile:
        profile["palette"] = base
    return profile


def _prompt_fields(prompt: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in prompt.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip().lower()] = value.strip()
    return fields


def _is_generic_text(value: str) -> bool:
    normalized = re.sub(r"\s+", " ", value).strip().lower()
    return normalized in {
        "",
        "-",
        "n/a",
        "none",
        "your offer",
        "your audience",
        "your topic",
        "your brand",
        "offer",
        "audience",
        "topic",
        "brand",
        "content",
        "post",
        "publication",
        "moderno",
        "modern",
        "teste",
        "test",
    }


def _has_restaurant_context(fields: dict[str, str]) -> bool:
    combined = _strip_accents(
        " ".join(
        [
            fields.get("niche", ""),
            fields.get("audience", ""),
            fields.get("topic", ""),
            fields.get("product/service", ""),
            fields.get("brand template", ""),
            fields.get("brand description", ""),
            fields.get("brand products/services", ""),
            fields.get("website description", ""),
            fields.get("website excerpt", ""),
        ]
        )
    ).lower()
    return any(
        keyword in combined
        for keyword in [
            "restaurant",
            "restaurante",
            "restaurantes",
            "bar",
            "bares",
            "donos de restaurantes",
            "donos de bares",
            "food service",
            "restaurante",
            "lanchonete",
            "lanchonetes",
            "menu",
            "pedido",
            "pedidos",
            "qrcode",
            "qr code",
            "qr",
            "totem",
            "totens",
            "tablets",
            "tablet",
            "cozinha",
            "cozinhas",
            "kitchen",
            "sala",
            "salao",
            "salon",
            "camareros",
            "garcon",
            "operacion",
            "operacao",
        ]
    )


def _resolve_subject(fields: dict[str, str]) -> str:
    candidates = [
        fields.get("product/service"),
        fields.get("topic"),
        fields.get("brand products/services"),
        fields.get("brand description"),
        fields.get("brand template"),
        fields.get("website description"),
        fields.get("website excerpt"),
    ]
    for candidate in candidates:
        text = (candidate or "").strip()
        if text and not _is_generic_text(text):
            return text
    return fields.get("niche", "").strip() or "your offer"


def _resolve_creative_angle(fields: dict[str, str]) -> str:
    angle = (fields.get("creative angle") or "").strip()
    if angle and not _is_generic_text(angle):
        return angle
    language = (fields.get("language") or "en").lower()
    if _has_restaurant_context(fields):
        options = {
            "es": [
                "hora pico con más control",
                "pedidos por QR sin fricción",
                "cocina y sala en sincronía",
                "menos errores en cada turno",
                "operación clara en cada mesa",
                "servicio más rápido y ordenado",
            ],
            "pt": [
                "hora de pico com mais controle",
                "pedidos por QR sem fricção",
                "cozinha e salão em sincronia",
                "menos erros em cada turno",
                "operação clara em cada mesa",
                "serviço mais rápido e organizado",
            ],
        }.get(
            language,
            [
                "peak hours with more control",
                "QR orders without friction",
                "kitchen and floor in sync",
                "fewer mistakes on every shift",
                "clear operation at every table",
                "faster and more organized service",
            ],
        )
    else:
        options = {
            "es": [
                "una oferta más clara",
                "un mensaje más directo",
                "más confianza para decidir",
                "una propuesta fácil de entender",
                "más valor en menos palabras",
                "un flujo más simple",
            ],
            "pt": [
                "uma oferta mais clara",
                "uma mensagem mais direta",
                "mais confiança para decidir",
                "uma proposta fácil de entender",
                "mais valor em menos palavras",
                "um fluxo mais simples",
            ],
        }.get(
            language,
            [
                "a clearer offer",
                "a more direct message",
                "more confidence to decide",
                "a proposal that's easy to understand",
                "more value in fewer words",
                "a simpler flow",
            ],
    )
    return options[_variation_index(fields, "creative angle", len(options))]


def _resolve_short_hook(fields: dict[str, str]) -> str:
    language = (fields.get("language") or "en").lower()
    if _has_restaurant_context(fields):
        subject_text = _strip_accents(
            " ".join(
                [
                    fields.get("topic", ""),
                    fields.get("product/service", ""),
                    fields.get("campaign theme", ""),
                    fields.get("special offer", ""),
                    fields.get("brand description", ""),
                    fields.get("brand products/services", ""),
                ]
            )
        ).lower()
        if any(token in subject_text for token in ["fila", "wait", "espera"]):
            return {
                "es": "Menos caos en hora pico.",
                "pt": "Menos caos no pico.",
            }.get(language, "Less chaos at peak hours.")
        if any(token in subject_text for token in ["qr", "qrcode", "codigo", "mesa"]):
            return {
                "es": "QR, cocina y sala sincronizados.",
                "pt": "QR, cozinha e salão sincronizados.",
            }.get(language, "QR, kitchen and floor synced.")
        if any(token in subject_text for token in ["control", "painel", "operacional", "admin"]):
            return {
                "es": "Más control en cada turno.",
                "pt": "Mais controle em cada turno.",
            }.get(language, "More control on every shift.")
        if any(token in subject_text for token in ["rap", "speed", "rápido", "veloc", "tempo real"]):
            return {
                "es": "Tu operación, más rápida.",
                "pt": "Sua operação, mais rápida.",
            }.get(language, "Your operation, faster.")
        options = {
            "es": [
                "Más pedidos, menos espera.",
                "Menos fricción, más servicio.",
                "Atiende mejor sin perder control.",
                "Pedidos claros desde la primera mesa.",
                "QR y cocina sincronizados.",
                "Más ritmo en cada turno.",
            ],
            "pt": [
                "Mais pedidos, menos espera.",
                "Menos fricção, mais serviço.",
                "Atenda melhor sem perder o controle.",
                "Pedidos claros desde a primeira mesa.",
                "QR e cozinha sincronizados.",
                "Mais ritmo em cada turno.",
            ],
        }.get(
            language,
            [
                "More orders, less waiting.",
                "Less friction, better service.",
                "Serve better without losing control.",
                "Clear orders from the first table.",
                "QR and kitchen synced.",
                "More rhythm on every shift.",
            ],
        )
        return options[_variation_index(fields, "short_hook", len(options))]
    subject = _resolve_subject(fields)
    angle = _resolve_creative_angle(fields)
    options = {
        "es": [
            f"Una forma más clara de {subject.lower()}",
            f"Más claridad para {angle}",
            f"Haz que {subject.lower()} se entienda mejor",
            f"Convierte {subject.lower()} en una historia más simple",
        ],
        "pt": [
            f"Uma forma mais clara de {subject.lower()}",
            f"Mais clareza para {angle}",
            f"Faça {subject.lower()} ser entendido melhor",
            f"Transforme {subject.lower()} em uma história mais simples",
        ],
    }.get(
        language,
        [
            f"A clearer way to {subject.lower()}",
            f"More clarity for {angle}",
            f"Make {subject.lower()} easier to understand",
            f"Turn {subject.lower()} into a simpler story",
        ],
    )
    return options[_variation_index(fields, "short_hook", len(options))]


def _slugify_hashtag(value: str) -> str:
    tokens = re.findall(r"[a-z0-9]+", value.lower())
    if not tokens:
        return "postalia"
    slug = "".join(tokens)
    return slug[:28] or "postalia"


def _parse_color(value: str | None, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    cleaned = (value or "").strip()
    if not cleaned or cleaned in {"not set", "unset", "none"}:
        return fallback
    try:
        return ImageColor.getrgb(cleaned)
    except ValueError:
        return fallback


def _caption_from_prompt(fields: dict[str, str]) -> str:
    language = (fields.get("language") or "en").lower()
    brand = (fields.get("brand") or "Your brand").strip() or "Your brand"
    audience = (fields.get("audience") or "your audience").strip()
    objective = (fields.get("objective") or "sell").strip()
    tone = _tone_phrase(fields)
    subject = _resolve_subject(fields)
    creative_angle = _resolve_creative_angle(fields)
    special_offer = (fields.get("special offer") or "").strip()
    campaign_theme = (fields.get("campaign theme") or "").strip()

    if _has_restaurant_context(fields):
        hook_options = {
            "es": [
                "Más pedidos, menos espera.",
                "Menos caos en hora pico.",
                "QR, cocina y sala sincronizados.",
                f"Más control en {creative_angle}.",
                "Tu operación, más rápida.",
                "Atiende mejor sin perder control.",
                "Pedidos claros desde la primera mesa.",
            ],
            "pt": [
                "Mais pedidos, menos espera.",
                "Menos caos no pico.",
                "QR, cozinha e salão sincronizados.",
                f"Mais controle em {creative_angle}.",
                "Sua operação, mais rápida.",
                "Atenda melhor sem perder o controle.",
                "Pedidos claros desde a primeira mesa.",
            ],
        }.get(
            language,
            [
                "More orders, less waiting.",
                "Less chaos at peak hours.",
                "QR, kitchen and staff synced.",
                f"More control at {creative_angle}.",
                "Your operation, faster.",
                "Serve better without losing control.",
                "Clear orders from the first table.",
            ],
        )
        body_options = {
            "es": [
                f"{brand} ayuda a {audience} a servir más rápido, reducir errores y tener control real de cada pedido.",
                f"Pedidos por QR, cocina sincronizada, tablets y administración completa en un solo sistema para {audience}.",
                f"Una forma más clara de gestionar {subject.lower()} cuando la prioridad es {creative_angle}.",
                f"Si el servicio se complica en hora pico, este flujo pone orden desde la mesa hasta la cocina.",
                f"Cuando {creative_angle}, el restaurante gana ritmo y el equipo gana control.",
                f"{f'Con {special_offer} en mente, esta pieza muestra un camino más simple para {audience}.' if special_offer else f'Una operación más clara ayuda a {audience} a vender mejor y atender con menos fricción.'}",
            ],
            "pt": [
                f"{brand} ajuda {audience} a atender mais rápido, reduzir erros e ter controle real de cada pedido.",
                f"Pedidos por QR, cozinha sincronizada, tablets e administração completa em um único sistema para {audience}.",
                f"Uma forma mais clara de gerenciar {subject.lower()} quando a prioridade é {creative_angle}.",
                f"Se o atendimento trava no pico, este fluxo organiza a operação da mesa à cozinha.",
                f"Quando {creative_angle}, o restaurante ganha ritmo e a equipe ganha controle.",
                f"{f'Com {special_offer} em mente, esta peça mostra um caminho mais simples para {audience}.' if special_offer else f'Uma operação mais clara ajuda {audience} a vender mais e atender com menos fricção.'}",
            ],
        }.get(
            language,
            [
                f"{brand} helps {audience} serve faster, reduce mistakes and keep real control over every order.",
                f"QR ordering, synced kitchen flow, tablets and full management in one system for {audience}.",
                f"A clearer way to manage {subject.lower()} when the priority is {creative_angle}.",
                f"If service gets messy at peak time, this flow brings order from table to kitchen.",
                f"When {creative_angle}, the restaurant gains rhythm and the team gains control.",
                f"{f'With {special_offer} in mind, this piece shows a simpler path for {audience}.' if special_offer else f'A clearer operation helps {audience} sell better and serve with less friction.'}",
            ],
        )
        cta_options = {
            "es": [
                "Solicita una demo y descubre cómo funciona.",
                "Pide una demo y comprueba el impacto.",
                "Habla con el equipo y mira el flujo completo.",
                "Reserva una demo y revisa la propuesta.",
            ],
            "pt": [
                "Peça uma demonstração e veja como funciona.",
                "Agende uma demo e confira o impacto.",
                "Fale com o time e veja o fluxo completo.",
                "Reserve uma demo e revise a proposta.",
            ],
        }.get(language, [
            "Book a demo and see how it works.",
            "Talk to the team and see the impact.",
            "See the full workflow in action.",
            "Reserve a demo and review the offer.",
        ])
        closing_options = {
            "es": [
                "Guárdalo para revisarlo con tu equipo.",
                "Compártelo con quien decide la operación.",
                "Si quieres menos fricción, este es el siguiente paso.",
                f"Si {special_offer.lower()} importa, esta es la pieza que faltaba." if special_offer else "Si quieres avanzar más rápido, esta es la pieza que faltaba.",
            ],
            "pt": [
                "Salve para revisar com o seu time.",
                "Compartilhe com quem decide a operação.",
                "Se você quer menos fricção, este é o próximo passo.",
                f"Se {special_offer.lower()} importa, esta é a peça que faltava." if special_offer else "Se você quer avançar mais rápido, esta é a peça que faltava.",
            ],
        }.get(language, [
            "Save it for your team.",
            "Share it with the person who decides operations.",
            "If you want less friction, this is the next step.",
            f"If {special_offer.lower()} matters, this is the missing piece." if special_offer else "If you want to move faster, this is the missing piece.",
        ])
        idx = _variation_index(fields, "caption", len(hook_options))
        parts = [
            hook_options[idx],
            body_options[_variation_index(fields, "body", len(body_options))],
            cta_options[_variation_index(fields, "cta", len(cta_options))],
            closing_options[_variation_index(fields, "closing", len(closing_options))],
        ]
        return "\n\n".join(part for part in parts if part)
    tone_text = tone if not _is_generic_text(tone) else "clear"
    creative_angle = _resolve_creative_angle(fields)
    opener_options = {
        "es": [
            f"¿Quieres mejorar {subject.lower()} con una experiencia más clara?",
            f"Una forma más clara de presentar {subject.lower()}.",
            f"Convierte {subject.lower()} en un mensaje más fácil de entender.",
            f"Haz que {subject.lower()} se entienda en segundos.",
        ],
        "pt": [
            f"Quer melhorar {subject.lower()} com uma experiência mais clara?",
            f"Uma forma mais clara de apresentar {subject.lower()}.",
            f"Transforme {subject.lower()} em uma mensagem mais fácil de entender.",
            f"Faça {subject.lower()} ser entendido em segundos.",
        ],
    }.get(language, [
        f"Want to improve {subject.lower()} with a clearer experience?",
        f"A cleaner way to present {subject.lower()}.",
        f"Turn {subject.lower()} into a message that's easier to understand.",
        f"Make {subject.lower()} clear in seconds.",
    ])
    body_options = {
        "es": [
            f"{brand} ayuda a {audience} a lograr mejores resultados con una propuesta {tone_text}, más directa y alineada con el objetivo de {objective}.",
            f"Este post está pensado para comunicar valor real, reducir fricción y empujar a la acción con foco en {creative_angle}.",
            f"Un mensaje útil, simple y fácil de guardar, ideal para mostrar lo que hace {brand} de forma clara.",
        ],
        "pt": [
            f"{brand} ajuda {audience} a alcançar melhores resultados com uma proposta {tone_text}, mais direta e alinhada ao objetivo de {objective}.",
            f"Este post foi pensado para comunicar valor real, reduzir fricção e levar à ação com foco em {creative_angle}.",
            f"Uma mensagem útil, simples e fácil de salvar, ideal para mostrar o que {brand} faz de forma clara.",
        ],
    }.get(language, [
        f"{brand} helps {audience} get better results with a {tone_text} offer, a more direct message and a focus aligned with the goal to {objective}.",
        f"This post is designed to communicate real value, reduce friction and drive action with a focus on {creative_angle}.",
        f"A useful, simple and easy-to-save message that shows what {brand} does in a clear way.",
    ])
    cta_options = {
        "es": [
            "Pide una demo y descubre cómo funciona.",
            "Reserva una demo y mira el flujo completo.",
            f"Habla con el equipo y descubre cómo encaja en {creative_angle}.",
        ],
        "pt": [
            "Peça uma demonstração e veja como funciona.",
            "Agende uma demo e veja o fluxo completo.",
            f"Fale com o time e descubra como encaixa em {creative_angle}.",
        ],
    }.get(language, ["Book a demo and see how it works.", "Schedule a demo and see the full flow.", f"Talk to the team and learn how it fits {creative_angle}."])
    closing_options = {
        "es": [
            "Guárdalo para revisarlo luego.",
            "Compártelo con tu equipo antes de decidir.",
            "Si esto te ayudó, es hora de probarlo.",
            f"Si {special_offer.lower()} importa, este es el siguiente paso." if special_offer else "Si quieres avanzar, este es el siguiente paso.",
        ],
        "pt": [
            "Salve para revisar depois.",
            "Compartilhe com seu time antes de decidir.",
            "Se isso ajudou, está na hora de testar.",
            f"Se {special_offer.lower()} importa, este é o próximo passo." if special_offer else "Se você quer avançar, este é o próximo passo.",
        ],
    }.get(language, ["Save it for later.", "Share it with your team before you decide.", "If this helped, it's time to try it.", f"If {special_offer.lower()} matters, it's time to try it." if special_offer else "If you want to move forward, it's time to try it."])
    idx = _variation_index(fields, "caption", len(opener_options))
    parts = [
        opener_options[idx],
        body_options[_variation_index(fields, "body", len(body_options))],
        cta_options[_variation_index(fields, "cta", len(cta_options))],
        closing_options[_variation_index(fields, "closing", len(closing_options))],
    ]
    return "\n\n".join(part for part in parts if part)


def _realistic_palette(fields: dict[str, str], seed: str) -> dict[str, tuple[int, int, int]]:
    base = _palette(seed)
    website_colors = [item.strip() for item in (fields.get("website colors") or "").split(",") if item.strip()]
    primary = _parse_color(fields.get("primary color") or (website_colors[0] if website_colors else ""), (248, 190, 39))
    secondary = _parse_color(fields.get("secondary color") or (website_colors[1] if len(website_colors) > 1 else ""), (255, 119, 34))
    return {
        "background": (6, 6, 7),
        "surface": (14, 15, 19),
        "panel": (20, 21, 27),
        "paper": (246, 246, 245),
        "text": (255, 255, 255),
        "muted": (212, 216, 224),
        "primary": primary or base["primary"],
        "accent": secondary or base["accent"],
        "success": (57, 181, 88),
    }


def _hero_headline(fields: dict[str, str]) -> list[str]:
    language = (fields.get("language") or "en").lower()
    niche = (fields.get("niche") or "").lower()
    audience = (fields.get("audience") or "").lower()
    if _has_restaurant_context(fields):
        return {
            "es": ["Más pedidos.", "Menos caos.", "Más control."],
            "pt": ["Mais pedidos.", "Menos caos.", "Mais controle."],
        }.get(language, ["More orders.", "Less chaos.", "More control."])
    if any(keyword in niche or keyword in audience for keyword in ["agency", "agencia"]):
        return {
            "es": ["Más clientes.", "Menos fricción.", "Más resultados."],
            "pt": ["Mais clientes.", "Menos fricção.", "Mais resultados."],
        }.get(language, ["More clients.", "Less friction.", "More results."])
    return {
        "es": ["Más impacto.", "Menos esfuerzo.", "Más ventas."],
        "pt": ["Mais impacto.", "Menos esforço.", "Mais vendas."],
    }.get(language, ["More impact.", "Less effort.", "More conversions."])


def _hero_subtitle(fields: dict[str, str]) -> str:
    language = (fields.get("language") or "en").lower()
    niche = fields.get("niche", "your niche")
    audience = fields.get("audience", "your audience")
    if _has_restaurant_context(fields):
        if language == "es":
            return f"Pedidos por QR, cocina sincronizada y control total para {audience}."
        if language == "pt":
            return f"Pedidos por QR, cozinha sincronizada e controle total para {audience}."
        return f"QR orders, synced kitchen flow and full control for {audience}."
    if language == "es":
        return f"El sistema completo para {niche}, diseñado para {audience}."
    if language == "pt":
        return f"O sistema completo para {niche}, pensado para {audience}."
    return f"The complete system for {niche}, designed for {audience}."


def _image_copy(language: str) -> dict[str, str]:
    lang = language if language in {"es", "pt"} else "en"
    return {
        "growth_title": {
            "es": "Crecimiento en movimiento",
            "pt": "Crescimento em movimento",
            "en": "Growth in motion",
        }[lang],
        "brand_chip": {
            "es": "Marca",
            "pt": "Marca",
            "en": "Brand",
        }[lang],
        "offer_chip": {
            "es": "Oferta",
            "pt": "Oferta",
            "en": "Offer",
        }[lang],
        "audience_chip": {
            "es": "Audiencia",
            "pt": "Público",
            "en": "Audience",
        }[lang],
        "cta_chip": "CTA",
        "focus": {
            "es": "Enfoque",
            "pt": "Foco",
            "en": "Focus",
        }[lang],
        "audience_label": {
            "es": "Audiencia",
            "pt": "Público",
            "en": "Audience",
        }[lang],
        "objective_label": {
            "es": "Objetivo",
            "pt": "Objetivo",
            "en": "Objective",
        }[lang],
        "tone_label": {
            "es": "Tono",
            "pt": "Tom",
            "en": "Tone",
        }[lang],
        "reach": {
            "es": "Alcance",
            "pt": "Alcance",
            "en": "Reach",
        }[lang],
        "clicks": {
            "es": "Clics",
            "pt": "Cliques",
            "en": "Clicks",
        }[lang],
        "leads": {
            "es": "Leads",
            "pt": "Leads",
            "en": "Leads",
        }[lang],
        "sales": {
            "es": "Ventas",
            "pt": "Vendas",
            "en": "Sales",
        }[lang],
        "hook": {
            "es": "Gancho",
            "pt": "Gancho",
            "en": "Hook",
        }[lang],
        "offer": {
            "es": "Oferta",
            "pt": "Oferta",
            "en": "Offer",
        }[lang],
        "cta": {
            "es": "CTA",
            "pt": "CTA",
            "en": "CTA",
        }[lang],
        "big_promise": {
            "es": "Gran promesa",
            "pt": "Grande promessa",
            "en": "Big promise",
        }[lang],
        "short_proof": {
            "es": "Prueba breve",
            "pt": "Prova breve",
            "en": "Short proof",
        }[lang],
        "clear_value": {
            "es": "Valor claro",
            "pt": "Valor claro",
            "en": "Clear value",
        }[lang],
        "trust_signal": {
            "es": "Señal de confianza",
            "pt": "Sinal de confiança",
            "en": "Trust signal",
        }[lang],
        "book_demo": {
            "es": "Reserva una demo",
            "pt": "Agende uma demo",
            "en": "Book demo",
        }[lang],
        "start_free": {
            "es": "Empieza gratis",
            "pt": "Comece grátis",
            "en": "Start free",
        }[lang],
        "campaign_snapshot": {
            "es": "Resumen de campaña",
            "pt": "Resumo da campanha",
            "en": "Campaign snapshot",
        }[lang],
        "visual_system": {
            "es": "Sistema visual",
            "pt": "Sistema visual",
            "en": "Visual system",
        }[lang],
        "seed_label": {
            "es": "Semilla",
            "pt": "Semente",
            "en": "Seed",
        }[lang],
        "demo_image": {
            "es": "IMAGEN DEMO",
            "pt": "IMAGEM DEMO",
            "en": "DEMO IMAGE",
        }[lang],
        "orders_realtime": {
            "es": "Pedidos en tiempo real",
            "pt": "Pedidos em tempo real",
            "en": "Orders in real time",
        }[lang],
        "pending": {
            "es": "Pendientes",
            "pt": "Pendentes",
            "en": "Pending",
        }[lang],
        "preparing": {
            "es": "En preparación",
            "pt": "Em preparação",
            "en": "Preparing",
        }[lang],
        "ready": {
            "es": "Listos",
            "pt": "Prontos",
            "en": "Ready",
        }[lang],
        "orders": {
            "es": "pedidos",
            "pt": "pedidos",
            "en": "orders",
        }[lang],
        "response_avg": {
            "es": "respuesta prom.",
            "pt": "resposta méd.",
            "en": "avg reply",
        }[lang],
        "sync": {
            "es": "sincronización",
            "pt": "sincronia",
            "en": "sync",
        }[lang],
        "satisfaction": {
            "es": "satisfacción",
            "pt": "satisfação",
            "en": "satisfaction",
        }[lang],
        "mobile_order": {
            "es": "PEDIR\nDESDE EL MÓVIL",
            "pt": "PEDIR\nPELO CELULAR",
            "en": "ORDER\nFROM MOBILE",
        }[lang],
        "total_control": {
            "es": "CONTROL TOTAL",
            "pt": "CONTROLE TOTAL",
            "en": "TOTAL CONTROL",
        }[lang],
        "sync_subtitle": {
            "es": "Pedidos, cocina y clientes sincronizados en tiempo real.",
            "pt": "Pedidos, cozinha e clientes sincronizados em tempo real.",
            "en": "Orders, kitchen and customers synced in real time.",
        }[lang],
        "no_lock_in": {
            "es": "Sin permanencia",
            "pt": "Sem permanência",
            "en": "No lock-in",
        }[lang],
        "no_card": {
            "es": "Sin tarjeta",
            "pt": "Sem cartão",
            "en": "No card",
        }[lang],
        "quick_setup": {
            "es": "Configuración rápida",
            "pt": "Configuração rápida",
            "en": "Quick setup",
        }[lang],
        "support": {
            "es": "Soporte",
            "pt": "Suporte",
            "en": "Support",
        }[lang],
    }


def _hero_bullets(fields: dict[str, str]) -> list[str]:
    language = (fields.get("language") or "en").lower()
    source = " ".join(
        [
            fields.get("product/service", ""),
            fields.get("brand template", ""),
            fields.get("campaign theme", ""),
            fields.get("special offer", ""),
            fields.get("brand description", ""),
            fields.get("brand products/services", ""),
            fields.get("website description", ""),
            fields.get("website excerpt", ""),
        ]
    ).lower()
    if _has_restaurant_context(fields) or any(keyword in source for keyword in ["pedido", "restaurant", "restaurante", "menu", "qr", "cozinha", "tablets"]):
        return {
            "es": [
                "Pedidos por QR en la mesa",
                "Cocina y camareros sincronizados",
                "Administración completa del negocio",
                "TV de estado en tiempo real",
            ],
            "pt": [
                "Pedidos por QR na mesa",
                "Cozinha e atendentes sincronizados",
                "Administração completa da operação",
                "Tela de status em tempo real",
            ],
        }.get(language, [
            "QR orders at the table",
            "Kitchen and staff synced in real time",
            "Full business control panel",
            "Live status display for operations",
        ])
    return {
        "es": [
            f"Enfocado en {fields.get('objective', 'conversion')}",
            f"Estilo {fields.get('tone', 'friendly')}",
            f"Pensado para {fields.get('audience', 'your audience')}",
            f"Alineado con {fields.get('topic', 'your topic')}",
        ],
        "pt": [
            f"Focado em {fields.get('objective', 'conversão')}",
            f"Tom {fields.get('tone', 'friendly')}",
            f"Pensado para {fields.get('audience', 'seu público')}",
            f"Alinhado com {fields.get('topic', 'seu tema')}",
        ],
    }.get(language, [
        f"Focused on {fields.get('objective', 'conversion')}",
        f"Tone: {fields.get('tone', 'friendly')}",
        f"Built for {fields.get('audience', 'your audience')}",
        f"Aligned with {fields.get('topic', 'your topic')}",
    ])


def _draw_metric_cards(draw: ImageDraw.ImageDraw, x: int, y: int, palette: dict[str, tuple[int, int, int]], font):
    metrics = [("14m", "avg reply"), ("302", "orders"), ("+100%", "growth"), ("0.3s", "sync")]
    for index, (value, label) in enumerate(metrics):
        col = index % 2
        row = index // 2
        box_x = x + col * 210
        box_y = y + row * 92
        draw.rounded_rectangle((box_x, box_y, box_x + 190, box_y + 76), radius=18, fill=(255, 255, 255))
        draw.text((box_x + 16, box_y + 12), value, fill=palette["surface"], font=font)
        draw.text((box_x + 16, box_y + 40), label, fill=palette["muted"], font=font)


def _gradient_background(image: Image.Image, start: tuple[int, int, int], end: tuple[int, int, int]) -> None:
    width, height = image.size
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(int(start[index] * (1 - ratio) + end[index] * ratio) for index in range(3))
        draw.line((0, y, width, y), fill=color)


def _rounded_panel(draw: ImageDraw.ImageDraw, bounds: tuple[int, int, int, int], fill, outline=None, radius=36, width=2):
    draw.rounded_rectangle(bounds, radius=radius, fill=fill, outline=outline, width=width)


def _load_font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_lines(text: str, width: int, limit: int | None = None) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    lines = textwrap.wrap(cleaned, width=width, break_long_words=False, break_on_hyphens=False)
    if limit is not None:
        lines = lines[:limit]
    return lines


def _draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    *,
    fill: tuple[int, int, int],
    font: ImageFont.ImageFont,
    max_lines: int = 2,
    line_gap: int = 5,
) -> None:
    x1, y1, x2, _ = box
    font_size = getattr(font, "size", 18)
    max_width = max(int((x2 - x1) / max(font_size * 0.55, 1)), 12)
    y = y1
    for line in _wrap_lines(text, max_width, max_lines):
        draw.text((x1, y), line, fill=fill, font=font)
        y += font_size + line_gap


def _mix_color(a: tuple[int, int, int], b: tuple[int, int, int], ratio: float) -> tuple[int, int, int]:
    ratio = max(0.0, min(1.0, ratio))
    return tuple(int(a[index] * (1 - ratio) + b[index] * ratio) for index in range(3))


def _draw_badge(draw: ImageDraw.ImageDraw, position: tuple[int, int], text: str, fill, text_fill, font):
    x, y = position
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    padding_x = 20
    padding_y = 12
    rect = (x, y, x + (right - left) + padding_x * 2, y + (bottom - top) + padding_y * 2)
    draw.rounded_rectangle(rect, radius=24, fill=fill)
    draw.text((x + padding_x, y + padding_y - 2), text, fill=text_fill, font=font)
    return rect


def _compose_story(
    image: Image.Image,
    prompt: str,
    output_format: str,
    seed: str,
    profile: dict[str, object],
) -> None:
    draw = ImageDraw.Draw(image)
    width, height = image.size
    palette = profile["palette"]  # type: ignore[assignment]
    style_label = profile["label"]  # type: ignore[assignment]
    mode = profile["mode"]  # type: ignore[assignment]
    title_font = _load_font(76, bold=True)
    body_font = _load_font(40)
    small_font = _load_font(30)
    micro_font = _load_font(24)
    fields = _prompt_fields(prompt)
    brand_name = fields.get("brand", "POSTALIA") or "POSTALIA"
    topic = _resolve_subject(fields)
    audience = fields.get("audience", "Audience not provided") or "Audience not provided"
    objective = fields.get("objective", "Objective not provided") or "Objective not provided"
    tone = fields.get("tone", style_label) or style_label
    language = (fields.get("language") or "en").lower()
    copy = _image_copy(language)

    # Background layers
    _gradient_background(image, palette["surface"], palette["primary"])
    draw.ellipse((-220, -120, 480, 580), fill=(*palette["accent"],))
    draw.ellipse((width - 360, 90, width + 240, 690), fill=(255, 255, 255, 22))
    draw.rounded_rectangle((70, 110, width - 70, height - 110), radius=48, fill=palette["paper"])
    if mode in {"glow", "neon"}:
        draw.rounded_rectangle((90, 130, width - 90, height - 130), radius=42, outline=palette["accent"], width=3)

    # Header
    draw.text((120, 170), brand_name.upper()[:28], fill=palette["primary"], font=micro_font)
    _draw_badge(draw, (120, 220), style_label.upper(), palette["primary"], (255, 255, 255), micro_font)
    _draw_badge(draw, (320, 220), output_format.replace("_", " ").upper(), palette["accent"], (255, 255, 255), micro_font)

    # Main title
    wrapped_title = _wrap_lines(topic, 18, 3) or _wrap_lines(prompt, 18, 3)
    current_y = 360
    for line in wrapped_title:
        draw.text((120, current_y), line, fill=palette["surface"], font=title_font)
        current_y += 92

    # Content block
    hook = [
        f"{copy['audience_label']}: {audience}",
        f"{copy['objective_label']}: {objective}",
        f"{copy['tone_label']}: {tone}",
    ]
    current_y += 18
    draw.text((120, current_y), copy["campaign_snapshot"], fill=palette["muted"], font=micro_font)
    current_y += 44
    for line in hook:
        draw.text((120, current_y), line, fill=(42, 48, 64), font=body_font)
        current_y += 56

    # Side card
    panel_x1 = width - 390
    panel_y1 = 230
    panel_x2 = width - 120
    panel_y2 = 820
    _rounded_panel(draw, (panel_x1, panel_y1, panel_x2, panel_y2), fill=(255, 255, 255), outline=(228, 232, 240), radius=36)
    draw.text((panel_x1 + 28, panel_y1 + 32), copy["visual_system"], fill=palette["primary"], font=micro_font)
    swatches = [
        (palette["primary"], copy["brand_chip"]),
        (palette["accent"], copy["offer_chip"]),
        ((34, 197, 94), copy["cta_chip"]),
        ((245, 158, 11), copy["focus"]),
    ]
    for index, (color, label) in enumerate(swatches):
        y = panel_y1 + 100 + index * 92
        draw.rounded_rectangle((panel_x1 + 28, y, panel_x1 + 102, y + 54), radius=16, fill=color)
        draw.text((panel_x1 + 122, y + 7), label, fill=palette["surface"], font=small_font)
        draw.text((panel_x1 + 122, y + 34), f"{copy['seed_label']} {seed[index * 2:index * 2 + 4]}", fill=palette["muted"], font=micro_font)
    draw.text((panel_x1 + 28, panel_y2 - 120), f"{copy['audience_label']}: {audience[:28]}", fill=palette["surface"], font=micro_font)
    draw.text((panel_x1 + 28, panel_y2 - 82), f"{copy['objective_label']}: {objective[:28]}", fill=palette["surface"], font=micro_font)

    # Footer
    draw.rounded_rectangle((120, height - 250, width - 120, height - 150), radius=30, fill=(25, 31, 45))
    draw.text((150, height - 226), style_label, fill=(255, 255, 255), font=small_font)
    draw.text((150, height - 188), copy["demo_image"], fill=(198, 204, 214), font=micro_font)
    _draw_badge(draw, (width - 335, height - 215), copy["demo_image"], palette["accent"], (255, 255, 255), micro_font)


def _compose_square(
    image: Image.Image,
    prompt: str,
    output_format: str,
    seed: str,
    profile: dict[str, object],
) -> None:
    draw = ImageDraw.Draw(image)
    width, height = image.size
    palette = profile["palette"]  # type: ignore[assignment]
    style_label = profile["label"]  # type: ignore[assignment]
    mode = profile["mode"]  # type: ignore[assignment]
    headline_font = _load_font(58, bold=True)
    body_font = _load_font(32)
    chip_font = _load_font(24)
    fields = _prompt_fields(prompt)
    brand_name = fields.get("brand", "POSTALIA") or "POSTALIA"
    topic = _resolve_subject(fields)
    audience = fields.get("audience", "Audience not provided") or "Audience not provided"
    objective = fields.get("objective", "Objective not provided") or "Objective not provided"
    tone = fields.get("tone", style_label) or style_label
    language = (fields.get("language") or "en").lower()
    copy = _image_copy(language)

    _gradient_background(image, palette["surface"], palette["primary"])
    draw.ellipse((-180, -120, 460, 520), fill=(*palette["accent"],))
    draw.rounded_rectangle((52, 52, width - 52, height - 52), radius=42, fill=(247, 248, 251))
    draw.rounded_rectangle((84, 84, width - 84, height - 84), radius=36, fill=(255, 255, 255), outline=(228, 232, 240), width=2)
    if mode in {"glow", "neon"}:
        draw.rounded_rectangle((84, 84, width - 84, height - 84), radius=36, outline=palette["accent"], width=3)
    elif mode in {"minimal", "clean"}:
        draw.rounded_rectangle((84, 84, width - 84, height - 84), radius=36, outline=palette["primary"], width=2)

    draw.text((120, 122), brand_name.upper()[:28], fill=palette["primary"], font=chip_font)
    _draw_badge(draw, (120, 170), style_label.upper(), palette["primary"], (255, 255, 255), chip_font)
    _draw_badge(draw, (300, 170), output_format.replace("_", " ").upper(), palette["accent"], (255, 255, 255), chip_font)

    title = _wrap_lines(topic, 24, 4) or _wrap_lines(prompt, 24, 4)
    current_y = 280
    for line in title:
        draw.text((120, current_y), line, fill=palette["surface"], font=headline_font)
        current_y += 68

    # Content cards
    left_x = 120
    top_y = 600
    card_w = 360
    card_h = 250
    for index in range(2):
        x = left_x + index * (card_w + 40)
        fill = palette["primary"] if index == 0 else palette["accent"]
        _rounded_panel(draw, (x, top_y, x + card_w, top_y + card_h), fill=fill, radius=28)
        draw.text((x + 26, top_y + 30), f"0{index + 1}", fill=(255, 255, 255), font=chip_font)
        draw.text((x + 26, top_y + 92), [copy["hook"], copy["cta"]][index], fill=(255, 255, 255), font=body_font)
        detail_text = [f"{copy['audience_label']}: {audience}", f"{copy['objective_label']}: {objective}", f"{copy['tone_label']}: {tone}"][index]
        draw.text((x + 26, top_y + 144), _wrap_lines(detail_text, 20, 2)[0], fill=(255, 255, 255), font=chip_font)
        extra_lines = _wrap_lines(detail_text, 20, 2)[1:]
        if extra_lines:
            draw.text((x + 26, top_y + 178), extra_lines[0], fill=(255, 255, 255), font=chip_font)

    draw.rounded_rectangle((120, height - 220, width - 120, height - 120), radius=30, fill=(24, 30, 44))
    draw.text((150, height - 188), f"{style_label} • {brand_name[:20]}", fill=(255, 255, 255), font=body_font)
    draw.text((150, height - 145), f"{copy['seed_label']} {seed}", fill=(196, 203, 214), font=chip_font)


def _compose_realistic_restaurant_hero(
    image: Image.Image,
    fields: dict[str, str],
    palette: dict[str, tuple[int, int, int]],
    seed: str,
) -> None:
    _compose_realistic_poster(image, fields, palette, seed)


def _compose_realistic_poster(
    image: Image.Image,
    fields: dict[str, str],
    palette: dict[str, tuple[int, int, int]],
    seed: str,
) -> None:
    draw = ImageDraw.Draw(image)
    width, height = image.size
    language = (fields.get("language") or "en").lower()
    copy = _image_copy(language)
    brand_name = (fields.get("brand") or "POSTALIA").strip() or "POSTALIA"
    brand_initial = (brand_name[:1] or "P").upper()
    headline = _hero_headline(fields)
    subtitle = _hero_subtitle(fields)
    bullets = _hero_bullets(fields)
    restaurant = _has_restaurant_context(fields)
    hero_font = _load_font(68, bold=True)
    subtitle_font = _load_font(22)
    body_font = _load_font(20)
    chip_font = _load_font(16)
    micro_font = _load_font(14)
    cta_text = {
        "es": "Solicita una demo",
        "pt": "Peça uma demonstração",
    }.get(language, "Book a demo")

    _gradient_background(image, palette["background"], palette["surface"])
    draw.ellipse((-170, 40, 380, 660), fill=palette["accent"])
    draw.ellipse((width - 320, 120, width + 110, 680), fill=palette["primary"])
    draw.rounded_rectangle((36, 36, width - 36, height - 36), radius=42, fill=(5, 6, 8))

    draw.rounded_rectangle((70, 72, 220, 142), radius=24, fill=palette["primary"])
    draw.text((98, 90), brand_initial, fill=(0, 0, 0), font=_load_font(42, bold=True))
    draw.text((246, 90), brand_name, fill=(255, 255, 255), font=_load_font(34, bold=True))

    draw.text((70, 184), headline[0], fill=(255, 255, 255), font=hero_font)
    draw.text((70, 292), headline[1], fill=palette["primary"], font=hero_font)
    draw.text((70, 400), headline[2], fill=(255, 255, 255), font=hero_font)
    _draw_wrapped_text(draw, subtitle, (74, 518, 360, 600), fill=(236, 239, 244), font=subtitle_font, max_lines=2)

    left_cards = bullets[:3]
    for index, bullet in enumerate(left_cards):
        card_y = 610 + index * 92
        draw.rounded_rectangle((72, card_y, 392, card_y + 74), radius=18, fill=(18, 20, 28), outline=palette["primary"], width=2)
        draw.ellipse((92, card_y + 20, 118, card_y + 46), fill=palette["primary"])
        draw.text((101, card_y + 19), "✓", fill=(0, 0, 0), font=chip_font)
        _draw_wrapped_text(draw, bullet, (132, card_y + 12, 370, card_y + 60), fill=(255, 255, 255), font=body_font, max_lines=2)

    draw.rounded_rectangle((72, height - 142, 420, height - 76), radius=26, fill=palette["primary"])
    draw.text((104, height - 124), cta_text, fill=(0, 0, 0), font=_load_font(26, bold=True))
    draw.text((426, height - 124), "→", fill=palette["primary"], font=_load_font(28, bold=True))

    board_x1, board_y1 = width - 520, 82
    board_x2, board_y2 = width - 78, height - 88
    draw.rounded_rectangle((board_x1, board_y1, board_x2, board_y2), radius=36, fill=palette["paper"], outline=(92, 92, 92), width=3)
    draw.rounded_rectangle((board_x1 + 12, board_y1 + 12, board_x2 - 12, board_y1 + 70), radius=20, fill=(30, 22, 26))
    draw.text((board_x1 + 26, board_y1 + 24), brand_name, fill=(255, 255, 255), font=chip_font)
    draw.text(
        (board_x2 - 196, board_y1 + 24),
        {
            "es": "LISTA PARA PUBLICAR",
            "pt": "PRONTA PARA PUBLICAR",
        }.get(language, "READY TO PUBLISH"),
        fill=(220, 220, 220),
        font=chip_font,
    )
    draw.text((board_x1 + 28, board_y1 + 92), copy["campaign_snapshot"], fill=(24, 24, 24), font=_load_font(28, bold=True))
    draw.text((board_x1 + 28, board_y1 + 130), copy["sync_subtitle"], fill=(86, 92, 102), font=micro_font)

    if restaurant:
        cards = [
            ("QR", "Menos espera" if language == "es" else "Menos espera" if language == "pt" else "Less waiting", palette["primary"]),
            ("Cocina", "Flujo en tiempo real" if language == "es" else "Fluxo em tempo real" if language == "pt" else "Real-time flow", palette["accent"]),
            ("Control", "Operación clara" if language == "es" else "Operação clara" if language == "pt" else "Clear control", _mix_color(palette["primary"], (255, 255, 255), 0.18)),
        ]
    else:
        generic_detail_texts = {
            "es": ["Sistema visual claro", "Oferta más directa", "Respuesta inmediata"],
            "pt": ["Sistema visual claro", "Oferta mais direta", "Resposta imediata"],
            "en": ["Clear visual system", "Sharper offer", "Immediate response"],
        }.get(language, ["Clear visual system", "Sharper offer", "Immediate response"])
        cards = [
            (copy["brand_chip"], generic_detail_texts[0], palette["primary"]),
            (copy["offer_chip"], generic_detail_texts[1], palette["accent"]),
            (copy["cta_chip"], generic_detail_texts[2], _mix_color(palette["primary"], (255, 255, 255), 0.18)),
        ]
    for index, (title, detail, fill_color) in enumerate(cards):
        card_x = board_x1 + 24 + index * 140
        card_y = board_y1 + 178
        draw.rounded_rectangle((card_x, card_y, card_x + 124, card_y + 108), radius=20, fill=fill_color)
        draw.text((card_x + 14, card_y + 16), title, fill=(18, 18, 18), font=_load_font(20, bold=True))
        _draw_wrapped_text(draw, detail, (card_x + 14, card_y + 48, card_x + 108, card_y + 96), fill=(52, 52, 56), font=micro_font, max_lines=2)

    lane_y1 = board_y1 + 314
    lane_y2 = board_y2 - 28
    draw.rounded_rectangle((board_x1 + 20, lane_y1, board_x2 - 20, lane_y2), radius=24, fill=(18, 18, 20), outline=(76, 76, 80))
    lane_title = {
        "es": "Flujo visual",
        "pt": "Fluxo visual",
    }.get(language, "Visual flow")
    draw.text((board_x1 + 38, lane_y1 + 18), lane_title, fill=(255, 255, 255), font=chip_font)
    flow_labels = [
        ("1", {"es": "Gancho", "pt": "Gancho", "en": "Hook"}.get(language, "Hook") if not restaurant else {"es": "Pedido", "pt": "Pedido", "en": "Order"}.get(language, "Order")),
        ("2", {"es": "Prueba", "pt": "Prova", "en": "Proof"}.get(language, "Proof") if not restaurant else {"es": "Cocina", "pt": "Cozinha", "en": "Kitchen"}.get(language, "Kitchen")),
        ("3", {"es": "CTA", "pt": "CTA", "en": "CTA"}.get(language, "CTA") if not restaurant else {"es": "Salón", "pt": "Salão", "en": "Dining"}.get(language, "Dining")),
    ]
    for index, (num, label) in enumerate(flow_labels):
        cell_x1 = board_x1 + 38 + index * 128
        cell_y1 = lane_y1 + 64
        draw.rounded_rectangle((cell_x1, cell_y1, cell_x1 + 102, cell_y1 + 98), radius=18, fill=(32, 26, 30))
        draw.rounded_rectangle((cell_x1 + 14, cell_y1 + 14, cell_x1 + 42, cell_y1 + 42), radius=10, fill=palette["primary"])
        draw.text((cell_x1 + 22, cell_y1 + 17), num, fill=(0, 0, 0), font=_load_font(18, bold=True))
        draw.text((cell_x1 + 16, cell_y1 + 56), label, fill=(255, 255, 255), font=chip_font)
        draw.text((cell_x1 + 16, cell_y1 + 78), copy["focus"], fill=(198, 202, 210), font=_load_font(11))

    footer_items = {
        "es": ["Sin permanencia", "Sin tarjeta", "Configuración rápida", "Soporte"],
        "pt": ["Sem permanência", "Sem cartão", "Configuração rápida", "Suporte"],
    }.get(language, ["No lock-in", "No card", "Quick setup", "Support"])
    for index, item in enumerate(footer_items):
        x = 78 + index * 184
        draw.text((x, height - 52), item, fill=(245, 245, 245), font=_load_font(12, bold=True))


def _compose_realistic_hero(
    image: Image.Image,
    prompt: str,
    output_format: str,
    seed: str,
) -> None:
    fields = _prompt_fields(prompt)
    palette = _realistic_palette(fields, seed)
    _compose_realistic_poster(image, fields, palette, seed)


def _compose_image(
    image: Image.Image,
    prompt: str,
    output_format: str,
    seed: str,
    style: str,
) -> None:
    style_key = (style or "realistic").strip().lower()
    profile = _style_profile(style, seed)
    if style_key == "realistic":
        if output_format in {"story", "reel_cover"}:
            _compose_story(image, prompt, output_format, seed, profile)
        else:
            _compose_realistic_hero(image, prompt, output_format, seed)
        return
    if output_format in {"story", "reel_cover"}:
        _compose_story(image, prompt, output_format, seed, profile)
        return
    if output_format in {"feed_square", "carousel"}:
        _compose_square(image, prompt, output_format, seed, profile)
        return
    _compose_square(image, prompt, output_format, seed, profile)


def _demo_mode() -> str:
    return os.getenv("DEMO_AI_MODE", "fake").strip().lower()


def _demo_text_model_id() -> str:
    return os.getenv("DEMO_AI_TEXT_MODEL", "").strip()


def _demo_image_model_id() -> str:
    return os.getenv("DEMO_AI_IMAGE_MODEL", "").strip()


def _demo_device() -> str:
    return os.getenv("DEMO_AI_DEVICE", "cpu").strip().lower()


def _demo_image_steps() -> int:
    try:
        return max(1, int(os.getenv("DEMO_AI_IMAGE_STEPS", "8")))
    except ValueError:
        return 8


def _demo_image_guidance_scale() -> float:
    try:
        return float(os.getenv("DEMO_AI_IMAGE_GUIDANCE_SCALE", "6.5"))
    except ValueError:
        return 6.5


@lru_cache(maxsize=1)
def _load_text_model():
    if _demo_mode() != "real":
        return None
    model_id = _demo_text_model_id()
    if not model_id:
        raise RuntimeError("DEMO_AI_MODE=real requires DEMO_AI_TEXT_MODEL.")
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception as exc:  # pragma: no cover - import failure is environment specific
        raise RuntimeError("Text model dependencies are unavailable.") from exc
    device = _demo_device()
    if device == "cuda" and not torch.cuda.is_available():
        device = "cpu"
    if device == "mps" and not (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()):
        device = "cpu"
    dtype = torch.float16 if device in {"cuda", "mps"} else torch.float32
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    if tokenizer.pad_token is None and tokenizer.eos_token is not None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True, torch_dtype=dtype)
    model = model.to(device)
    model.eval()
    return tokenizer, model, torch


def _build_text_prompt(prompt: str, generation_type: str, title: str = "", cta: str = "") -> str:
    system_prompt = (
        "You are Postalia, a senior Instagram creative strategist. "
        "Write original, non-repetitive content in the requested language. "
        "Never mention that you are an AI. Never echo the prompt verbatim."
    )
    if generation_type == "full_post":
        return (
            f"{system_prompt}\n"
            "Return valid JSON with keys: title, short_hook, caption, hashtags, carousel_slides, "
            "image_prompt, call_to_action, recommended_design_notes.\n"
            "Caption must read like a natural Instagram caption with a strong hook, line breaks, a persuasive body "
            "and a clear CTA. The image_prompt must describe a premium social publication with brand colors, "
            "clear hierarchy, niche-aligned visuals and a layout ready to publish on Instagram.\n"
            f"Requested title: {title or ''}\n"
            f"Requested CTA: {cta or ''}\n"
            f"Context:\n{prompt}\n"
        )
    if generation_type == "image_prompt":
        return (
            f"{system_prompt}\n"
            "Return a single image prompt for a premium Instagram visual. "
            "Keep it concise, specific and visually rich.\n"
            f"Context:\n{prompt}\n"
        )
    return (
        f"{system_prompt}\n"
        "Return only a natural Instagram caption with line breaks and a clear CTA.\n"
        f"Context:\n{prompt}\n"
    )


def _generate_text_with_model(prompt: str, generation_type: str, title: str = "", cta: str = "") -> str | None:
    loaded = _load_text_model()
    if not loaded:
        return None
    tokenizer, model, torch = loaded
    messages = [
        {"role": "system", "content": "You are Postalia, a senior Instagram creative strategist."},
        {"role": "user", "content": _build_text_prompt(prompt, generation_type, title=title, cta=cta)},
    ]
    if hasattr(tokenizer, "apply_chat_template"):
        input_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    else:
        input_text = "\n\n".join(item["content"] for item in messages) + "\n\nAssistant:"
    inputs = tokenizer(input_text, return_tensors="pt")
    inputs = {key: value.to(model.device) for key, value in inputs.items()}
    max_new_tokens = {
        "full_post": 320,
        "image_prompt": 96,
    }.get(generation_type, 220)
    with torch.no_grad():
        output_tokens = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.85,
            top_p=0.92,
            repetition_penalty=1.08,
            pad_token_id=tokenizer.eos_token_id,
        )
    decoded = tokenizer.decode(output_tokens[0], skip_special_tokens=True).strip()
    if decoded.startswith(input_text):
        decoded = decoded[len(input_text) :].strip()
    return decoded.strip()


def _normalize_text_list(value) -> list[str]:
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        items = [item.strip() for item in re.split(r"[\n,]", value) if item.strip()]
    else:
        items = []
    return [str(item).strip() for item in items if str(item).strip()]


def _maybe_parse_json(value: str) -> dict | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _build_text_model_response(prompt: str, generation_type: str, title: str = "", cta: str = "") -> tuple[str, dict] | None:
    raw_text = _generate_text_with_model(prompt, generation_type, title=title, cta=cta)
    if raw_text is None:
        return None
    if generation_type == "full_post":
        baseline = _package(prompt, title, cta)
        parsed = _maybe_parse_json(raw_text)
        payload = {**baseline, **parsed} if isinstance(parsed, dict) else {**baseline, "caption": raw_text, "content": raw_text}
        payload["title"] = str(payload.get("title") or title or baseline["title"])
        payload["short_hook"] = str(payload.get("short_hook") or baseline["short_hook"])
        payload["caption"] = str(payload.get("caption") or payload.get("content") or raw_text)
        payload["image_prompt"] = str(payload.get("image_prompt") or baseline["image_prompt"])
        payload["call_to_action"] = str(payload.get("call_to_action") or cta or baseline["call_to_action"])
        payload["recommended_design_notes"] = str(payload.get("recommended_design_notes") or baseline["recommended_design_notes"])
        payload["hashtags"] = _normalize_text_list(payload.get("hashtags")) or baseline["hashtags"]
        payload["carousel_slides"] = _normalize_text_list(payload.get("carousel_slides")) or baseline["carousel_slides"]
        return json.dumps(payload, ensure_ascii=False), payload
    if generation_type == "image_prompt":
        text = raw_text.strip() or f"Visual direction for {prompt[:120]}"
        return text, {"content": text, "image_prompt": text}
    fields = _prompt_fields(prompt)
    language = (fields.get("language") or "en").lower()
    text = raw_text.strip() or _caption_from_prompt(fields)
    return text, {
        "content": text,
        "caption": text,
        "hashtags": _build_hashtags(fields, language),
        "image_prompt": f"Visual direction for {prompt[:120]}",
    }


@lru_cache(maxsize=1)
def _load_image_model():
    if _demo_mode() != "real":
        return None
    model_id = _demo_image_model_id()
    if not model_id:
        raise RuntimeError("DEMO_AI_MODE=real requires DEMO_AI_IMAGE_MODEL.")
    try:
        import torch
        from diffusers import AutoPipelineForText2Image
    except Exception as exc:  # pragma: no cover - import failure is environment specific
        raise RuntimeError("Image model dependencies are unavailable.") from exc
    device = _demo_device()
    if device == "cuda" and not torch.cuda.is_available():
        device = "cpu"
    if device == "mps" and not (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()):
        device = "cpu"
    dtype = torch.float16 if device in {"cuda", "mps"} else torch.float32
    pipe = AutoPipelineForText2Image.from_pretrained(model_id, torch_dtype=dtype)
    pipe = pipe.to(device)
    return pipe, torch


def _build_image_prompt(prompt: str, output_format: str, style: str) -> str:
    fields = _prompt_fields(prompt)
    brand = (fields.get("brand") or "Postalia").strip() or "Postalia"
    niche = (fields.get("niche") or "brand").strip()
    audience = (fields.get("audience") or "your audience").strip()
    subject = _resolve_subject(fields)
    tone = (fields.get("tone") or "friendly").strip()
    creative_angle = _resolve_creative_angle(fields)
    language = (fields.get("language") or "en").strip()
    website_hint = fields.get("website description") or fields.get("website excerpt") or fields.get("brand template") or ""
    restaurant_context = _has_restaurant_context(fields)
    visual_direction = (
        "This is a software UI advertisement, not food photography. "
        "If the context mentions restaurants, show restaurant operations software: QR ordering screens, waiter tablets, "
        "kitchen display software, admin dashboards, and mobile app UI. "
        "Do not show plated dishes, bowls, cutlery, ingredients, chefs, recipes, menus as cuisine, or table meal styling."
        if restaurant_context
        else "This is a software UI advertisement, not food photography. Show product UI, dashboards, phone screens, and a clean CTA. "
        "Do not show plated dishes, bowls, cutlery, ingredients, chefs, recipes, or restaurant meal styling."
    )
    return (
        f"Premium Instagram creative for {brand}. "
        f"Audience: {audience}. Niche: {niche}. Subject: {subject}. Tone: {tone}. "
        f"Creative angle: {creative_angle}. Language: {language}. Output format: {output_format}. Style: {style}. "
        f"Use one dominant hero message, strong hierarchy, clean typography, brand colors and realistic marketing context. "
        f"{visual_direction} "
        "Avoid dashboards, sidebars, dense charts, footer ribbons, tiny labels and generic templates. "
        f"Website context: {website_hint}. "
        f"Prompt context: {prompt}"
    )


def _render_model_image(prompt: str, output_format: str, style: str) -> Image.Image | None:
    loaded = _load_image_model()
    if not loaded:
        return None
    pipe, torch = loaded
    device = _demo_device()
    model_id = _demo_image_model_id().lower()
    turbo_mode = "turbo" in model_id or "lcm" in model_id
    seed = int(_seed(f"{prompt}|{output_format}|{style}"), 16) % (2**32)
    generator = torch.Generator(device=device if device in {"cuda", "mps"} else "cpu").manual_seed(seed)
    width, height = _format_size(output_format)
    pipe_kwargs = {
        "prompt": _build_image_prompt(prompt, output_format, style),
        "width": width,
        "height": height,
        "num_inference_steps": 1 if turbo_mode else _demo_image_steps(),
        "guidance_scale": 0.0 if turbo_mode else _demo_image_guidance_scale(),
        "generator": generator,
    }
    if not turbo_mode:
        pipe_kwargs["negative_prompt"] = "text, watermark, logo, blurry, low quality, dashboard, sidebar, chart, clutter"
    result = pipe(**pipe_kwargs)
    return result.images[0]


def _render_structured_fallback_image(prompt: str, output_format: str, style: str) -> Image.Image:
    fields = _prompt_fields(prompt)
    seed = _seed(f"{prompt}|{output_format}|{style}")
    size = _format_size(output_format)
    image = Image.new("RGB", size, color=(12, 14, 20))
    palette = _realistic_palette(fields, seed)
    _compose_realistic_poster(image, fields, palette, seed)
    return image


@app.post("/text")
def text(payload: TextRequest):
    if _demo_mode() == "real":
        try:
            model_response = _build_text_model_response(payload.prompt, payload.generation_type, title=payload.title or "", cta=payload.cta or "")
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        if model_response is None:
            raise HTTPException(status_code=503, detail="DEMO_AI_MODE=real requires a loadable text model.")
        text_value, package = model_response
        return {"text": text_value, "payload": package}
    _thinking_delay(payload.prompt, payload.generation_type, "realistic")
    if payload.generation_type == "full_post":
        package = _package(payload.prompt, payload.title or "", payload.cta or "")
        text_value = json.dumps(package, ensure_ascii=False)
        return {"text": text_value, "payload": package}
    if payload.generation_type == "image_prompt":
        seed = _seed(payload.prompt)
        return {
            "text": f"Visual direction for {payload.prompt[:120]} ({seed})",
            "payload": {
                "content": f"Visual direction for {payload.prompt[:120]}",
                "image_prompt": f"Visual direction for {payload.prompt[:120]}",
            },
        }
    fields = _prompt_fields(payload.prompt)
    content = _caption_from_prompt(fields)
    return {
        "text": content,
        "payload": {
            "content": content,
            "caption": content,
            "hashtags": _build_hashtags(fields, (fields.get("language") or "en").lower()),
            "image_prompt": f"Visual direction for {payload.prompt[:120]}",
        },
    }


@app.post("/image")
def image(payload: ImageRequest):
    if _demo_mode() == "real":
        try:
            model_image = _render_model_image(payload.prompt, payload.output_format, payload.style)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception:
            logger.exception("Real image generation failed, using structured fallback.")
            model_image = _render_structured_fallback_image(payload.prompt, payload.output_format, payload.style)
        if model_image is None:
            model_image = _render_structured_fallback_image(payload.prompt, payload.output_format, payload.style)
        seed = _seed(payload.prompt + payload.output_format + payload.style)
        filename = f"{seed}-{uuid.uuid4().hex[:12]}-{payload.output_format}.png"
        path = BASE_DIR / filename
        model_image.save(path, format="PNG")
        return {"image_url": f"http://localhost:8001/files/{filename}", "output_format": payload.output_format}
    _thinking_delay(payload.prompt, "image", payload.style)
    width, height = _format_size(payload.output_format)
    seed = _seed(payload.prompt + payload.output_format)
    image = Image.new("RGB", (width, height), color=(18, 24, 38))
    _compose_image(image, payload.prompt, payload.output_format, seed, payload.style)
    filename = f"{seed}-{uuid.uuid4().hex[:12]}-{payload.output_format}.png"
    path = BASE_DIR / filename
    image.save(path, format="PNG")
    return {"image_url": f"http://localhost:8001/files/{filename}", "output_format": payload.output_format}
