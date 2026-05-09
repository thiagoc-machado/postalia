from __future__ import annotations

import hashlib
import json
import logging
import re
import time
import uuid
import unicodedata
from dataclasses import dataclass
from io import BytesIO

import httpx
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont

from apps.common.storage import save_generated_file

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AIResponse:
    text: str
    payload: dict
    provider: str
    model: str
    image_url: str | None = None


def validate_ai_configuration(settings_obj) -> None:
    if settings_obj.AI_PROVIDER_MODE not in {"fake", "real"}:
        raise ValueError("AI_PROVIDER_MODE must be either 'fake' or 'real'.")
    if not settings_obj.DEBUG and settings_obj.AI_PROVIDER_MODE == "fake" and not settings_obj.ENABLE_FAKE_AI_IN_PRODUCTION:
        raise ValueError("AI_PROVIDER_MODE=fake requires ENABLE_FAKE_AI_IN_PRODUCTION=true in production.")
    if settings_obj.AI_PROVIDER_MODE == "real":
        if not settings_obj.AI_TEXT_PROVIDER:
            raise ValueError("Real text AI requires AI_TEXT_PROVIDER.")
        if settings_obj.AI_TEXT_PROVIDER == "local":
            if settings_obj.DEMO_AI_MODE != "real":
                raise ValueError("Local text AI requires DEMO_AI_MODE=real.")
            if not settings_obj.DEMO_AI_BASE_URL or not settings_obj.DEMO_AI_TEXT_MODEL:
                raise ValueError("Local text AI requires DEMO_AI_BASE_URL and DEMO_AI_TEXT_MODEL.")
        elif not settings_obj.AI_TEXT_API_KEY or not settings_obj.AI_TEXT_MODEL:
            raise ValueError("Real text AI requires AI_TEXT_API_KEY and AI_TEXT_MODEL.")
        if settings_obj.AI_IMAGE_PROVIDER:
            if settings_obj.AI_IMAGE_PROVIDER == "local":
                if settings_obj.DEMO_AI_MODE != "real":
                    raise ValueError("Local image AI requires DEMO_AI_MODE=real.")
                if not settings_obj.DEMO_AI_BASE_URL or not settings_obj.DEMO_AI_IMAGE_MODEL:
                    raise ValueError("Local image AI requires DEMO_AI_BASE_URL and DEMO_AI_IMAGE_MODEL.")
            elif not settings_obj.AI_IMAGE_API_KEY or not settings_obj.AI_IMAGE_MODEL:
                raise ValueError("Real image AI requires AI_IMAGE_API_KEY and AI_IMAGE_MODEL when AI_IMAGE_PROVIDER is set.")


def _is_local_ai_provider(provider: str) -> bool:
    return provider in {"local", "demo", "demo-ai"}


def _demo_ai_endpoint(path: str) -> str:
    return f"{settings.DEMO_AI_BASE_URL.rstrip('/')}/{path.lstrip('/')}"


