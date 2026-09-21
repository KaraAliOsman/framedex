from django.urls import path

from billing.views import WalletView, BillingView, FlowConfirmationView, FlowRegistrationView, FlowRefundView

urlpatterns = [path('wallet/', WalletView.as_view()), path('', BillingView.as_view()),
               path('flow/confirm/<uuid:order_id>/', FlowConfirmationView.as_view()),
               path('flow/refund/<uuid:operation_id>/', FlowRefundView.as_view()),
               path('flow/register/<uuid:operation_id>/', FlowRegistrationView.as_view())]
