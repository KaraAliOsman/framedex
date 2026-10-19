from django.urls import path
from documents.issuance_views import (
    QuotationCustomerView,
    QuotationDraftPreviewView,
    QuotationIssueView,
    QuotationLayoutView,
    QuotationNumberingView,
    QuotationPreviewAccessView,
    QuotationPreviewView,
    QuickDraftView,
)

from documents.views import (
    ArtifactAccessView,
    ArtifactGenerateView,
    ArtifactListView,
    DocumentaryInputsView,
    FreezeRevisionView,
    RevisionCompareView,
)

urlpatterns = [
    path("projects/<uuid:project_id>/quotation-customer/", QuotationCustomerView.as_view(), name="quotation-customer"),
    path("projects/<uuid:project_id>/quotation-preview/", QuotationPreviewView.as_view(), name="quotation-preview"),
    path("projects/<uuid:project_id>/quotation-previews/<uuid:preview_id>/", QuotationPreviewAccessView.as_view(), name="quotation-preview-access"),
    path("projects/<uuid:project_id>/issue/", QuotationIssueView.as_view(), name="quotation-issue"),
    path("projects/<uuid:project_id>/quotation-layout/", QuotationLayoutView.as_view(), name="quotation-layout"),
    path("projects/<uuid:project_id>/quotation-draft/", QuotationDraftPreviewView.as_view(), name="quotation-draft"),
    path("projects/<uuid:project_id>/quick-draft/", QuickDraftView.as_view(), name="quick-draft"),
    path("organization/quotation-numbering/", QuotationNumberingView.as_view(), name="quotation-numbering"),
    path("artifacts/", ArtifactGenerateView.as_view(), name="documentary-artifact-generate"),
    path(
        "artifacts/<uuid:artifact_id>/access/",
        ArtifactAccessView.as_view(),
        name="documentary-artifact-access",
    ),
    path(
        "projects/<uuid:project_id>/artifacts/",
        ArtifactListView.as_view(),
        name="documentary-artifact-list",
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
    path(
        "projects/<uuid:project_id>/versions/compare/",
        RevisionCompareView.as_view(),
        name="documentary-versions-compare",
    ),
]
