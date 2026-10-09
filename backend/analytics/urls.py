from django.urls import path

from analytics.views import OperationalSummaryView, QuotationsView, TodayView

urlpatterns = [
    path("summary/", OperationalSummaryView.as_view(), name="analytics-summary"),
    path("today/", TodayView.as_view(), name="analytics-today"),
    path("quotations/", QuotationsView.as_view(), name="analytics-quotations"),
]
