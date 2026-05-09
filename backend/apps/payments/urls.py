from django.urls import path

from .views import BillingCheckoutView, BillingPortalView, CreemWebhookView, MyBillingSubscriptionView

urlpatterns = [
    path("billing/checkout/", BillingCheckoutView.as_view(), name="billing-checkout"),
    path("billing/subscription/", MyBillingSubscriptionView.as_view(), name="billing-subscription"),
    path("billing/portal/", BillingPortalView.as_view(), name="billing-portal"),
    path("webhooks/creem/", CreemWebhookView.as_view(), name="creem-webhook"),
]
