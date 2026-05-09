from rest_framework import serializers

from .models import Referral


class ReferralSerializer(serializers.ModelSerializer):
    referrer_email = serializers.EmailField(source="referrer.email", read_only=True)
    referred_user_email = serializers.EmailField(source="referred_user.email", read_only=True)

    class Meta:
        model = Referral
        fields = "__all__"


class ReferralSummarySerializer(serializers.Serializer):
    referral_code = serializers.CharField()
    sent = ReferralSerializer(many=True)


class ReferralApplySerializer(serializers.Serializer):
    referral_code = serializers.CharField(max_length=12)
