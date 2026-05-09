from __future__ import annotations

import json
from dataclasses import dataclass
import re

from django.db import transaction
from django.utils import timezone

from apps.ai_providers.services import (
    AIResponse,
    _build_hashtags,
    _caption_for_context,
    _parse_prompt_fields,
    _variation_index,
    _resolve_short_hook,
    generate_fake_image,
    generate_fake_text,
    generate_real_image,
    generate_real_text,
)
from apps.brands.models import Brand, BrandTemplate
from apps.brands.services import can_use_brand_for_generation, format_website_context, refresh_brand_website_context
from apps.credits.models import CreditTransaction
from apps.credits.services import ensure_wallet, spend_points
from apps.common.moderation import moderate_text
from apps.subscriptions.services import count_generations_in_period, count_image_generations_in_period, get_user_subscription

from .models import GenerationRequest


@dataclass(frozen=True)
class GenerationOutcome:
    request: GenerationRequest
    payload: dict


def build_prompt(
    brand: Brand,
    template: BrandTemplate | None,
    generation_type: str,
    topic: str,
    product_service: str,
    objective: str,
    tone: str,
    language: str,
    campaign_theme: str = "",
    special_offer: str = "",
    output_format: str = "feed_square",
    style: str = "realistic",
) -> str:
    effective_tone = _resolve_effective_tone(brand, tone)
    template_prompt = template.base_prompt if template else ""
    template_visual_style = _normalize_visual_style(template.visual_style if template else "", brand)
    template_copywriting_style = template.copywriting_style if template else ""
    preferred_cta = template.preferred_cta if template else ""
    website_context = format_website_context(brand.website_context)
    website_context_block = f"Website context:\n{website_context}\n" if website_context else ""
    primary_color = brand.primary_color or "not set"
    secondary_color = brand.secondary_color or "not set"
    logo_status = "available" if brand.logo else "not set"
    content_focus = _resolve_content_focus(brand, template, topic, product_service, campaign_theme, special_offer)
    creative_angle = _resolve_creative_angle(
        brand,
        template,
        topic,
        product_service,
        campaign_theme,
        special_offer,
        objective,
        language,
    )
    visual_direction = _resolve_visual_direction(
        brand,
        template,
        topic,
        product_service,
        campaign_theme,
        special_offer,
        objective,
        language,
    )
    return (
        f"Brand: {brand.name}\n"
        f"Niche: {brand.niche}\n"
        f"Audience: {brand.target_audience}\n"
        f"Website: {brand.website or 'not set'}\n"
        f"Instagram handle: {brand.instagram_handle or 'not set'}\n"
        f"Brand description: {brand.description or 'not set'}\n"
        f"Brand products/services: {brand.products_services or 'not set'}\n"
        f"Brand voice: {brand.tone_of_voice or 'not set'}\n"
        f"Primary color: {primary_color}\n"
        f"Secondary color: {secondary_color}\n"
        f"Logo: {logo_status}\n"
        f"Tone: {effective_tone}\n"
        f"Requested tone: {tone}\n"
        f"Language: {language}\n"
        f"Objective: {objective}\n"
        f"Generation type: {generation_type}\n"
        f"Output format: {output_format}\n"
        f"Visual style: {style}\n"
        f"Creative angle: {creative_angle}\n"
        "Visual direction: create a real Instagram publication or ad creative, not a mock template. "
        "Respect the brand colors, niche and output format. Use strong visual hierarchy, natural typography, "
        "clear call to action and layout that looks ready to publish on Instagram. "
        "Do not generate a dashboard, sidebar admin panel, dense analytics chart or footer ribbon. "
        "Prefer a poster-like composition with one dominant hero area, a single product or operation mockup, "
        "three concise supporting blocks and only a few readable labels in the selected language.\n"
        f"Content focus: {content_focus}\n"
        f"Topic: {topic}\n"
        f"Product/Service: {product_service}\n"
        f"Campaign theme: {campaign_theme}\n"
        f"Special offer: {special_offer}\n"
        f"Brand template: {template_prompt}\n"
        f"Template visual style: {template_visual_style}\n"
        f"Template copywriting style: {template_copywriting_style}\n"
        f"Preferred CTA: {preferred_cta}\n"
        f"{visual_direction}\n"
        f"{website_context_block}"
        f"Forbidden topics: {template.forbidden_topics if template else ''}"
    )