def _deterministic_seed(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


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
    combined = re.sub(
        r"\s+",
        " ",
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
        ),
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
            "salon",
            "salao",
            "sala",
            "camareros",
            "garcon",
            "operacao",
            "operacion",
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
    return int(_deterministic_seed(basis), 16) % max(size, 1)


def _build_hashtags(fields: dict[str, str], language: str) -> list[str]:
    tags: list[str] = ["#postalia"]
    brand = (fields.get("brand") or "").strip()
    subject = _resolve_subject(fields)
    audience = (fields.get("audience") or "").strip()
    niche = (fields.get("niche") or "").strip()
    instagram_handle = (fields.get("instagram handle") or "").strip().lstrip("@")

    for value in [brand, instagram_handle, subject, audience, niche]:
        tag = f"#{_slugify_hashtag(value)}" if value else ""
        if tag and tag not in tags:
            if len(tag) > 20 and value not in {brand, instagram_handle}:
                continue
            tags.append(tag)

    if _has_restaurant_context(fields):
        restaurant_tags = {
            "es": ["#restaurantes", "#pedidosonline", "#qrcode", "#automatizacion", "#pedidosporqrcode", "#automacionderestaurantes"],
            "pt": ["#restaurantes", "#pedidosonline", "#qrcode", "#automacao", "#pedidosporqrcode", "#automacaodepedidos"],
            "en": ["#restaurants", "#onlineorders", "#qrcode", "#automation", "#restaurantautomation", "#ordersoftware"],
        }.get(language, [])
        for tag in restaurant_tags:
            if tag not in tags:
                tags.append(tag)
    else:
        generic_tags = {
            "es": ["#marketingdigital", "#negocios", "#crecimiento"],
            "pt": ["#marketingdigital", "#negociosdigitais", "#crescimento"],
            "en": ["#marketing", "#businessgrowth", "#contentstrategy"],
        }.get(language, [])
        for tag in generic_tags:
            if tag not in tags:
                tags.append(tag)

    if _has_restaurant_context(fields):
        curated = {
            "es": ["#automacionderestaurantes", "#pedidosporqrcode"],
            "pt": ["#automacaodepedidos", "#pedidosporqrcode"],
            "en": ["#restaurantautomation", "#ordersoftware"],
        }.get(language, [])
        for tag in curated:
            if tag not in tags:
                tags.append(tag)

    return tags[:8]


def _caption_for_context(fields: dict[str, str]) -> str:
    language = (fields.get("language") or "en").lower()
    brand = (fields.get("brand") or "your brand").strip() or "your brand"
    audience = (fields.get("audience") or "your audience").strip()
    objective = (fields.get("objective") or "connect").strip()
    tone = _tone_phrase(fields)
    subject = _resolve_subject(fields)
    creative_angle = _resolve_creative_angle(fields)
    special_offer = (fields.get("special offer") or "").strip()
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
        }.get(language, [f"{brand} helps {audience} serve faster, reduce mistakes and keep real control over every order.", f"QR ordering, synced kitchen flow, tablets and full management in one system for {audience}.", f"A clearer way to manage {subject.lower()} when the priority is {creative_angle}.", f"If service gets messy at peak time, this flow brings order from table to kitchen.", f"When {creative_angle}, the restaurant gains rhythm and the team gains control.", f"{f'With {special_offer} in mind, this piece shows a simpler path for {audience}.' if special_offer else f'A clearer operation helps {audience} sell better and serve with less friction.'}"])
        cta_options = {
            "es": ["Solicita una demo y descubre cómo funciona.", "Pide una demo y comprueba el impacto.", "Habla con el equipo y mira el flujo completo.", "Reserva una demo y revisa la propuesta."],
            "pt": ["Peça uma demonstração e veja como funciona.", "Agende uma demo e confira o impacto.", "Fale com o time e veja o fluxo completo.", "Reserve uma demo e revise a proposta."],
        }.get(language, ["Book a demo and see how it works.", "Talk to the team and see the impact.", "See the full workflow in action.", "Reserve a demo and review the offer."])
        closing_options = {
            "es": ["Guárdalo para revisarlo con tu equipo.", "Compártelo con quien decide la operación.", "Si quieres menos fricción, este es el siguiente paso.", f"Si {special_offer.lower()} importa, esta es la pieza que faltaba." if special_offer else "Si quieres avanzar más rápido, esta es la pieza que faltaba."],
            "pt": ["Salve para revisar com o seu time.", "Compartilhe com quem decide a operação.", "Se você quer menos fricção, este é o próximo passo.", f"Se {special_offer.lower()} importa, esta é a peça que faltava." if special_offer else "Se você quer avançar mais rápido, esta é a peça que faltava."],
        }.get(language, ["Save it for your team.", "Share it with the person who decides operations.", "If you want less friction, this is the next step.", f"If {special_offer.lower()} matters, this is the missing piece." if special_offer else "If you want to move faster, this is the missing piece."])
        idx = _variation_index(fields, "caption", len(hook_options))
        return "\n\n".join(
            part
            for part in [
                hook_options[idx],
                body_options[_variation_index(fields, "body", len(body_options))],
                cta_options[_variation_index(fields, "cta", len(cta_options))],
                closing_options[_variation_index(fields, "closing", len(closing_options))],
            ]
            if part.strip()
    )
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
    }.get(language, [f"Want to improve {subject.lower()} with a clearer experience?", f"A cleaner way to present {subject.lower()}.", f"Turn {subject.lower()} into a message that's easier to understand.", f"Make {subject.lower()} clear in seconds."])
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
    }.get(language, [f"{brand} helps {audience} get better results with a {tone_text} offer, a more direct message and a focus aligned with the goal to {objective}.", f"This post is designed to communicate real value, reduce friction and drive action with a focus on {creative_angle}.", f"A useful, simple and easy-to-save message that shows what {brand} does in a clear way."])
    cta_options = {
        "es": ["Pide una demo y descubre cómo funciona.", "Reserva una demo y mira el flujo completo.", f"Habla con el equipo y descubre cómo encaja en {creative_angle}."],
        "pt": ["Peça uma demonstração e veja como funciona.", "Agende uma demo e veja o fluxo completo.", f"Fale com o time e descubra como encaixa em {creative_angle}."],
    }.get(language, ["Book a demo and see how it works.", "Schedule a demo and see the full flow.", f"Talk to the team and learn how it fits {creative_angle}."])
    closing_options = {
        "es": ["Guárdalo para revisarlo luego.", "Compártelo con tu equipo antes de decidir.", "Si esto te ayudó, es hora de probarlo.", f"Si {special_offer.lower()} importa, este es el siguiente paso." if special_offer else "Si quieres avanzar, este es el siguiente paso."],
        "pt": ["Salve para revisar depois.", "Compartilhe com seu time antes de decidir.", "Se isso ajudou, está na hora de testar.", f"Se {special_offer.lower()} importa, este é o próximo passo." if special_offer else "Se você quer avançar, este é o próximo passo."],
    }.get(language, ["Save it for later.", "Share it with your team before you decide.", "If this helped, it's time to try it.", f"If {special_offer.lower()} matters, it's time to try it." if special_offer else "If you want to move forward, it's time to try it."])
    idx = _variation_index(fields, "caption", len(opener_options))
    return "\n\n".join(
        part
        for part in [
            opener_options[idx],
            body_options[_variation_index(fields, "body", len(body_options))],
            cta_options[_variation_index(fields, "cta", len(cta_options))],
            closing_options[_variation_index(fields, "closing", len(closing_options))],
        ]
        if part.strip()
    )


