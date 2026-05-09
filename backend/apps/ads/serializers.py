from rest_framework import serializers

from .models import RewardedAdEvent


class RewardedAdEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardedAdEvent
        fields = "__all__"


class RewardedAdCompleteSerializer(serializers.Serializer):
    provider = serializers.CharField(max_length=50, required=False, allow_blank=True)
    external_event_id = serializers.CharField(max_length=255)
    metadata = serializers.JSONField(required=False)


class RewardedAdStatusSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
    provider = serializers.CharField()
    points_per_ad = serializers.IntegerField()
    daily_limit = serializers.IntegerField()
    watched_today = serializers.IntegerField()
    remaining_today = serializers.IntegerField()