def _normalize_visual_style(value: str, brand: Brand) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        return "Premium social media layout with clear hierarchy and brand colors"
    if re.fullmatch(r"#?[0-9a-fA-F]{3,8}", cleaned):
        palette = cleaned if cleaned.startswith("#") else f"#{cleaned}"
        return (
            f"Premium social media layout using {palette} as the accent color, "
            f"with a clean editorial composition and a strong product focus"
        )
    return cleaned


def _resolve_content_focus(
    brand: Brand,
    template: BrandTemplate | None,
    topic: str,
    product_service: str,
    campaign_theme: str,
    special_offer: str,
) -> str:
    candidates = [
        topic,
        product_service,
        brand.products_services,
        brand.description,
        campaign_theme,
        special_offer,
        template.base_prompt if template else "",
    ]
    for candidate in candidates:
        text = (candidate or "").strip()
        if text and not _looks_generic(text):
            return text
    if brand.products_services.strip():
        return brand.products_services.strip()
    if brand.description.strip():
        return brand.description.strip()
    return brand.niche


def _resolve_creative_angle(
    brand: Brand,
    template: BrandTemplate | None,
    topic: str,
    product_service: str,
    campaign_theme: str,
    special_offer: str,
    objective: str,
    language: str,
) -> str:
    fields = {
        "niche": brand.niche,
        "audience": brand.target_audience,
        "topic": topic,
        "product/service": product_service,
        "brand description": brand.description,
        "brand products/services": brand.products_services,
        "brand template": template.base_prompt if template else "",
        "campaign theme": campaign_theme,
        "special offer": special_offer,
        "objective": objective,
        "language": language,
    }
    subject = _resolve_content_focus(brand, template, topic, product_service, campaign_theme, special_offer)
    normalized_objective = (objective or "").strip().lower()
    if _looks_generic(subject):
        subject = brand.niche
    restaurant_context = re.sub(
        r"\s+",
        " ",
        " ".join([brand.niche, brand.target_audience, subject, campaign_theme]),
    ).lower()
    if "restaur" in restaurant_context:
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
        }.get(language, [
            "peak hours with more control",
            "QR orders without friction",
            "kitchen and floor in sync",
            "fewer mistakes on every shift",
            "clear operation at every table",
            "faster and more organized service",
        ])
        return options[_variation_index(fields, "creative angle", len(options))]
    if normalized_objective in {"announce promotion", "promote", "promotion"} and special_offer.strip():
        return special_offer.strip()
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
    }.get(language, [
        "a clearer offer",
        "a more direct message",
        "more confidence to decide",
        "a proposal that's easy to understand",
        "more value in fewer words",
        "a simpler flow",
    ])
    return options[_variation_index(fields, "creative angle", len(options))]


def _resolve_visual_direction(
    brand: Brand,
    template: BrandTemplate | None,
    topic: str,
    product_service: str,
    campaign_theme: str,
    special_offer: str,
    objective: str,
    language: str,
) -> str:
    subject = _resolve_content_focus(brand, template, topic, product_service, campaign_theme, special_offer)
    restaurant_context = re.sub(
        r"\s+",
        " ",
        " ".join([brand.niche, brand.target_audience, subject, campaign_theme, brand.description, brand.products_services]),
    ).lower()
    if "restaur" in restaurant_context:
        return (
            "Visual direction: create a premium Instagram ad for restaurant operations software, not food photography. "
            "Show a product UI, QR ordering screens, tablet interfaces for staff, a kitchen display screen, and an admin dashboard. "
            "Do not show plated dishes, bowls, cutlery, ingredients, chefs, menus as cuisine, or restaurant meal styling. "
            "Use brand colors, strong hierarchy, and a layout ready to publish."
        )
    return (
        "Visual direction: create a premium Instagram ad for SaaS or business software, not food photography. "
        "Show a product UI, dashboard screens, tablet or phone mockups, and a clear CTA. "
        "Avoid plated dishes, bowls, cutlery, ingredients, chefs, and restaurant meal styling."
    )


def _looks_generic(value: str) -> bool:
    normalized = value.strip().lower()
    generic = {
        "moderno",
        "modern",
        "teste",
        "test",
        "your offer",
        "your audience",
        "your topic",
        "your brand",
        "brand",
        "offer",
        "topic",
        "content",
        "post",
        "publication",
    }
    if normalized in generic:
        return True
    return normalized in {"", "-", "n/a", "none"}