def _fallback_caption_from_prompt(prompt: str) -> str:
    fields = _parse_prompt_fields(prompt)
    return _caption_for_context(fields)


def _fake_text_payload(prompt: str) -> str:
    fields = _parse_prompt_fields(prompt)
    return _caption_for_context(fields)


def _fake_package(prompt: str, title: str, cta: str) -> dict:
    seed = _deterministic_seed(prompt)
    fields = _parse_prompt_fields(prompt)
    language = fields.get("language", "en").lower()
    brand = fields.get("brand", "Postalia").strip() or "Postalia"
    niche = fields.get("niche", "brand").strip()
    audience = fields.get("audience", "your audience").strip()
    subject = _resolve_subject(fields)
    objective = fields.get("objective", "sell").strip()
    tone = _tone_phrase(fields)
    creative_angle = _resolve_creative_angle(fields)
    instagram_handle = (fields.get("instagram handle") or "").strip().lstrip("@")
    cta_text = cta or {
        "es": "Solicita una demo",
        "pt": "Peça uma demonstração",
    }.get(language, "Book a demo")
    caption = _caption_for_context(fields)
    has_restaurant = _has_restaurant_context(fields)
    image_prompt = (
        f"Premium Instagram publication for {brand} in the {niche} niche. "
        f"Create a real social ad with a strong hero headline, brand colors, "
        f"clear product or dashboard mockup, support copy for {audience}, "
        f"and a CTA that emphasizes {objective}. "
        f"Style should feel {tone}, polished and ready to publish. "
        f"Subject focus: {subject}. "
        f"{'Use QR ordering, kitchen sync and restaurant dashboard visuals.' if has_restaurant else 'Use the strongest product or service cues from the brand context.'}"
        f"{f' Include the Instagram handle {instagram_handle} if it is visible in the brand context.' if instagram_handle else ''}"
    )
    return {
        "title": title or f"Postalia Idea {seed}",
        "short_hook": _resolve_short_hook(fields),
        "caption": caption,
        "hashtags": _build_hashtags(fields, language),
        "carousel_slides": [
            "Slide 1: Strong hook" if not has_restaurant else "Slide 1: Menos filas",
            "Slide 2: Main problem" if not has_restaurant else "Slide 2: Menos erros",
            "Slide 3: Clear solution" if not has_restaurant else "Slide 3: QR, tablets and kitchen sync",
            "Slide 4: Visual proof" if not has_restaurant else "Slide 4: Real-time control",
            f"Slide 5: {cta_text}",
        ],
        "image_prompt": image_prompt,
        "call_to_action": cta_text,
        "recommended_design_notes": (
            f"Use {brand} colors when available. Keep the layout premium, high-contrast and aligned with {niche}. "
            "Include a clear headline, supporting UI or product mockup, and a strong CTA. "
            "If the brand serves restaurants, emphasize QR ordering, tablets, kitchen flow and operational control."
        ),
    }


