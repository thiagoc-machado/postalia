from __future__ import annotations

from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.rates import BillingThrottle

from .serializers import BillingCheckoutSerializer, BillingPortalSerializer, BillingSubscriptionSerializer
from .services import billing_service, subscription_snapshot


class BillingCheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [BillingThrottle]

    def post(self, request):
        if not settings.CREEM_ENABLED:
            return Response({"detail": "Payments are not enabled yet."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        serializer = BillingCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            checkout_url = billing_service().create_checkout(request.user, serializer.validated_data["plan_code"])
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"checkout_url": checkout_url})


class MyBillingSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(BillingSubscriptionSerializer(subscription_snapshot(request.user)).data)


class BillingPortalView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [BillingThrottle]

    def post(self, request):
        if not settings.CREEM_ENABLED:
            return Response({"portal_url": None, "detail": "Payments are not enabled yet."})
        portal_url = billing_service().create_portal(request.user)
        if not portal_url:
            return Response(
                {"portal_url": None, "detail": "Billing portal is not available until a Creem customer is linked."}
            )
        return Response(BillingPortalSerializer({"portal_url": portal_url}).data)


class CreemWebhookView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        signature = request.headers.get("creem-signature")
        timestamp = request.headers.get("creem-timestamp") or request.headers.get("x-creem-timestamp")
        try:
            event, action = billing_service().process_webhook(request.body, signature, timestamp)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "status": action,
                "event_id": event.external_event_id,
                "event_type": event.event_type,
            }
        )
