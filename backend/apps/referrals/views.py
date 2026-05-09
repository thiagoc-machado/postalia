from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.rates import ReferralThrottle

from .models import Referral
from .serializers import ReferralApplySerializer, ReferralSerializer
from .services import confirm_paid_referral, register_referral


class MyReferralsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ReferralThrottle]

    def get(self, request):
        data = {
            "referral_code": request.user.referral_code,
            "sent": ReferralSerializer(request.user.referrals_sent.all(), many=True).data,
        }
        return Response(data)


class ApplyReferralView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ReferralThrottle]

    def post(self, request):
        serializer = ReferralApplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        referral = register_referral(request.user, serializer.validated_data["referral_code"])
        if referral is None:
            return Response({"detail": "Referral not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ReferralSerializer(referral).data, status=status.HTTP_201_CREATED)


class ConfirmPaidReferralView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk: int):
        if not request.user.is_staff:
            return Response({"detail": "Staff only."}, status=status.HTTP_403_FORBIDDEN)
        referral = get_object_or_404(Referral, pk=pk)
        referral = confirm_paid_referral(referral)
        return Response(ReferralSerializer(referral).data)