def _fallback_canvas_size(output_format: str) -> tuple[int, int]:
    mapping = {
        "feed_portrait": (1080, 1350),
        "story": (1080, 1920),
        "reel_cover": (1080, 1920),
        "carousel": (1080, 1080),
        "feed_square": (1080, 1080),
    }
    return mapping.get(output_format, (1080, 1080))


def _fallback_title_lines(fields: dict[str, str], language: str) -> list[str]:
    if _has_restaurant_context(fields):
        return {
            "es": ["Más pedidos.", "Menos caos.", "Más control."],
            "pt": ["Mais pedidos.", "Menos caos.", "Mais controle."],
        }.get(language, ["More orders.", "Less chaos.", "More control."])
    subject = _resolve_subject(fields)
    brand = (fields.get("brand") or "").strip() or "your brand"
    return {
        "es": [f"{brand}.", f"Mejora {subject[:24].strip() or 'tu oferta'}.", "Convierte más."],
        "pt": [f"{brand}.", f"Melhore {subject[:24].strip() or 'sua oferta'}.", "Converta mais."],
    }.get(language, [f"{brand}.", f"Improve {subject[:24].strip() or 'your offer'}.", "Convert more."])


def _fallback_bullets(fields: dict[str, str], language: str) -> list[str]:
    if _has_restaurant_context(fields):
        return {
            "es": ["Pedidos QR", "Cocina sincronizada", "Control en tiempo real"],
            "pt": ["Pedidos QR", "Cozinha sincronizada", "Controle em tempo real"],
        }.get(language, ["QR orders", "Kitchen sync", "Real-time control"])
    subject = _resolve_subject(fields)
    return {
        "es": [f"Oferta clara para {subject[:18]}", "Mensaje más directo", "CTA fácil de actuar"],
        "pt": [f"Oferta clara para {subject[:18]}", "Mensagem mais direta", "CTA fácil de agir"],
    }.get(language, [f"Clear offer for {subject[:18]}", "Sharper message", "Easy-to-act CTA"])


def _hex_to_rgb(value: str, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    raw = re.sub(r"[^0-9a-fA-F]", "", value or "")
    if len(raw) == 6:
        try:
            return tuple(int(raw[index : index + 2], 16) for index in (0, 2, 4))
        except ValueError:
            return fallback
    return fallback


def _mix_color(a: tuple[int, int, int], b: tuple[int, int, int], ratio: float) -> tuple[int, int, int]:
    ratio = max(0.0, min(1.0, ratio))
    return tuple(int(a[index] * (1 - ratio) + b[index] * ratio) for index in range(3))


def _load_fallback_font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/usr/local/lib/python3.13/site-packages/rest_framework/static/rest_framework/fonts/fontawesome-webfont.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    *,
    fill: tuple[int, int, int],
    font: ImageFont.ImageFont,
    line_spacing: int = 6,
    max_lines: int | None = None,
) -> int:
    x1, y1, x2, y2 = box
    max_width = max(x2 - x1, 1)
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        test = " ".join(current + [word])
        if draw.textlength(test, font=font) <= max_width:
            current.append(word)
            continue
        if current:
            lines.append(" ".join(current))
        current = [word]
    if current:
        lines.append(" ".join(current))
    if max_lines is not None:
        lines = lines[:max_lines]
    y = y1
    for line in lines:
        draw.text((x1, y), line, fill=fill, font=font)
        y += font.size + line_spacing if hasattr(font, "size") else 18 + line_spacing
        if y > y2:
            break
    return y


