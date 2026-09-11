from django.urls import path

from pricing.views import AdminView, ApplyView, DraftView, ImportView, OperationsView, PreviewView

urlpatterns = [
    path('admin/<str:resource>/',AdminView.as_view(),name='pricing-admin'),
    path('preview/',PreviewView.as_view(),name='pricing-preview'),
    path('operations/',OperationsView.as_view(),name='pricing-operations'),
    path('operations/<uuid:operation_id>/apply/',ApplyView.as_view(),name='pricing-apply'),
    path('drafts/',DraftView.as_view(),name='pricing-draft'),
    path('import/',ImportView.as_view(),name='pricing-import'),
]
