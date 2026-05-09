from django.urls import path

from .views import RewardedAdCompleteView, RewardedAdStatusView

urlpatterns = [
    path("rewards/ads/status/", RewardedAdStatusView.as_view(), name="rewarded-ad-status"),
    path("rewards/ads/complete/", RewardedAdCompleteView.as_view(), name="rewarded-ad-complete"),
    path("ads/rewarded/complete/", RewardedAdCompleteView.as_view(), name="rewarded-ad-complete-legacy"),
]