def _render_structured_fallback_image(fields: dict[str, str], output_format: str, style: str, prompt: str) -> ContentFile:
    size = _fallback_canvas_size(output_format)
    scale = 2
    base_size = (size[0] // scale, size[1] // scale)
    image = Image.new("RGB", base_size, color=(10, 12, 16))
    draw = ImageDraw.Draw(image)
    primary = _hex_to_rgb(fields.get("primary color", ""), (58, 38, 41))
    secondary = _hex_to_rgb(fields.get("secondary color", ""), (197, 138, 42))
    background = _mix_color(primary, (8, 10, 18), 0.7)
    surface = _mix_color(primary, (22, 24, 34), 0.42)
    paper = (244, 240, 232)
    accent = secondary
    strong = (255, 255, 255)
    muted = (214, 219, 228)
    draw.rectangle((0, 0, *base_size), fill=background)
    for index in range(base_size[1]):
        ratio = index / max(base_size[1] - 1, 1)
        color = tuple(int(background[channel] * (1 - ratio) + surface[channel] * ratio) for channel in range(3))
        draw.line((0, index, base_size[0], index), fill=color)
    draw.ellipse((-120, 10, 260, 360), fill=accent)
    draw.ellipse((base_size[0] - 220, 60, base_size[0] + 120, 360), fill=_mix_color(accent, (255, 255, 255), 0.18))
    draw.rounded_rectangle((20, 20, base_size[0] - 20, base_size[1] - 20), radius=26, fill=_mix_color((0, 0, 0), background, 0.26))

    brand = (fields.get("brand") or "POSTALIA").strip() or "POSTALIA"
    language = (fields.get("language") or "en").lower()
    brand_font = _load_fallback_font(18, bold=True)
    title_font = _load_fallback_font(36, bold=True)
    body_font = _load_fallback_font(18)
    small_font = _load_fallback_font(13)

    draw.rounded_rectangle((32, 34, 118, 116), radius=18, fill=accent)
    draw.text((47, 63), (brand[:1] or "P").upper(), fill=(0, 0, 0), font=_load_fallback_font(42, bold=True))
    draw.text((136, 52), brand.upper(), fill=strong, font=brand_font)
    draw.text((136, 74), fields.get("brand voice", "Premium social creative"), fill=muted, font=small_font)

    headline_lines = _fallback_title_lines(fields, language)
    headline_y = 160
    for index, line in enumerate(headline_lines):
        color = accent if index == 1 else strong
        draw.text((32, headline_y + index * 56), line, fill=color, font=title_font)

    subject = _resolve_subject(fields)
    subtitle = {
        "es": f"Solución para {subject[:54]}",
        "pt": f"Solução para {subject[:54]}",
    }.get(language, f"Solution for {subject[:54]}")
    draw.text((32, 352), subtitle, fill=muted, font=body_font)

    bullets = _fallback_bullets(fields, language)
    for index, bullet in enumerate(bullets):
        y = 418 + index * 38
        draw.ellipse((34, y + 5, 46, y + 17), fill=accent)
        draw.text((58, y), bullet, fill=strong, font=body_font)

    cta_text = {
        "es": "Solicita una demo",
        "pt": "Peça uma demonstração",
    }.get(language, "Book a demo")
    draw.rounded_rectangle((32, base_size[1] - 120, 308, base_size[1] - 54), radius=18, fill=accent)
    draw.text((56, base_size[1] - 101), cta_text, fill=(0, 0, 0), font=_load_fallback_font(17, bold=True))

    panel_x1 = base_size[0] - 258
    panel_y1 = 42
    panel_x2 = base_size[0] - 36
    panel_y2 = base_size[1] - 42
    draw.rounded_rectangle((panel_x1, panel_y1, panel_x2, panel_y2), radius=20, fill=paper, outline=(120, 120, 120), width=2)
    draw.rounded_rectangle((panel_x1 + 10, panel_y1 + 10, panel_x2 - 10, panel_y1 + 54), radius=14, fill=(31, 22, 26))
    draw.text((panel_x1 + 22, panel_y1 + 22), brand, fill=strong, font=small_font)
    draw.text((panel_x2 - 88, panel_y1 + 22), "EXPORT", fill=(220, 220, 220), font=small_font)
    draw.text((panel_x1 + 18, panel_y1 + 72), {
        "es": "Financiero",
        "pt": "Painel",
    }.get(language, "Dashboard"), fill=(20, 20, 22), font=body_font)
    stats = [
        ("302", "orders", accent),
        ("0.3s", "sync", _mix_color(accent, (255, 255, 255), 0.18)),
        ("98%", "control", _mix_color(accent, (255, 255, 255), 0.3)),
    ]
    stat_y = panel_y1 + 120
    for index, (value, label, fill) in enumerate(stats):
        x = panel_x1 + 16 + index * 65
        draw.rounded_rectangle((x, stat_y, x + 56, stat_y + 44), radius=10, fill=fill)
        draw.text((x + 6, stat_y + 8), value, fill=(18, 18, 18), font=small_font)
        draw.text((x + 6, stat_y + 24), label, fill=(66, 66, 72), font=_load_fallback_font(10))

    chart_x1, chart_y1 = panel_x1 + 18, panel_y1 + 186
    chart_x2, chart_y2 = panel_x2 - 18, panel_y2 - 26
    draw.rounded_rectangle((chart_x1, chart_y1, chart_x2, chart_y2), radius=16, fill=(250, 250, 250), outline=(222, 227, 232), width=2)
    for grid_x in range(chart_x1 + 10, chart_x2 - 10, 18):
        draw.line((grid_x, chart_y1 + 10, grid_x, chart_y2 - 10), fill=(234, 236, 241), width=1)
    for grid_y in range(chart_y1 + 10, chart_y2 - 10, 18):
        draw.line((chart_x1 + 10, grid_y, chart_x2 - 10, grid_y), fill=(234, 236, 241), width=1)
    points = []
    step = (chart_x2 - chart_x1 - 24) / 9
    for index in range(10):
        x = chart_x1 + 12 + int(step * index)
        y = chart_y2 - 36 - int(((index * 17 + len(subject)) % 7) * 18)
        points.append((x, y))
    draw.line(points, fill=accent, width=3)
    for point in points:
        draw.ellipse((point[0] - 3, point[1] - 3, point[0] + 3, point[1] + 3), fill=_mix_color(accent, (255, 100, 40), 0.2))

    footer_y = base_size[1] - 36
    draw.rounded_rectangle((32, footer_y - 22, base_size[0] - 32, footer_y + 14), radius=14, fill=(14, 14, 14))
    footer_items = {
        "es": ["Sin permanencia", "Sin tarjeta", "Configuración rápida", "Soporte"],
        "pt": ["Sem permanência", "Sem cartão", "Configuração rápida", "Suporte"],
    }.get(language, ["No lock-in", "No card", "Quick setup", "Support"])
    spacing = max((base_size[0] - 80) // max(len(footer_items), 1), 1)
    for index, item in enumerate(footer_items):
        draw.text((42 + index * spacing, footer_y - 12), item, fill=strong, font=_load_fallback_font(11))

    final_image = image.resize(size, Image.Resampling.LANCZOS)
    buffer = BytesIO()
    final_image.save(buffer, format="PNG")
    return ContentFile(
        buffer.getvalue(),
        name=f"fallback-{_deterministic_seed(prompt + output_format + style)}-{uuid.uuid4().hex[:12]}-{output_format}.png",
    )


def generate_fake_text(prompt: str, generation_type: str, title: str = "", cta: str = "") -> AIResponse:
    try:
        response = httpx.post(
            f"{settings.DEMO_AI_BASE_URL}/text",
            json={"prompt": prompt, "generation_type": generation_type, "title": title, "cta": cta},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        return AIResponse(
            text=data["text"],
            payload=data["payload"],
            provider="fake",
            model="demo-local",
        )
    except Exception:
        pass
    payload = _fake_package(prompt, title, cta) if generation_type == "full_post" else {
        "content": _fallback_caption_from_prompt(prompt),
        "image_prompt": f"Visual direction for {prompt[:120]}",
    }
    if generation_type == "image_prompt":
        text = payload["image_prompt"]
    elif generation_type in {"carousel", "full_post"}:
        text = json.dumps(payload, ensure_ascii=False)
    else:
        text = payload["content"]
    return AIResponse(
        text=text,
        payload=payload,
        provider="fake",
        model="demo-local",
    )


def generate_fake_image(prompt: str, output_format: str, style: str = "realistic") -> AIResponse:
    fields = _parse_prompt_fields(prompt)
    caption = _fallback_caption_from_prompt(prompt)
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = httpx.post(
                f"{settings.DEMO_AI_BASE_URL}/image",
                json={"prompt": prompt, "output_format": output_format, "style": style},
                timeout=90,
            )
            response.raise_for_status()
            data = response.json()
            image_source_url = str(data["image_url"]).replace("http://localhost:8001", settings.DEMO_AI_BASE_URL.rstrip("/"))
            image_response = httpx.get(image_source_url, timeout=60)
            image_response.raise_for_status()
            stored = save_generated_file(
                ContentFile(
                    image_response.content,
                    name=f"{_deterministic_seed(prompt + output_format)}-{uuid.uuid4().hex[:12]}-{output_format}.png",
                ),
                "generated",
            )
            return AIResponse(
                text=caption,
                payload={
                    **data,
                    "image_url": stored,
                    "source_prompt": prompt,
                    "source_image_url": image_source_url,
                    "style": style,
                    "caption": caption,
                    "hashtags": _fake_package(prompt, "", "")["hashtags"],
                },
                provider="fake",
                model="demo-local-image",
                image_url=stored,
            )
        except Exception as exc:
            last_error = exc
            logger.warning("Fake image generation attempt %s failed: %s", attempt + 1, exc.__class__.__name__)
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
            continue
    fallback_file = _render_structured_fallback_image(fields, output_format, style, prompt)
    url = save_generated_file(fallback_file, "generated")
    payload = {
        "image_url": url,
        "output_format": output_format,
        "source_prompt": prompt,
        "style": style,
        "caption": caption,
        "hashtags": _fake_package(prompt, "", "")["hashtags"],
        "fallback_reason": last_error.__class__.__name__ if last_error else "unknown",
    }
    return AIResponse(
        text=caption,
        payload=payload,
        provider="fake",
        model="demo-local-image",
        image_url=url,
    )


def _real_text_endpoint(provider: str) -> str:
    mapping = {
        "groq": "https://api.groq.com/openai/v1/chat/completions",
        "together": "https://api.together.xyz/v1/chat/completions",
        "mistral": "https://api.mistral.ai/v1/chat/completions",
        "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    }
    if provider not in mapping:
        raise ValueError(f"Unsupported AI text provider: {provider}")
    return mapping[provider]


def generate_real_text(prompt: str, generation_type: str, title: str = "", cta: str = "") -> AIResponse:
    if not settings.AI_TEXT_PROVIDER:
        raise ValueError("Real text provider is not configured.")
    if _is_local_ai_provider(settings.AI_TEXT_PROVIDER):
        if not settings.DEMO_AI_BASE_URL or not settings.DEMO_AI_TEXT_MODEL:
            raise ValueError("Local text provider is not configured.")
        endpoint = _demo_ai_endpoint("text")
        headers = {}
        payload = {
            "prompt": prompt,
            "generation_type": generation_type,
            "title": title or "",
            "cta": cta or "",
        }
    else:
        if not settings.AI_TEXT_API_KEY or not settings.AI_TEXT_MODEL:
            raise ValueError("Real text provider is not configured.")
        endpoint = _real_text_endpoint(settings.AI_TEXT_PROVIDER)
        headers = {"Authorization": f"Bearer {settings.AI_TEXT_API_KEY}"}
        system_prompt = (
            "You are Postalia, a senior Instagram creative strategist. Return polished, publication-ready content. "
            "Never echo the raw prompt, never mention that you are an AI, and never include debugging text."
        )
        user_prompt = prompt
        if generation_type == "full_post":
            user_prompt += (
                "\nReturn valid JSON with keys: title, short_hook, caption, hashtags, carousel_slides, "
                "image_prompt, call_to_action, recommended_design_notes.\n"
                "Caption must read like a natural Instagram caption with a strong hook, line breaks, a persuasive body "
                "and a clear CTA. The image_prompt must describe a premium social publication with brand colors, "
                "clear hierarchy, niche-aligned visuals and a layout ready to publish on Instagram. "
                "Choose a fresh creative angle that fits the brand context instead of repeating the same formula. "
                "Use the selected language only. Avoid tiny labels, dense admin-like dashboards, clutter and mixed languages. "
                "If the niche is restaurants, prefer a clean ad layout with one large hero message, one dashboard mockup, "
                "one mobile device and only a few supporting labels."
            )
        payload = {
            "model": settings.AI_TEXT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
        }
        if settings.AI_TEXT_PROVIDER == "openrouter":
            headers["HTTP-Referer"] = settings.APP_BASE_URL
            headers["X-Title"] = "Postalia"
    try:
        request_timeout = 300 if _is_local_ai_provider(settings.AI_TEXT_PROVIDER) else 60
        response = httpx.post(endpoint, json=payload, headers=headers, timeout=request_timeout)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception("Text AI provider error: %s", exc.__class__.__name__)
        raise ValueError("Text AI provider request failed.") from exc
    data = response.json()
    if _is_local_ai_provider(settings.AI_TEXT_PROVIDER):
        content = data.get("text") or data.get("payload", {}).get("caption") or data.get("payload", {}).get("content")
        if not content:
            raise ValueError("Local text AI provider returned no text.")
        parsed = data.get("payload") if isinstance(data.get("payload"), dict) else _maybe_parse_json(content)
        return AIResponse(
            text=content,
            payload=parsed or {"content": content},
            provider=settings.AI_TEXT_PROVIDER,
            model=settings.DEMO_AI_TEXT_MODEL,
        )
    content = data["choices"][0]["message"]["content"]
    parsed = _maybe_parse_json(content)
    return AIResponse(
        text=content,
        payload=parsed or {"content": content},
        provider=settings.AI_TEXT_PROVIDER,
        model=settings.AI_TEXT_MODEL,
    )


def generate_real_image(prompt: str, output_format: str, style: str = "realistic") -> AIResponse:
    if not settings.AI_IMAGE_PROVIDER:
        raise ValueError("Real image provider is not configured.")
    if _is_local_ai_provider(settings.AI_IMAGE_PROVIDER):
        if not settings.DEMO_AI_BASE_URL or not settings.DEMO_AI_IMAGE_MODEL:
            raise ValueError("Local image provider is not configured.")
        endpoint = _demo_ai_endpoint("image")
        headers = {}
    else:
        if not settings.AI_IMAGE_API_KEY or not settings.AI_IMAGE_MODEL:
            raise ValueError("Real image provider is not configured.")
        mapping = {
            "together": "https://api.together.xyz/v1/images/generations",
        }
        endpoint = mapping.get(settings.AI_IMAGE_PROVIDER)
        if not endpoint:
            raise ValueError(f"Unsupported AI image provider: {settings.AI_IMAGE_PROVIDER}")
        headers = {"Authorization": f"Bearer {settings.AI_IMAGE_API_KEY}"}
    payload = {
        "model": settings.DEMO_AI_IMAGE_MODEL if _is_local_ai_provider(settings.AI_IMAGE_PROVIDER) else settings.AI_IMAGE_MODEL,
        "prompt": (
            f"{prompt}\n"
            f"Format: {output_format}\n"
            f"Visual style: {style}\n"
            "Create a real Instagram publication or ad creative for software, not a mock template. "
            "Use brand colors, premium composition, strong hierarchy, realistic marketing context, "
            "and a layout that feels like a finished post ready to publish. "
            "This is a software UI advertisement, not food photography. "
            "If the context mentions restaurants, show restaurant operations software: QR ordering screens, waiter tablets, "
            "kitchen display software, admin dashboards, and mobile app UI. "
            "Do not show plated dishes, bowls, cutlery, ingredients, chefs, recipes, menus as cuisine, or table meal styling. "
            "Choose a fresh creative angle that matches the prompt instead of repeating a fixed template. "
            "Use the selected language only. Keep typography large and readable. Avoid tiny labels, dense dashboards, "
            "sidebar navigation, admin panels, charts, footer ribbons, mixed languages and visual clutter. "
            "Prefer a poster-like composition with one dominant hero area, one primary product or operation mockup, "
            "three concise supporting blocks and a clear CTA."
        ),
    }
    if _is_local_ai_provider(settings.AI_IMAGE_PROVIDER):
        payload["output_format"] = output_format
    else:
        payload["size"] = {
            "feed_square": "1024x1024",
            "feed_portrait": "1024x1536",
            "story": "1024x1792",
            "reel_cover": "1024x1792",
            "carousel": "1024x1024",
        }.get(output_format, "1024x1024")
    request_timeout = 900 if _is_local_ai_provider(settings.AI_IMAGE_PROVIDER) else 90
    try:
        response = httpx.post(endpoint, json=payload, headers=headers, timeout=request_timeout)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception("Image AI provider error: %s", exc.__class__.__name__)
        raise ValueError("Image AI provider request failed.") from exc
    data = response.json()
    image_url = data.get("image_url") or data.get("data", [{}])[0].get("url") or data.get("url")
    if not image_url:
        raise ValueError("Image AI provider returned no image URL.")
    if _is_local_ai_provider(settings.AI_IMAGE_PROVIDER):
        image_source_url = str(image_url).replace("http://localhost:8001", settings.DEMO_AI_BASE_URL.rstrip("/"))
        image_response = httpx.get(image_source_url, timeout=60)
        image_response.raise_for_status()
        stored = save_generated_file(
            ContentFile(
                image_response.content,
                name=f"{_deterministic_seed(prompt + output_format)}-{uuid.uuid4().hex[:12]}-{output_format}.png",
            ),
            "generated",
        )
        return AIResponse(
            text=f"Publication generated in {style.replace('_', ' ')} style for {output_format.replace('_', ' ')}.",
            payload={**data, "source_prompt": prompt, "output_format": output_format, "style": style, "source_image_url": image_source_url, "image_url": stored},
            provider=settings.AI_IMAGE_PROVIDER,
            model=settings.DEMO_AI_IMAGE_MODEL,
            image_url=stored,
        )
    return AIResponse(
        text=f"Publication generated in {style.replace('_', ' ')} style for {output_format.replace('_', ' ')}.",
        payload={**data, "source_prompt": prompt, "output_format": output_format, "style": style},
        provider=settings.AI_IMAGE_PROVIDER,
        model=settings.AI_IMAGE_MODEL,
        image_url=image_url,
    )


def _maybe_parse_json(content: str) -> dict | None:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        return parsed
    return None


def _parse_prompt_fields(prompt: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in prompt.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip().lower()] = value.strip()
    return fields
