from django.urls import path

from portal.views import PortalQuoteDecisionView, PortalQuoteView, ProjectQuoteLinkView

urlpatterns = [
    path(
        "projects/<uuid:project_id>/quote-link/",
        ProjectQuoteLinkView.as_view(),
        name="project-quote-link",
    ),
    path("portal/quotes/<str:token>/", PortalQuoteView.as_view(), name="portal-quote"),
    path(
        "portal/quotes/<str:token>/decide/",
        PortalQuoteDecisionView.as_view(),
        name="portal-quote-decide",
    ),
]
