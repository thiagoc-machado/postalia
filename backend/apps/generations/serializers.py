from rest_framework import serializers

from apps.brands.models import Brand, BrandTemplate

from .models import GenerationRequest


class GenerationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenerationRequest
        fields = "__all__"
        read_only_fields = (
            "id",
            "user",
            "generated_text",
            "generated_payload",
            "generated_image_url",
            "ai_provider",
            "ai_model",
            "points_spent",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        )


class GenerationCreateSerializer(serializers.Serializer):
    IMAGE_STYLES = [
        "realistic",
        "animated",
        "cartoon",
        "ghibli",
        "stick_figure",
        "isometric",
        "flat",
        "minimal",
        "three_d",
        "cyberpunk",
        "editorial",
        "premium_clean",
        "watercolor",
    ]

    brand_id = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.none(), source="brand")
    template_id = serializers.PrimaryKeyRelatedField(
        queryset=BrandTemplate.objects.none(), source="template", required=False, allow_null=True
    )
    generation_type = serializers.ChoiceField(choices=GenerationRequest.GenerationType.choices)
    output_format = serializers.ChoiceField(choices=GenerationRequest.OutputFormat.choices, required=False)
    style = serializers.ChoiceField(choices=IMAGE_STYLES, required=False, default="realistic")
    topic = serializers.CharField()
    product_service = serializers.CharField(required=False, allow_blank=True)
    objective = serializers.ChoiceField(
        choices=["sell", "educate", "announce promotion", "engagement", "brand awareness"]
    )
    tone = serializers.ChoiceField(
        choices=["professional", "friendly", "fun", "luxury", "urgent", "inspirational"]
    )
    language = serializers.ChoiceField(choices=["en", "es", "pt"])
    campaign_theme = serializers.CharField(required=False, allow_blank=True)
    special_offer = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    call_to_action = serializers.CharField(required=False, allow_blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            self.fields["brand_id"].queryset = Brand.objects.filter(user=request.user)
            self.fields["template_id"].queryset = BrandTemplate.objects.filter(brand__user=request.user)
