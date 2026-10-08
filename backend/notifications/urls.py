from django.urls import path

from notifications.views import (
    MailExamplesView,
    MailIntegrationView,
    MailListView,
    MailRecoverView,
    PaymentMailView,
    QuoteMailView,
)

urlpatterns = [
    path("organization/mail/", MailIntegrationView.as_view()),
    path("mail/", MailListView.as_view()),
    path("mail/<uuid:mail_id>/recover/", MailRecoverView.as_view()),
    path("dev/mail/", MailExamplesView.as_view()),
    path("projects/<uuid:project_id>/quote-mail/", QuoteMailView.as_view()),
    path("projects/<uuid:project_id>/payments/<uuid:payment_id>/mail/", PaymentMailView.as_view()),
]
