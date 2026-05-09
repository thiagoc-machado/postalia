from django.urls import path

from .views import StaffGenerationListView, StaffPlanListView, StaffRiskEventListView, StaffSummaryView, StaffUserListView

urlpatterns = [
    path("staff/summary/", StaffSummaryView.as_view(), name="staff-summary"),
    path("staff/users/", StaffUserListView.as_view(), name="staff-users"),
    path("staff/plans/", StaffPlanListView.as_view(), name="staff-plans"),
    path("staff/risk-events/", StaffRiskEventListView.as_view(), name="staff-risk-events"),
    path("staff/generations/", StaffGenerationListView.as_view(), name="staff-generations"),
]
