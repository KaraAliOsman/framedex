from django.urls import path

from jobs.views import JobDetailView, JobListCreateView

urlpatterns = [
    path("", JobListCreateView.as_view(), name="job-list-create"),
    path("<uuid:job_id>/", JobDetailView.as_view(), name="job-detail"),
]