def _resolve_effective_tone(brand: Brand, tone: str) -> str:
    requested = (tone or "").strip()
    brand_voice = (brand.tone_of_voice or "").strip()
    if brand_voice and (not requested or _looks_generic(requested) or requested.lower() in {"friendly", "clear", "professional"}):
        return brand_voice
    return requested or brand_voice or "friendly"


FREE_IMAGE_POINTS_COST = 30
FULL_POST_POINTS_SURCHARGE = 15
FREE_TEXT_OVERAGE_POINTS_COST = 5


def determine_cost(user, generation_type: str) -> tuple[int, str]:
    subscription = get_user_subscription(user)
    plan = subscription.plan
    if generation_type == GenerationRequest.GenerationType.FULL_POST:
        text_used = count_generations_in_period(user, generation_type)
        image_used = count_image_generations_in_period(user)
        if plan.code == "free":
            if image_used >= 1:
                raise ValueError("Free plan allows only 1 image generation per day.")
            cost = FREE_IMAGE_POINTS_COST + FULL_POST_POINTS_SURCHARGE
            if text_used >= plan.text_limit:
                cost += FREE_TEXT_OVERAGE_POINTS_COST
                return cost, "Free full post exceeds the text quota and includes image generation."
            return cost, "Free full post includes text and image generation."
        if text_used >= plan.text_limit:
            raise ValueError("Monthly text generation limit reached.")
        if image_used >= plan.image_limit:
            raise ValueError("Monthly image generation limit reached.")
        return 0, "Included in plan."
    if generation_type in {
        GenerationRequest.GenerationType.TEXT,
        GenerationRequest.GenerationType.CAROUSEL,
        GenerationRequest.GenerationType.IMAGE_PROMPT,
    }:
        used = count_generations_in_period(user, generation_type)
        if used >= plan.text_limit:
            if plan.code == "free":
                return 5, "Free quota exceeded, generation costs 5 points."
            raise ValueError("Monthly text generation limit reached.")
        return 0, "Included in plan."
    if generation_type == GenerationRequest.GenerationType.IMAGE:
        if plan.code == "free":
            from apps.generations.models import GenerationRequest as RequestModel

            used = RequestModel.objects.filter(
                user=user,
                generation_type__in=[
                    RequestModel.GenerationType.IMAGE,
                    RequestModel.GenerationType.FULL_POST,
                ],
                created_at__date=timezone.localdate(),
                status=RequestModel.Status.COMPLETED,
            ).count()
            if used >= 1:
                raise ValueError("Free plan allows only 1 image generation per day.")
            return FREE_IMAGE_POINTS_COST, "Free image generation costs 30 points."
        used = count_image_generations_in_period(user)
        if used >= plan.image_limit:
            raise ValueError("Monthly image generation limit reached.")
        return 0, "Included in plan."
    raise ValueError("Unsupported generation type.")


def preview_generation(user, validated_data: dict) -> dict:
    generation_type = validated_data["generation_type"]
    cost, reason = determine_cost(user, generation_type)
    subscription = get_user_subscription(user)
    plan = subscription.plan
    text_used = count_generations_in_period(user, GenerationRequest.GenerationType.TEXT)
    image_used = count_image_generations_in_period(user)
    if plan.code == "free":
        image_used = GenerationRequest.objects.filter(
            user=user,
            generation_type__in=[
                GenerationRequest.GenerationType.IMAGE,
                GenerationRequest.GenerationType.FULL_POST,
            ],
            created_at__date=timezone.localdate(),
            status=GenerationRequest.Status.COMPLETED,
        ).count()
    return {
        "cost": cost,
        "reason": reason,
        "plan_code": plan.code,
        "text_limit": plan.text_limit,
        "image_limit": plan.image_limit,
        "text_used": text_used,
        "image_used": image_used,
        "points_balance": user.wallet.points_balance,
    }


