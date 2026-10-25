"""Project and position routes."""

from django.urls import path
from projects.thermal_views import ProjectThermalView, ThermalAlternativesView

from projects.views import (
    ClientView,
    ClientsView,
    FlowPaymentConfirmView,
    OrganizationBrandingLogoView,
    OrganizationBrandingView,
    ProjectCloneView,
    ProjectPaymentIntegrationView,
    ProjectPaymentLinkRecoverView,
    ProjectPaymentLinksView,
    ProjectCreditNoteAccessView,
    ProjectCreditNoteDteEnvioView,
    ProjectCreditNoteDteView,
    ProjectCreditNotesView,
    ProjectInvoiceAccessView,
    ProjectInvoiceDteView,
    ProjectInvoicesView,
    ProjectPaymentReceiptView,
    ProjectPaymentsView,
    ProjectPaymentView,
    ProjectPositionsView,
    ProjectSuccessorView,
    ProjectResetPricingView,
    ProjectView,
    ProjectsView,
    PositionDesignAlternativesView,
    PositionDesignAssistView,
    PositionView,
    SiiCafsView,
    SiiCertificateView,
    ProjectInvoiceDteEnvioView,
)
from projects.options import DesignOptionsView
from projects.company_views import CompanyView,CompanyUsersView,CompanyUserView,CompanyInvitationsView,CompanyInvitationView,InvitationInspectView,InvitationAcceptView,WorkshopCreateView,CompanyNumberingView,CompanyPreviewView,CompanyDesignDefaultsView,CompanySiteMeasurementView,FinishReferencesView,FinishReferenceView,FinishReferenceImageView,ProjectMaterialsView,ProjectCutDraftView
from projects.client_views import ClientDirectoryView, ClientDossierView, ClientNotesView, ClientMergePreviewView, ClientMergeView
from projects.ops_registry import OperationsRegistryView, SimulateOpsView
from projects.project_ops import ProjectOpsPreviewView, ProjectOpsApplyView, ProjectOpsUndoView, ProjectOpsStateView
from projects.hardware import HardwarePreviewView
from projects.finishes import FinishPreviewView
from projects.extras import ExtraPolicyView, ProjectServicesView, ExtrasPreviewView
from projects.mounting import MountingRulesView, MountingPreviewView, MeasurementConfirmView, RectificationView
from projects.collection_views import CollectionSettingsView, FlowSimulationView, FiscalSimulationView, CollectionReminderView, CollectionReminderSendView
from projects.works import WorksView

