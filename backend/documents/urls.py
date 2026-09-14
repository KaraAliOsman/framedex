from django.urls import path

from documents.views import (
    ArtifactAccessView,
    ArtifactGenerateView,
    DocumentaryInputsView,
    FreezeRevisionView,
)

urlpatterns = [
    path("artifacts/", ArtifactGenerateView.as_view(), name="documentary-artifact-generate"),
    path(
        "artifacts/<uuid:artifact_id>/access/",
        ArtifactAccessView.as_view(),
        name="documentary-artifact-access",
    ),
    path(
        "projects/<uuid:project_id>/inputs/",
        DocumentaryInputsView.as_view(),
        name="documentary-inputs",
    ),
    path(
        "projects/<uuid:project_id>/freeze/",
        FreezeRevisionView.as_view(),
        name="documentary-freeze",
    ),
]
