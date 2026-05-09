from __future__ import annotations

from rest_framework import permissions
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.brands.models import Brand
from apps.common.mixins import IsStaff
from apps.generations.models import GenerationRequest
from apps.risk.models import RiskEvent
from apps.subscriptions.models import SubscriptionPlan

from .serializers import StaffGenerationSerializer, StaffPlanSerializer, StaffRiskEventSerializer, StaffUserSerializer


class StaffSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsStaff]

    def get(self, request):
        data = {
            "users": User.objects.count(),
            "brands": Brand.objects.count(),
            "generations": GenerationRequest.objects.count(),
            "risk_events": RiskEvent.objects.count(),
        }
        return Response(data)


class StaffUserListView(ListAPIView):
    queryset = User.objects.select_related("subscription", "wallet")
    serializer_class = StaffUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaff]


class StaffPlanListView(ListAPIView):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = StaffPlanSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaff]


class StaffRiskEventListView(ListAPIView):
    queryset = RiskEvent.objects.select_related("user")
    serializer_class = StaffRiskEventSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaff]


class StaffGenerationListView(ListAPIView):
    queryset = GenerationRequest.objects.select_related("user", "brand", "template")
    serializer_class = StaffGenerationSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaff]
