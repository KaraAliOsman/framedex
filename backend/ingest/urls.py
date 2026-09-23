from django.urls import path

from ingest.views import (
    ProjectImportConfirmView,
    ProjectImportDetailView,
    ProjectImportsView,
)

urlpatterns = [
    path(
        "projects/<uuid:project_id>/imports/",
        ProjectImportsView.as_view(),
        name="project-imports",
    ),
    path(
        "projects/<uuid:project_id>/imports/<uuid:import_id>/",
        ProjectImportDetailView.as_view(),
        name="project-import-detail",
    ),
    path(
        "projects/<uuid:project_id>/imports/<uuid:import_id>/confirm/",
        ProjectImportConfirmView.as_view(),
        name="project-import-confirm",
    ),
]
