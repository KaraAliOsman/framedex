from django.urls import path

from analytics.views import OperationalSummaryView

urlpatterns = [
    path("summary/", OperationalSummaryView.as_view(), name="analytics-summary"),
]
