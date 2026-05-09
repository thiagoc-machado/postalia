from django.urls import path

from .views import ApplyReferralView, ConfirmPaidReferralView, MyReferralsView

urlpatterns = [
    path("referrals/me/", MyReferralsView.as_view(), name="my-referrals"),
    path("referrals/apply/", ApplyReferralView.as_view(), name="apply-referral"),
    path("staff/referrals/<int:pk>/confirm-paid/", ConfirmPaidReferralView.as_view(), name="confirm-paid-referral"),
]
