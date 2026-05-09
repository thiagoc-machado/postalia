from __future__ import annotations

from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.rates import AdsThrottle

from .serializers import RewardedAdCompleteSerializer, RewardedAdEventSerializer, RewardedAdStatusSerializer
from .services import complete_rewarded_ad, rewarded_ad_status


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class RewardedAdStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(RewardedAdStatusSerializer(rewarded_ad_status(request.user)).data)


class RewardedAdCompleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AdsThrottle]

    def post(self, request):
        if not settings.ENABLE_DEV_FAKE_AD_REWARDS:
            return Response({"detail": "Simulation disabled."}, status=status.HTTP_403_FORBIDDEN)
        serializer = RewardedAdCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            event = complete_rewarded_ad(
                request.user,
                serializer.validated_data["external_event_id"],
                _client_ip(request),
                request.META.get("HTTP_USER_AGENT"),
                metadata=serializer.validated_data.get("metadata"),
                provider=getattr(settings, "REWARDED_AD_PROVIDER", "mock"),
            )
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        request.user.wallet.refresh_from_db(fields=["points_balance"])
        data = RewardedAdEventSerializer(event).data
        data["points_balance"] = request.user.wallet.points_balance
        return Response(data, status=status.HTTP_201_CREATED)
