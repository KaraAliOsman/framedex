from django.urls import path

from analytics.views import OperationalSummaryView, QuotationsView, TodayView
from analytics.decision_views import (
    AnalyticsWorkspaceView,
    AnalyticsCsvView,
    AnalyticsPreferencesView,
    ActualReportView,
    ActualReportPreviewView,
)

urlpatterns = [
    path("decision/", AnalyticsWorkspaceView.as_view(), name="analytics-decision"),
    path("decision/export/", AnalyticsCsvView.as_view(), name="analytics-decision-csv"),
    path("preferences/", AnalyticsPreferencesView.as_view(), name="analytics-preferences"),
    path("orders/<uuid:order_id>/actual/", ActualReportView.as_view(), name="analytics-actual"),
    path(
        "orders/<uuid:order_id>/actual/preview/",
        ActualReportPreviewView.as_view(),
        name="analytics-actual-preview",
    ),
    path("summary/", OperationalSummaryView.as_view(), name="analytics-summary"),
    path("today/", TodayView.as_view(), name="analytics-today"),
    path("quotations/", QuotationsView.as_view(), name="analytics-quotations"),
]
