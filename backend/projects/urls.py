"""Project and position routes."""

from django.urls import path

from projects.views import (
    ProjectCloneView,
    ProjectPositionsView,
    ProjectSuccessorView,
    ProjectResetPricingView,
    ProjectView,
    ProjectsView,
    PositionView,
)
from projects.options import DesignOptionsView

urlpatterns = [
    path("projects/design-options/<uuid:system_id>/", DesignOptionsView.as_view()),
    path("projects/", ProjectsView.as_view()),
    path("projects/<uuid:project_id>/", ProjectView.as_view()),
    path("projects/<uuid:project_id>/clone/", ProjectCloneView.as_view()),
    path("projects/<uuid:project_id>/successor/", ProjectSuccessorView.as_view()),
    path("projects/<uuid:project_id>/reset-pricing/", ProjectResetPricingView.as_view()),
    path("projects/<uuid:project_id>/positions/", ProjectPositionsView.as_view()),
    path("positions/<uuid:position_id>/", PositionView.as_view()),
]
