from django.urls import path

from pricing.views import (AdminView, ApplyView, DesignBatchPreviewView, DraftView, ImportView, OperationView,
                           OperationsView, PreviewView, WithdrawView, WorkspaceView, OptionsView, AcknowledgeView)

urlpatterns = [
    path('admin/<str:resource>/',AdminView.as_view(),name='pricing-admin'),
    path('preview/',PreviewView.as_view(),name='pricing-preview'),
    path('workspace/',WorkspaceView.as_view(),name='pricing-workspace'),
    path('options/',OptionsView.as_view(),name='pricing-options'),
    path('acknowledge/',AcknowledgeView.as_view(),name='pricing-acknowledge'),
    path('design-batch-preview/',DesignBatchPreviewView.as_view(),name='pricing-design-batch-preview'),
    path('operations/',OperationsView.as_view(),name='pricing-operations'),
    path('operations/<uuid:operation_id>/',OperationView.as_view(),name='pricing-operation'),
    path('operations/<uuid:operation_id>/apply/',ApplyView.as_view(),name='pricing-apply'),
    path('operations/<uuid:operation_id>/withdraw/',WithdrawView.as_view(),name='pricing-withdraw'),
    path('drafts/',DraftView.as_view(),name='pricing-draft'),
    path('import/',ImportView.as_view(),name='pricing-import'),
]
