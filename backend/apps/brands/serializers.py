from rest_framework import serializers

from .models import Brand, BrandTemplate
from .services import normalize_brand_logo, refresh_brand_website_context


class BrandTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandTemplate
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "brand")


class BrandSerializer(serializers.ModelSerializer):
    templates = BrandTemplateSerializer(many=True, read_only=True)

    class Meta:
        model = Brand
        fields = "__all__"
        read_only_fields = ("id", "slug", "created_at", "updated_at", "user", "website_context")


class BrandUpdateSerializer(serializers.ModelSerializer):
    templates = BrandTemplateSerializer(many=True, read_only=True)
    name = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)

    class Meta:
        model = Brand
        fields = "__all__"
        read_only_fields = (
            "id",
            "name",
            "slug",
            "created_at",
            "updated_at",
            "user",
            "website_context",
            "templates",
        )

    def validate(self, attrs):
        if self.instance is None:
            return attrs
        for locked_field in ("name", "slug"):
            if locked_field in self.initial_data:
                current_value = getattr(self.instance, locked_field, "")
                incoming_value = self.initial_data.get(locked_field)
                if incoming_value is not None and str(incoming_value).strip() != str(current_value).strip():
                    raise serializers.ValidationError({locked_field: "This field cannot be changed."})
        return attrs

    def update(self, instance, validated_data):
        logo = validated_data.get("logo")
        if logo:
            try:
                validated_data["logo"] = normalize_brand_logo(logo)
            except ValueError as exc:
                raise serializers.ValidationError({"logo": str(exc)}) from exc
        website_changed = "website" in validated_data
        instance = super().update(instance, validated_data)
        if website_changed:
            refresh_brand_website_context(instance)
        return instance


class BrandCreateSerializer(serializers.ModelSerializer):
    create_default_template = serializers.BooleanField(default=True, write_only=True)

    class Meta:
        model = Brand
        fields = [
            "name",
            "niche",
            "target_audience",
            "tone_of_voice",
            "description",
            "products_services",
            "website",
            "instagram_handle",
            "logo",
            "primary_color",
            "secondary_color",
            "language",
            "is_default",
            "create_default_template",
        ]

    def validate(self, attrs):
        request = self.context["request"]
        name = attrs.get("name")
        if Brand.objects.filter(user=request.user, name=name).exists():
            raise serializers.ValidationError({"name": "You already have a brand with this name."})
        if not Brand.objects.filter(user=request.user).exists():
            attrs["is_default"] = True
        return attrs

    def create(self, validated_data):
        create_default_template = validated_data.pop("create_default_template", True)
        request = self.context["request"]
        logo = validated_data.get("logo")
        if logo:
            try:
                validated_data["logo"] = normalize_brand_logo(logo)
            except ValueError as exc:
                raise serializers.ValidationError({"logo": str(exc)}) from exc
        brand = Brand.objects.create(user=request.user, **validated_data)
        refresh_brand_website_context(brand)
        if brand.is_default:
            Brand.objects.filter(user=request.user).exclude(pk=brand.pk).update(is_default=False)
        if create_default_template:
            BrandTemplate.objects.create(
                brand=brand,
                name="Base Template",
                base_prompt=self._default_prompt(brand),
                visual_style=self._default_visual_style(brand),
                copywriting_style=self._default_copywriting_style(brand),
                forbidden_topics="",
                preferred_cta="Learn more",
            )
        return brand

    def _default_prompt(self, brand: Brand) -> str:
        website_context = brand.website_context or {}
        website_summary = website_context.get("summary") if isinstance(website_context, dict) else ""
        website_context_block = f"\nWebsite context: {website_summary}" if website_summary else ""
        description_block = f"\nBrand description: {brand.description}" if brand.description else ""
        products_block = f"\nBrand products/services: {brand.products_services}" if brand.products_services else ""
        voice_block = f"\nBrand voice: {brand.tone_of_voice}" if brand.tone_of_voice else ""
        return (
            f"Generate Instagram content for {brand.name} in the {brand.niche} niche, "
            f"speaking to {brand.target_audience}. Use a {brand.tone_of_voice or 'clear and persuasive'} tone, "
            f"highlight {brand.products_services or brand.description or brand.niche} and keep the content aligned with the brand identity."
            f"{description_block}{products_block}{voice_block}"
            f"{website_context_block}"
        )

    def _default_visual_style(self, brand: Brand) -> str:
        palette_hint = []
        if brand.primary_color:
            palette_hint.append(f"primary color {brand.primary_color}")
        if brand.secondary_color:
            palette_hint.append(f"secondary color {brand.secondary_color}")
        palette_text = ", ".join(palette_hint) if palette_hint else "brand colors"
        return (
            f"Premium social media layout using {palette_text}, a strong hero headline, "
            f"clean product mockups and a high-contrast editorial composition"
        )

    def _default_copywriting_style(self, brand: Brand) -> str:
        voice = brand.tone_of_voice or "clear and persuasive"
        audience = brand.target_audience or "the target audience"
        return f"{voice.capitalize()} copywriting focused on {audience}"

    def update(self, instance, validated_data):
        raise serializers.ValidationError({"detail": "Use the brand update endpoint with BrandUpdateSerializer."})
