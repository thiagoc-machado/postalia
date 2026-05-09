from __future__ import annotations

import io
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlparse

import pytest
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework_simplejwt.tokens import RefreshToken
from PIL import Image

from apps.ads.models import RewardedAdEvent
from apps.ai_providers.services import generate_fake_image, generate_fake_text, generate_real_image, generate_real_text, validate_ai_configuration
from apps.brands.models import Brand, BrandTemplate
from apps.brands.services import extract_website_context
from apps.credits.models import CreditTransaction
from apps.credits.services import grant_points, spend_points
from apps.generations.services import build_prompt
from apps.referrals.models import Referral
from apps.referrals.services import register_referral

from apps.accounts.models import User


def auth_client(api_client, user):
    token = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


def create_brand_and_template(
    client,
    *,
    name: str,
    niche: str = "Marketing",
    language: str = "en",
    tone_of_voice: str = "friendly",
    description: str = "Brand",
    products_services: str = "SaaS",
    target_audience: str = "Customers",
    website: str = "https://example.com",
    instagram_handle: str | None = None,
):
    fake_context = {
        "status": "captured",
        "source_url": "https://example.com",
        "title": "Example Brand",
        "description": "Example website description",
        "colors": ["#112233", "#f8be27"],
        "text_excerpt": "Example site excerpt",
        "summary": "Example Brand | Example website description | Colors: #112233, #f8be27 | Example site excerpt",
    }

    def _fake_refresh(brand):
        brand.website_context = fake_context
        Brand.objects.filter(pk=brand.pk).update(website_context=fake_context)
        return fake_context

    with patch("apps.brands.serializers.refresh_brand_website_context", side_effect=_fake_refresh):
        response = client.post(
            "/api/brands/",
            {
                "name": name,
                "niche": niche,
                "target_audience": target_audience,
                "tone_of_voice": tone_of_voice,
                "description": description,
                "products_services": products_services,
                "website": website,
                "instagram_handle": instagram_handle or f"@{name.lower().replace(' ', '')}",
                "language": language,
                "is_default": True,
                "create_default_template": True,
            },
            format="json",
        )
    brand_id = response.data["id"]
    template_id = Brand.objects.get(id=brand_id).templates.first().id
    return brand_id, template_id


@pytest.mark.django_db
@override_settings(GOOGLE_ONLY=True)
def test_auth_config_reflects_google_only(api_client):
    response = api_client.get("/api/auth/config/")
    assert response.status_code == 200
    assert response.data["google_only"] is True
    assert response.data["local_auth_enabled"] is False