urlpatterns = [
    path("projects/works/", WorksView.as_view()),
    path("projects/<uuid:project_id>/thermal/", ProjectThermalView.as_view()),
    path("projects/<uuid:project_id>/thermal/<uuid:position_id>/alternatives/", ThermalAlternativesView.as_view()),
    path("organization/company/",CompanyView.as_view()),
    path("organization/users/",CompanyUsersView.as_view()),
    path("organization/users/<uuid:identity>/",CompanyUserView.as_view()),
    path("organization/invitations/",CompanyInvitationsView.as_view()),
    path("organization/invitations/<uuid:identity>/",CompanyInvitationView.as_view()),
    path("auth/invitation/",InvitationInspectView.as_view()),
    path("auth/invitation/accept/",InvitationAcceptView.as_view()),
    path("auth/workshop/",WorkshopCreateView.as_view()),
    path("organization/numbering/",CompanyNumberingView.as_view()),
    path("projects/<uuid:project_id>/materials/", ProjectMaterialsView.as_view(), name="project-materials"),
    path("projects/<uuid:project_id>/cut-draft/", ProjectCutDraftView.as_view(), name="project-cut-draft"),
    path("organization/design-defaults/",CompanyDesignDefaultsView.as_view()),
    path("organization/site-measurement/",CompanySiteMeasurementView.as_view()),
    path("organization/finish-references/",FinishReferencesView.as_view()),
    path("organization/finish-references/<uuid:reference_id>/",FinishReferenceView.as_view()),
    path("organization/finish-references/<uuid:reference_id>/image/",FinishReferenceImageView.as_view()),
    path("organization/document-preview/",CompanyPreviewView.as_view()),
    path("clients/directory/", ClientDirectoryView.as_view()),
    path("clients/<uuid:client_id>/dossier/", ClientDossierView.as_view()),
    path("clients/<uuid:client_id>/notes/", ClientNotesView.as_view()),
    path("clients/<uuid:client_id>/merge-preview/", ClientMergePreviewView.as_view()),
    path("clients/<uuid:client_id>/merge/", ClientMergeView.as_view()),
    path("organization/collections/", CollectionSettingsView.as_view()),
    path("projects/<uuid:project_id>/collection-reminder/", CollectionReminderView.as_view()),
    path("projects/<uuid:project_id>/collection-reminder/send/", CollectionReminderSendView.as_view()),
    path("projects/flow/simulated/<uuid:link_id>/", FlowSimulationView.as_view()),
    path("projects/<uuid:project_id>/fiscal-simulations/", FiscalSimulationView.as_view()),
    path("projects/<uuid:project_id>/operations/state/", ProjectOpsStateView.as_view()),
    path("projects/<uuid:project_id>/operations/preview/", ProjectOpsPreviewView.as_view()),
    path("projects/<uuid:project_id>/operations/apply/", ProjectOpsApplyView.as_view()),
    path("projects/<uuid:project_id>/operations/<uuid:operation_id>/undo/", ProjectOpsUndoView.as_view()),
    path("projects/operations/registry/", OperationsRegistryView.as_view()),
    path("projects/operations/simulate/", SimulateOpsView.as_view()),
    path('organization/mounting/<uuid:system_id>/', MountingRulesView.as_view()),
    path('projects/mounting-preview/', MountingPreviewView.as_view()),
    path('positions/<uuid:position_id>/measurements/confirm/', MeasurementConfirmView.as_view()),
    path('positions/<uuid:position_id>/measurements/rectify/', RectificationView.as_view()),
    path("organization/extras/", ExtraPolicyView.as_view()),
    path("projects/extras-preview/", ExtrasPreviewView.as_view()),
    path("projects/<uuid:project_id>/services/", ProjectServicesView.as_view()),
    path("projects/finish-preview/", FinishPreviewView.as_view()),
    path("projects/hardware-preview/", HardwarePreviewView.as_view()),
    path("projects/design-options/<uuid:system_id>/", DesignOptionsView.as_view()),
    path("projects/flow/confirm/<uuid:link_id>/", FlowPaymentConfirmView.as_view()),
    path("organization/branding/", OrganizationBrandingView.as_view()),
    path("organization/branding/logo/", OrganizationBrandingLogoView.as_view()),
    path("projects/payment-integration/", ProjectPaymentIntegrationView.as_view()),
    path("clients/", ClientsView.as_view()),
    path("clients/<uuid:client_id>/", ClientView.as_view()),
    path("projects/", ProjectsView.as_view()),
    path("projects/<uuid:project_id>/", ProjectView.as_view()),
    path("projects/<uuid:project_id>/clone/", ProjectCloneView.as_view()),
    path("projects/<uuid:project_id>/successor/", ProjectSuccessorView.as_view()),
    path("projects/<uuid:project_id>/reset-pricing/", ProjectResetPricingView.as_view()),
    path("projects/<uuid:project_id>/positions/", ProjectPositionsView.as_view()),
    path("projects/<uuid:project_id>/payments/", ProjectPaymentsView.as_view()),
    path(
        "projects/<uuid:project_id>/payments/<uuid:payment_id>/",
        ProjectPaymentView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/payments/<uuid:payment_id>/receipt/",
        ProjectPaymentReceiptView.as_view(),
    ),
    path("projects/<uuid:project_id>/invoices/", ProjectInvoicesView.as_view()),
    path(
        "projects/<uuid:project_id>/invoices/<uuid:invoice_id>/",
        ProjectInvoiceAccessView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/invoices/<uuid:invoice_id>/credit-note/",
        ProjectCreditNotesView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/invoices/<uuid:invoice_id>/dte/",
        ProjectInvoiceDteView.as_view(),
    ),
    path("sii/cafs/", SiiCafsView.as_view()),
    path("sii/certificate/", SiiCertificateView.as_view()),
    path(
        "projects/<uuid:project_id>/invoices/<uuid:invoice_id>/dte-envio/",
        ProjectInvoiceDteEnvioView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/credit-notes/<uuid:credit_note_id>/",
        ProjectCreditNoteAccessView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/invoices/<uuid:invoice_id>/credit-note-dte/",
        ProjectCreditNoteDteView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/credit-notes/<uuid:credit_note_id>/dte-envio/",
        ProjectCreditNoteDteEnvioView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/payment-links/",
        ProjectPaymentLinksView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/payment-links/<uuid:link_id>/recover/",
        ProjectPaymentLinkRecoverView.as_view(),
    ),
    path("positions/<uuid:position_id>/", PositionView.as_view()),
    path(
        "positions/<uuid:position_id>/design-assist/",
        PositionDesignAssistView.as_view(),
    ),
    path(
        "positions/<uuid:position_id>/design-alternatives/",
        PositionDesignAlternativesView.as_view(),
    ),
]
