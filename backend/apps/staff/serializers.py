from rest_framework import serializers

from apps.accounts.models import User
from apps.generations.models import GenerationRequest
from apps.risk.models import RiskEvent
from apps.subscriptions.models import SubscriptionPlan


class StaffUserSerializer(serializers.ModelSerializer):
    wallet_balance = serializers.IntegerField(source="wallet.points_balance", read_only=True)
    plan_code = serializers.CharField(source="subscription.plan.code", read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "name", "is_active", "is_staff", "auth_provider", "wallet_balance", "plan_code"]


class StaffPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = "__all__"


class StaffRiskEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskEvent
        fields = "__all__"


class StaffGenerationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenerationRequest
        fields = "__all__"


class StaffSummarySerializer(serializers.Serializer):
    users = serializers.IntegerField()
    brands = serializers.IntegerField()
    generations = serializers.IntegerField()
    risk_events = serializers.IntegerField()
