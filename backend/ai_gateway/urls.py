from django.urls import path

from ai_gateway.views import (
    AiAgentView,
    AiAskView,
    AiInvokeView,
    AiJobCollectionView,
    AiJobMessagesView,
    AiJobView,
)

urlpatterns = [
    path("invoke/", AiInvokeView.as_view(), name="ai-invoke"),
    path("ask/", AiAskView.as_view(), name="ai-ask"),
    path("agent/", AiAgentView.as_view(), name="ai-agent"),
    path("jobs/", AiJobCollectionView.as_view(), name="ai-jobs"),
    path("jobs/<uuid:job_id>/", AiJobView.as_view(), name="ai-job"),
    path(
        "jobs/<uuid:job_id>/messages/",
        AiJobMessagesView.as_view(),
        name="ai-job-messages",
    ),
]