def _generate_payload(prompt: str, generation_type: str, output_format: str, title: str, call_to_action: str, style: str):
    if generation_type == GenerationRequest.GenerationType.IMAGE:
        return (
            generate_fake_image(prompt, output_format, style=style)
            if _use_fake_ai()
            else generate_real_image(prompt, output_format, style=style)
        )
    if generation_type == GenerationRequest.GenerationType.FULL_POST:
        if _use_fake_ai():
            text_response = generate_fake_text(prompt, generation_type, title=title, cta=call_to_action)
            image_prompt = (
                text_response.payload.get("image_prompt")
                if isinstance(text_response.payload, dict)
                else None
            ) or prompt
            image_response = generate_fake_image(image_prompt, output_format, style=style)
            payload = {**text_response.payload, **image_response.payload}
            return AIResponse(
                text=text_response.text,
                payload=payload,
                provider=text_response.provider,
                model=text_response.model,
                image_url=image_response.image_url,
            )
        text_response = generate_real_text(prompt, generation_type, title=title, cta=call_to_action)
        from django.conf import settings

        if settings.AI_IMAGE_PROVIDER and settings.AI_IMAGE_API_KEY and settings.AI_IMAGE_MODEL:
            try:
                image_prompt = text_response.payload.get("image_prompt") if isinstance(text_response.payload, dict) else None
                image_response = generate_real_image(image_prompt or prompt, output_format, style=style)
                payload = {**text_response.payload, **image_response.payload}
                return AIResponse(
                    text=text_response.text,
                    payload=payload,
                    provider=text_response.provider,
                    model=text_response.model,
                    image_url=image_response.image_url,
                )
            except Exception:
                from logging import getLogger

                getLogger(__name__).exception("Real full post image generation failed.")
        return text_response
    return generate_fake_text(prompt, generation_type, title=title, cta=call_to_action) if _use_fake_ai() else generate_real_text(prompt, generation_type, title=title, cta=call_to_action)


def _use_fake_ai() -> bool:
    from django.conf import settings

    return settings.AI_PROVIDER_MODE == "fake"


def _preferred_generation_text(ai_response: AIResponse, generation_type: str) -> str:
    if generation_type == GenerationRequest.GenerationType.FULL_POST and isinstance(ai_response.payload, dict):
        for key in ("caption", "content", "short_hook", "title"):
            value = ai_response.payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ai_response.text


def _is_generic_full_post_text(text: str) -> bool:
    normalized = re.sub(r"\s+", " ", text).strip().lower()
    return any(
        marker in normalized
        for marker in [
            "your brand helps your audience",
            "your audience",
            "your brand",
            "a clearer offer",
            "aligned with your offer",
            "get better results with a friendly message",
            "a cleaner way to present your offer",
            "this post is designed to communicate real value",
            "book a demo and see how it works",
            "if this helped, it's time to try it",
            "want to improve your offer with a clearer experience",
            "turn your offer into a message that's easier to understand",
        ]
    )


def _repair_full_post_response(prompt: str, ai_response: AIResponse, title: str, cta: str) -> AIResponse:
    fields = _parse_prompt_fields(prompt)
    caption = _caption_for_context(fields)
    hashtags = _build_hashtags(fields, (fields.get("language") or "en").lower())
    short_hook = ai_response.payload.get("short_hook") if isinstance(ai_response.payload, dict) else ""
    if not isinstance(short_hook, str) or not short_hook.strip() or "your" in short_hook.lower():
        short_hook = _resolve_short_hook(fields)
    package = {
        "title": title or (ai_response.payload.get("title") if isinstance(ai_response.payload, dict) else "") or "Postalia Idea",
        "short_hook": short_hook,
        "caption": caption,
        "hashtags": hashtags,
        "carousel_slides": (
            ai_response.payload.get("carousel_slides")
            if isinstance(ai_response.payload, dict) and isinstance(ai_response.payload.get("carousel_slides"), list)
            else [
                "Slide 1: Hook",
                "Slide 2: Problem",
                "Slide 3: Solution",
                "Slide 4: Proof",
                f"Slide 5: {cta or 'Book a demo'}",
            ]
        ),
        "image_prompt": (
            ai_response.payload.get("image_prompt")
            if isinstance(ai_response.payload, dict) and isinstance(ai_response.payload.get("image_prompt"), str)
            else prompt
        ),
        "call_to_action": cta or (
            ai_response.payload.get("call_to_action") if isinstance(ai_response.payload, dict) else ""
        ) or "Book a demo",
        "output_format": fields.get("output format") or "feed_square",
        "style": fields.get("visual style") or "realistic",
        "image_url": ai_response.image_url
        or (
            ai_response.payload.get("image_url") if isinstance(ai_response.payload, dict) else ""
        )
        or "",
        "source_prompt": prompt,
        "recommended_design_notes": (
            ai_response.payload.get("recommended_design_notes")
            if isinstance(ai_response.payload, dict) and isinstance(ai_response.payload.get("recommended_design_notes"), str)
            else "Use brand colors, strong hierarchy and a clear CTA."
        ),
    }
    return AIResponse(
        text=json.dumps(package, ensure_ascii=False),
        payload=package,
        provider=ai_response.provider,
        model=ai_response.model,
        image_url=ai_response.image_url,
    )


