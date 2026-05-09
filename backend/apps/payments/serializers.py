from __future__ import annotations

from rest_framework import serializers

from .models import PaymentSubscription


class BillingCheckoutSerializer(serializers.Serializer):
    plan_code = serializers.ChoiceField(choices=["starter", "pro", "agency"])


class BillingSubscriptionSerializer(serializers.Serializer):
    plan_code = serializers.CharField()
    status = serializers.CharField()
    current_period_start = serializers.CharField(allow_null=True)
    current_period_end = serializers.CharField(allow_null=True)
    cancel_at_period_end = serializers.BooleanField()
    payment_provider = serializers.CharField()


class BillingPortalSerializer(serializers.Serializer):
    portal_url = serializers.CharField(allow_null=True, required=False)
    detail = serializers.CharField(required=False, allow_blank=True)


class PaymentSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentSubscription
        fields = "__all__"
