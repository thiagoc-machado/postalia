from rest_framework import serializers

from .models import CreditTransaction, CreditWallet, DailyLoginReward


class CreditTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditTransaction
        fields = "__all__"


class CreditWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditWallet
        fields = "__all__"


class DailyLoginRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyLoginReward
        fields = "__all__"