def create_generation(user, validated_data: dict) -> GenerationRequest:
    brand = validated_data["brand"]
    template = validated_data.get("template")
    generation_type = validated_data["generation_type"]
    output_format = validated_data.get("output_format") or GenerationRequest.OutputFormat.FEED_SQUARE
    style = validated_data.get("style") or "realistic"
    topic = validated_data["topic"]
    product_service = validated_data.get("product_service", "")
    objective = validated_data["objective"]
    tone = validated_data["tone"]
    language = validated_data["language"]
    campaign_theme = validated_data.get("campaign_theme", "")
    special_offer = validated_data.get("special_offer", "")
    title = validated_data.get("title", "")
    call_to_action = validated_data.get("call_to_action", "")

    if brand.user_id != user.id:
        raise PermissionError("You do not own this brand.")
    allowed, reason = can_use_brand_for_generation(user, brand)
    if not allowed:
        raise PermissionError(reason or "This brand is not available on your current plan.")
    if template and template.brand_id != brand.id:
        raise PermissionError("Template does not belong to the selected brand.")
    if brand.website and not (brand.website_context or {}).get("status") == "captured":
        try:
            refresh_brand_website_context(brand)
        except Exception:
            pass

    prompt = build_prompt(
        brand,
        template,
        generation_type,
        topic,
        product_service,
        objective,
        tone,
        language,
        campaign_theme,
        special_offer,
        output_format,
        style,
    )
    allowed, reason = moderate_text(prompt)
    if not allowed:
        return GenerationRequest.objects.create(
            user=user,
            brand=brand,
            template=template,
            generation_type=generation_type,
            output_format=output_format,
            prompt_input=prompt,
            status=GenerationRequest.Status.BLOCKED,
            error_message=reason or "Blocked by moderation.",
        )

    try:
        cost, cost_reason = determine_cost(user, generation_type)
    except ValueError as exc:
        return GenerationRequest.objects.create(
            user=user,
            brand=brand,
            template=template,
            generation_type=generation_type,
            output_format=output_format,
            prompt_input=prompt,
            status=GenerationRequest.Status.BLOCKED,
            error_message=str(exc),
        )
    if cost > 0:
        wallet = ensure_wallet(user)
        if wallet.points_balance < cost:
            return GenerationRequest.objects.create(
                user=user,
                brand=brand,
                template=template,
                generation_type=generation_type,
                output_format=output_format,
                prompt_input=prompt,
                status=GenerationRequest.Status.BLOCKED,
                error_message=f"Insufficient points. {cost_reason}",
            )
    try:
        ai_response = _generate_payload(prompt, generation_type, output_format, title, call_to_action, style)
        if generation_type == GenerationRequest.GenerationType.FULL_POST and _use_fake_ai():
            if _is_generic_full_post_text(_preferred_generation_text(ai_response, generation_type)):
                ai_response = _repair_full_post_response(prompt, ai_response, title, call_to_action)
        generated_text = _preferred_generation_text(ai_response, generation_type)
        with transaction.atomic():
            if cost > 0:
                spend_points(
                    user,
                    cost,
                    CreditTransaction.TransactionType.GENERATION_SPEND,
                    cost_reason,
                    {"generation_type": generation_type, "brand_id": brand.id},
                )
            generation = GenerationRequest.objects.create(
                user=user,
                brand=brand,
                template=template,
                generation_type=generation_type,
                output_format=output_format,
                prompt_input=prompt,
                generated_text=generated_text,
                generated_payload=ai_response.payload,
                generated_image_url=ai_response.image_url or "",
                ai_provider=ai_response.provider,
                ai_model=ai_response.model,
                points_spent=cost,
                status=GenerationRequest.Status.COMPLETED,
            )
    except Exception as exc:
        generation = GenerationRequest.objects.create(
            user=user,
            brand=brand,
            template=template,
            generation_type=generation_type,
            output_format=output_format,
            prompt_input=prompt,
            status=GenerationRequest.Status.FAILED,
            error_message=str(exc),
        )
    from apps.referrals.services import maybe_reward_referral_on_first_generation

    maybe_reward_referral_on_first_generation(user)
    return generation


def list_user_generations(user):
    return GenerationRequest.objects.filter(user=user).select_related("brand", "template")