@pytest.mark.django_db
@override_settings(GOOGLE_ONLY=True)
def test_local_login_blocked_when_google_only(api_client):
    user = User.objects.create_user(email="local@example.com", password="Password123!", name="Local User")
    response = api_client.post("/api/auth/login/", {"email": user.email, "password": "Password123!"}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
@override_settings(GOOGLE_ONLY=False)
def test_local_login_allowed_when_google_only_false(api_client):
    user = User.objects.create_user(email="local@example.com", password="Password123!", name="Local User")
    response = api_client.post("/api/auth/login/", {"email": user.email, "password": "Password123!"}, format="json")
    assert response.status_code == 200
    assert response.data["user"]["email"] == user.email


@pytest.mark.django_db
@override_settings(GOOGLE_ONLY=False)
def test_google_login_creates_user(api_client):
    with patch("apps.accounts.views.verify_google_credential") as mocked_verify:
        mocked_verify.return_value = {
            "email": "google@example.com",
            "sub": "google-sub-123",
            "email_verified": True,
            "name": "Google User",
        }
        response = api_client.post("/api/auth/google/", {"credential": "dummy"}, format="json")
    assert response.status_code == 200
    user = User.objects.get(email="google@example.com")
    assert user.auth_provider == User.AuthProvider.GOOGLE
    assert user.google_sub == "google-sub-123"


@pytest.mark.django_db
def test_brand_limit_and_duplicate_name(api_client):
    user = User.objects.create_user(email="brand@example.com", password="Password123!", name="Brand User")
    client = auth_client(api_client, user)
    payload = {
        "name": "Cafe Uno",
        "niche": "Food",
        "target_audience": "Local customers",
        "tone_of_voice": "friendly",
        "description": "Cafe brand",
        "products_services": "Coffee",
        "website": "https://example.com",
        "instagram_handle": "@cafeuno",
        "language": "en",
        "is_default": True,
    }
    with patch("apps.brands.serializers.refresh_brand_website_context") as mocked_refresh:
        mocked_refresh.side_effect = lambda brand: {"status": "captured", "summary": "Mock context"}
        first = client.post("/api/brands/", {**payload, "create_default_template": True}, format="json")
        assert first.status_code == 201
        duplicate = client.post("/api/brands/", {**payload, "name": "Cafe Uno 2", "create_default_template": True}, format="json")
        assert duplicate.status_code == 403
        same_name = client.post("/api/brands/", {**payload, "create_default_template": True}, format="json")
        assert same_name.status_code == 400


@pytest.mark.django_db
def test_brand_permissions_are_isolated(api_client):
    owner = User.objects.create_user(email="owner@example.com", password="Password123!", name="Owner")
    stranger = User.objects.create_user(email="stranger@example.com", password="Password123!", name="Stranger")
    owner_client = auth_client(api_client, owner)
    with patch("apps.brands.serializers.refresh_brand_website_context") as mocked_refresh:
        mocked_refresh.side_effect = lambda brand: {"status": "captured", "summary": "Mock context"}
        response = owner_client.post(
            "/api/brands/",
            {
                "name": "Private Brand",
                "niche": "Food",
                "target_audience": "Customers",
                "tone_of_voice": "friendly",
                "description": "Brand",
                "products_services": "Meals",
                "website": "https://example.com",
                "instagram_handle": "@private",
                "language": "en",
                "is_default": True,
                "create_default_template": True,
            },
            format="json",
        )
    brand_id = response.data["id"]
    stranger_client = auth_client(api_client, stranger)
    forbidden = stranger_client.get(f"/api/brands/{brand_id}/")
    assert forbidden.status_code == 404


@pytest.mark.django_db
def test_brand_name_cannot_be_edited(api_client):
    user = User.objects.create_user(email="rename@example.com", password="Password123!", name="Rename User")
    client = auth_client(api_client, user)
    brand_id, _template_id = create_brand_and_template(client, name="Locked Brand")

    response = client.patch(
        f"/api/brands/{brand_id}/",
        {
            "name": "New Name",
            "niche": "Food",
        },
        format="json",
    )
    assert response.status_code == 400
    assert "name" in response.data
    assert Brand.objects.get(id=brand_id).name == "Locked Brand"


@pytest.mark.django_db
@override_settings(MEDIA_ROOT="/tmp/postalia-test-media")
def test_brand_logo_is_cropped_to_square(api_client):
    user = User.objects.create_user(email="logo@example.com", password="Password123!", name="Logo User")
    client = auth_client(api_client, user)

    image = Image.new("RGB", (160, 80), color=(255, 0, 0))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    with patch("apps.brands.serializers.refresh_brand_website_context") as mocked_refresh:
        mocked_refresh.side_effect = lambda brand: {"status": "captured", "summary": "Mock context"}
        response = client.post(
            "/api/brands/",
            {
                "name": "Logo Brand",
                "niche": "Food",
                "target_audience": "Customers",
                "tone_of_voice": "friendly",
                "description": "Brand",
                "products_services": "Meals",
                "website": "https://example.com",
                "instagram_handle": "@logo",
                "language": "en",
                "is_default": True,
                "create_default_template": True,
                "logo": SimpleUploadedFile("logo.png", buffer.getvalue(), content_type="image/png"),
            },
            format="multipart",
        )

    assert response.status_code == 201
    brand = Brand.objects.get(id=response.data["id"])
    assert brand.logo
    with Image.open(brand.logo.path) as saved_image:
        assert saved_image.width == saved_image.height
        assert saved_image.width == 1024


@pytest.mark.django_db
def test_website_context_extraction_and_prompt_inclusion(monkeypatch):
    html = """
    <html>
      <head>
        <title>MagisMenu</title>
        <meta name="description" content="Restaurant SaaS with QR orders and live kitchen sync">
        <meta property="og:image" content="https://cdn.example.com/brand.png">
        <meta name="theme-color" content="#f8be27">
      </head>
      <body>
        <h1>Más pedidos, menos caos</h1>
        <p>Pedidos por QR, cocina sincronizada e controle total.</p>
        <style>body{background:#112233;color:#f8be27}</style>
      </body>
    </html>
    """

    class FakeResponse:
        def raise_for_status(self):
            return None

        @property
        def text(self):
            return html

    monkeypatch.setattr("apps.brands.services.socket.getaddrinfo", lambda *args, **kwargs: [(None, None, None, None, ("93.184.216.34", 0))])
    monkeypatch.setattr("apps.brands.services.httpx.get", lambda *args, **kwargs: FakeResponse())

    context = extract_website_context("https://magismenu.com")
    assert context["status"] == "captured"
    assert context["title"] == "MagisMenu"
    assert context["description"] == "Restaurant SaaS with QR orders and live kitchen sync"
    assert "#112233" in context["colors"]
    assert "#f8be27" in context["colors"]

    user = User.objects.create_user(email="context@example.com", password="Password123!", name="Context User")
    brand = Brand.objects.create(
        user=user,
        name="MagisMenu",
        niche="saas",
        target_audience="restaurant owners",
        tone_of_voice="friendly",
        description="Restaurant SaaS",
        products_services="QR orders",
        website="https://magismenu.com",
        instagram_handle="@magismenu",
        language="es",
        is_default=True,
        website_context=context,
    )
    template = BrandTemplate.objects.create(
        brand=brand,
        name="Base Template",
        base_prompt="Use clear hierarchy and brand colors.",
        visual_style="Clean",
        copywriting_style="Friendly",
        forbidden_topics="",
        preferred_cta="Book a demo",
    )
    prompt = build_prompt(
        brand,
        template,
        "full_post",
        "menos filas",
        "QR orders",
        "sell",
        "friendly",
        "es",
        output_format="feed_square",
        style="realistic",
    )
    assert "Website context:" in prompt
    assert "MagisMenu" in prompt
    assert "#112233" in prompt
    assert "restaurant operations software" in prompt.lower()
    assert "food photography" in prompt.lower()


@pytest.mark.django_db
def test_full_post_uses_brand_context_for_caption_and_hashtags(api_client):
    user = User.objects.create_user(email="contextfull@example.com", password="Password123!", name="Context Full User")
    client = auth_client(api_client, user)
    brand_id, template_id = create_brand_and_template(
        client,
        name="Magismenu",
        niche="saas",
        language="es",
        tone_of_voice="animada e confiante",
        description="Sistema de controle de pedidos automatizado para restaurantes.",
        products_services="Pedidos por QR, totens, garçom com tablets, cozinha sincronizada e painel administrativo.",
        target_audience="donos de restaurantes, bares e lanchonetes",
        website="https://magismenu.com",
        instagram_handle="magismenu.com/",
    )

    response = client.post(
        "/api/generations/",
        {
            "brand_id": brand_id,
            "template_id": template_id,
            "generation_type": "full_post",
            "output_format": "feed_square",
            "style": "realistic",
            "topic": "moderno",
            "product_service": "",
            "objective": "sell",
            "tone": "friendly",
            "language": "es",
        },
        format="json",
    )
    assert response.status_code == 201
    caption = response.data["generated_text"].lower()
    payload = response.data["generated_payload"]
    assert "your brand" not in caption
    assert "your audience" not in caption
    assert any(keyword in caption for keyword in ["pedidos", "pedido", "qr", "cocina", "controle"])
    assert response.data["generated_image_url"]
    assert any("#magismenu" in tag.lower() or "#restaurantes" in tag.lower() for tag in payload.get("hashtags", []))


@pytest.mark.django_db
def test_wallet_transaction_integrity():
    user = User.objects.create_user(email="wallet@example.com", password="Password123!", name="Wallet User")
    grant_points(user, 20, CreditTransaction.TransactionType.MANUAL, "Test grant")
    spend_points(user, 7, CreditTransaction.TransactionType.MANUAL, "Test spend")
    user.wallet.refresh_from_db()
    assert user.wallet.points_balance == 13
    assert user.wallet.transactions.count() == 2

    with pytest.raises(ValueError):
        spend_points(user, 999, CreditTransaction.TransactionType.MANUAL, "Too much")


@pytest.mark.django_db
def test_generation_preview_and_free_text_cost(api_client):
    user = User.objects.create_user(email="gen@example.com", password="Password123!", name="Gen User")
    client = auth_client(api_client, user)
    brand_id, template_id = create_brand_and_template(client, name="Studio Uno")

    payload = {
        "brand_id": brand_id,
        "template_id": template_id,
        "generation_type": "text",
        "output_format": "feed_square",
        "topic": "New offer",
        "product_service": "Consulting",
        "objective": "sell",
        "tone": "friendly",
        "language": "en",
    }
    for _ in range(3):
        response = client.post("/api/generations/", payload, format="json")
        assert response.status_code == 201
        assert response.data["status"] == "completed"

    preview = client.post("/api/generations/preview/", payload, format="json")
    assert preview.status_code == 200
    assert preview.data["cost"] == 5


@pytest.mark.django_db
def test_full_post_costs_more_than_image_and_counts_as_image_quota(api_client):
    user = User.objects.create_user(email="fullpostcost@example.com", password="Password123!", name="Full Post Cost User")
    grant_points(user, 200, CreditTransaction.TransactionType.MANUAL, "Test grant")
    client = auth_client(api_client, user)
    brand_id, template_id = create_brand_and_template(client, name="Full Post Cost Studio")

    image_payload = {
        "brand_id": brand_id,
        "template_id": template_id,
        "generation_type": "image",
        "output_format": "feed_square",
        "style": "animated",
        "topic": "Launch campaign",
        "product_service": "Consulting",
        "objective": "sell",
        "tone": "friendly",
        "language": "en",
    }
    full_post_payload = {
        **image_payload,
        "generation_type": "full_post",
    }

    image_preview = client.post("/api/generations/preview/", image_payload, format="json")
    full_post_preview = client.post("/api/generations/preview/", full_post_payload, format="json")
    assert image_preview.status_code == 200
    assert full_post_preview.status_code == 200
    assert image_preview.data["cost"] == 30
    assert full_post_preview.data["cost"] > image_preview.data["cost"]

    first_image = client.post("/api/generations/", image_payload, format="json")
    assert first_image.status_code == 201
    assert first_image.data["status"] == "completed"

    blocked_full_post = client.post("/api/generations/", full_post_payload, format="json")
    assert blocked_full_post.status_code == 201
    assert blocked_full_post.data["status"] == "blocked"
    assert "image generation" in blocked_full_post.data["error_message"].lower()


@pytest.mark.django_db
def test_full_post_fake_generation_returns_image(api_client):
    user = User.objects.create_user(email="fullpost@example.com", password="Password123!", name="Full Post User")
    grant_points(user, 200, CreditTransaction.TransactionType.MANUAL, "Test grant")
    client = auth_client(api_client, user)
    brand_id, template_id = create_brand_and_template(client, name="Full Post Studio")

    response = client.post(
        "/api/generations/",
        {
            "brand_id": brand_id,
            "template_id": template_id,
            "generation_type": "full_post",
            "output_format": "feed_square",
            "style": "animated",
            "topic": "Launch campaign",
            "product_service": "Consulting",
            "objective": "sell",
            "tone": "friendly",
            "language": "en",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["status"] == "completed"
    assert response.data["generated_image_url"]
    assert response.data["generated_payload"]["image_url"] == response.data["generated_image_url"]
    assert "Visual style: animated" in response.data["prompt_input"]
    assert response.data["generated_payload"]["style"] == "animated"
    assert "Demo content" not in response.data["generated_text"]


@pytest.mark.django_db
def test_image_generation_blocked_has_clear_reason(api_client):
    user = User.objects.create_user(email="imageblocked@example.com", password="Password123!", name="Image Blocked User")
    client = auth_client(api_client, user)
    brand_id, template_id = create_brand_and_template(client, name="Image Blocked Studio")

    response = client.post(
        "/api/generations/",
        {
            "brand_id": brand_id,
            "template_id": template_id,
            "generation_type": "image",
            "output_format": "feed_square",
            "topic": "Launch campaign",
            "product_service": "Consulting",
            "objective": "sell",
            "tone": "friendly",
            "language": "en",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["status"] == "blocked"
    assert "points" in response.data["error_message"].lower()


@pytest.mark.django_db
def test_rewarded_ads_limit_and_duplicate(api_client):
    user = User.objects.create_user(email="ads@example.com", password="Password123!", name="Ads User")
    client = auth_client(api_client, user)
    payload = {"provider": "dev", "external_event_id": "event-1"}
    first = client.post("/api/ads/rewarded/complete/", payload, format="json")
    second = client.post("/api/ads/rewarded/complete/", {"provider": "dev", "external_event_id": "event-2"}, format="json")
    third = client.post("/api/ads/rewarded/complete/", {"provider": "dev", "external_event_id": "event-3"}, format="json")
    duplicate = client.post("/api/ads/rewarded/complete/", payload, format="json")
    assert first.status_code == 201
    assert second.status_code == 201
    assert third.status_code == 400
    assert duplicate.status_code == 400
    assert RewardedAdEvent.objects.filter(user=user, status=RewardedAdEvent.Status.COMPLETED).count() == 2


@pytest.mark.django_db
def test_referral_reward_on_first_generation(api_client):
    referrer = User.objects.create_user(email="referrer@example.com", password="Password123!", name="Referrer")
    referred = User.objects.create_user(email="referred@example.com", password="Password123!", name="Referred")
    register_referral(referred, referrer.referral_code)

    client = auth_client(api_client, referred)
    brand_response = client.post(
        "/api/brands/",
        {
            "name": "Referral Brand",
            "niche": "Food",
            "target_audience": "Customers",
            "tone_of_voice": "friendly",
            "description": "Brand",
            "products_services": "Meals",
            "website": "https://example.com",
            "instagram_handle": "@refbrand",
            "language": "en",
            "is_default": True,
            "create_default_template": True,
        },
        format="json",
    )
    brand_id = brand_response.data["id"]
    template_id = Brand.objects.get(id=brand_id).templates.first().id
    response = client.post(
        "/api/generations/",
        {
            "brand_id": brand_id,
            "template_id": template_id,
            "generation_type": "text",
            "output_format": "feed_square",
            "topic": "Referral test",
            "product_service": "Meals",
            "objective": "engagement",
            "tone": "friendly",
            "language": "en",
        },
        format="json",
    )
    assert response.status_code == 201
    referral = Referral.objects.get(referred_user=referred)
    referral.refresh_from_db()
    referrer.wallet.refresh_from_db()
    assert referral.status == Referral.Status.REWARDED
    assert referrer.wallet.points_balance == 15


@pytest.mark.django_db
def test_fake_ai_deterministic_outputs():
    prompt = "Brand prompt for a coffee shop"
    one = generate_fake_text(prompt, "full_post")
    two = generate_fake_text(prompt, "full_post")
    assert one.text == two.text
    image = generate_fake_image(prompt, "feed_square")
    assert image.image_url


@pytest.mark.django_db
def test_fake_text_varies_for_different_topics():
    base = (
        "Brand: Magismenu\n"
        "Niche: saas\n"
        "Audience: donos de restaurantes, bares e lanchonetes\n"
        "Tone: friendly\n"
        "Language: es\n"
        "Objective: sell\n"
        "Generation type: full_post\n"
        "Output format: feed_square\n"
    )
    first = generate_fake_text(base + "Topic: menos filas\n", "full_post")
    second = generate_fake_text(base + "Topic: mais controle em hora pico\n", "full_post")
    assert first.text != second.text
    assert "your brand" not in first.text.lower()
    assert "your audience" not in second.text.lower()


@pytest.mark.django_db
def test_fake_image_fallback_is_not_placeholder(monkeypatch):
    class BrokenResponse:
        def raise_for_status(self):
            raise Exception("demo-ai unavailable")

    monkeypatch.setattr("apps.ai_providers.services.httpx.post", lambda *args, **kwargs: BrokenResponse())
    prompt = (
        "Brand: Magismenu\n"
        "Niche: saas\n"
        "Audience: donos de restaurantes, bares e lanchonetes\n"
        "Tone: friendly\n"
        "Language: es\n"
        "Objective: sell\n"
        "Generation type: image\n"
        "Output format: feed_square\n"
        "Topic: sistema de controle de pedidos automatizado e sincronizado em tempo real\n"
        "Product/Service: sistema de controle de pedidos automatizado e sincronizado em tempo real\n"
    )
    image = generate_fake_image(prompt, "feed_square")
    assert image.image_url
    assert "placeholder" not in image.image_url
    assert image.payload["fallback_reason"] == "Exception"


@pytest.mark.django_db
def test_export_sets_watermark_on_free_plan(api_client):
    user = User.objects.create_user(email="export@example.com", password="Password123!", name="Export User")
    client = auth_client(api_client, user)
    brand_response = client.post(
        "/api/brands/",
        {
            "name": "Export Brand",
            "niche": "Marketing",
            "target_audience": "SMBs",
            "tone_of_voice": "friendly",
            "description": "Brand",
            "products_services": "Consulting",
            "website": "https://example.com",
            "instagram_handle": "@export",
            "language": "en",
            "is_default": True,
            "create_default_template": True,
        },
        format="json",
    )
    brand_id = brand_response.data["id"]
    template_id = Brand.objects.get(id=brand_id).templates.first().id
    generation = client.post(
        "/api/generations/",
        {
            "brand_id": brand_id,
            "template_id": template_id,
            "generation_type": "text",
            "output_format": "feed_square",
            "topic": "Export test",
            "product_service": "Consulting",
            "objective": "brand awareness",
            "tone": "friendly",
            "language": "en",
        },
        format="json",
    ).data
    export_response = client.post(f"/api/generations/{generation['id']}/export/", format="json")
    assert export_response.status_code == 201
    assert export_response.data["has_watermark"] is True
    export_file = urlparse(export_response.data["file"]).path.lstrip("/")
    if export_file.startswith("media/"):
        export_file = export_file[len("media/"):]
    assert default_storage.exists(export_file)


def test_validate_ai_configuration():
    fake_prod = SimpleNamespace(
        DEBUG=False,
        AI_PROVIDER_MODE="fake",
        ENABLE_FAKE_AI_IN_PRODUCTION=False,
        AI_TEXT_PROVIDER="",
        AI_TEXT_API_KEY="",
        AI_TEXT_MODEL="",
        AI_IMAGE_PROVIDER="",
        AI_IMAGE_API_KEY="",
        AI_IMAGE_MODEL="",
    )
    with pytest.raises(ValueError):
        validate_ai_configuration(fake_prod)

    real_missing = SimpleNamespace(
        DEBUG=True,
        AI_PROVIDER_MODE="real",
        ENABLE_FAKE_AI_IN_PRODUCTION=False,
        AI_TEXT_PROVIDER="",
        AI_TEXT_API_KEY="",
        AI_TEXT_MODEL="",
        AI_IMAGE_PROVIDER="",
        AI_IMAGE_API_KEY="",
        AI_IMAGE_MODEL="",
    )
    with pytest.raises(ValueError):
        validate_ai_configuration(real_missing)

    local_real = SimpleNamespace(
        DEBUG=True,
        AI_PROVIDER_MODE="real",
        ENABLE_FAKE_AI_IN_PRODUCTION=False,
        AI_TEXT_PROVIDER="local",
        AI_TEXT_API_KEY="",
        AI_TEXT_MODEL="",
        AI_IMAGE_PROVIDER="local",
        AI_IMAGE_API_KEY="",
        AI_IMAGE_MODEL="",
        DEMO_AI_BASE_URL="http://demo-ai:8001",
        DEMO_AI_MODE="real",
        DEMO_AI_TEXT_MODEL="Qwen/Qwen2.5-0.5B-Instruct",
        DEMO_AI_IMAGE_MODEL="stabilityai/sd-turbo",
        DEMO_AI_DEVICE="cpu",
    )
    validate_ai_configuration(local_real)


@pytest.mark.django_db
@override_settings(
    AI_PROVIDER_MODE="real",
    AI_TEXT_PROVIDER="local",
    AI_TEXT_API_KEY="",
    AI_TEXT_MODEL="",
    DEMO_AI_BASE_URL="http://demo-ai:8001",
    DEMO_AI_MODE="real",
    DEMO_AI_TEXT_MODEL="Qwen/Qwen2.5-0.5B-Instruct",
)
def test_real_text_local_provider_uses_demo_ai(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "text": "{\"title\": \"Local\", \"caption\": \"Local caption\"}",
                "payload": {"title": "Local", "caption": "Local caption"},
            }

    seen = {}

    def fake_post(url, **kwargs):
        seen["url"] = url
        seen["kwargs"] = kwargs
        return FakeResponse()

    monkeypatch.setattr("apps.ai_providers.services.httpx.post", fake_post)
    response = generate_real_text(
        "Brand: Demo\nLanguage: en\nTopic: test\n",
        "full_post",
        title="Local title",
        cta="Local CTA",
    )
    assert seen["url"] == "http://demo-ai:8001/text"
    assert seen["kwargs"]["json"] == {
        "prompt": "Brand: Demo\nLanguage: en\nTopic: test\n",
        "generation_type": "full_post",
        "title": "Local title",
        "cta": "Local CTA",
    }
    assert seen["kwargs"]["timeout"] == 300
    assert response.provider == "local"
    assert response.payload["caption"] == "Local caption"


@pytest.mark.django_db
@override_settings(
    AI_PROVIDER_MODE="real",
    AI_IMAGE_PROVIDER="local",
    AI_IMAGE_API_KEY="",
    AI_IMAGE_MODEL="",
    DEMO_AI_BASE_URL="http://demo-ai:8001",
    DEMO_AI_MODE="real",
    DEMO_AI_IMAGE_MODEL="stabilityai/sd-turbo",
)
def test_real_image_local_provider_stores_result(monkeypatch):
    class FakePostResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"image_url": "http://localhost:8001/files/demo.png"}

    class FakeGetResponse:
        content = b"fake-image-bytes"

        def raise_for_status(self):
            return None

    seen = {}

    def fake_post(url, **kwargs):
        seen["post_url"] = url
        seen["post_kwargs"] = kwargs
        return FakePostResponse()

    def fake_get(url, **kwargs):
        seen["get_url"] = url
        return FakeGetResponse()

    monkeypatch.setattr("apps.ai_providers.services.httpx.post", fake_post)
    monkeypatch.setattr("apps.ai_providers.services.httpx.get", fake_get)
    monkeypatch.setattr("apps.ai_providers.services.save_generated_file", lambda file_obj, folder: "/media/generated/demo.png")

    response = generate_real_image("Brand: Demo\nLanguage: en\nTopic: test\n", "feed_square")
    assert seen["post_url"] == "http://demo-ai:8001/image"
    assert seen["post_kwargs"]["json"]["output_format"] == "feed_square"
    assert seen["post_kwargs"]["timeout"] == 900
    assert "software ui advertisement" in seen["post_kwargs"]["json"]["prompt"].lower()
    assert "food photography" in seen["post_kwargs"]["json"]["prompt"].lower()
    assert seen["get_url"] == "http://demo-ai:8001/files/demo.png"
    assert response.provider == "local"
    assert response.image_url == "/media/generated/demo.png"
