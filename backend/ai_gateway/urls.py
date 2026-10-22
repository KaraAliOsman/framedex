from django.urls import path
from ai_gateway.operations_views import AiSettingsView, AiConnectionView, AiUsageView, AiModeView

from ai_gateway.copilot_views import (
    AiAttachmentCollectionView,
    AiAttachmentContentView,
    AiAttachmentView,
    AiJobApproveView,
    AiJobUndoAllView,
    AiThreadAttachmentsView,
    AiThreadCollectionView,
    AiThreadTimelineView,
    AiThreadView,
)
from ai_gateway.views import (
    AiAgentView,
    AiAskView,
    AiInvokeView,
    AiJobCollectionView,
    AiJobMessagesView,
    AiJobOutcomeView,
    AiJobRetryView,
    AiJobView,
    AiMetricsView,
    AiPresenceView,
)

urlpatterns = [
    path("mode/", AiModeView.as_view(), name="ai-test-mode"),
    path("settings/", AiSettingsView.as_view(), name="ai-settings"),
    path("connection-test/", AiConnectionView.as_view(), name="ai-connection-test"),
    path("usage/", AiUsageView.as_view(), name="ai-provider-usage"),
    path("invoke/", AiInvokeView.as_view(), name="ai-invoke"),
    path("ask/", AiAskView.as_view(), name="ai-ask"),
    path("agent/", AiAgentView.as_view(), name="ai-agent"),
    path("presence/", AiPresenceView.as_view(), name="ai-presence"),
    path("jobs/", AiJobCollectionView.as_view(), name="ai-jobs"),
    path("jobs/<uuid:job_id>/", AiJobView.as_view(), name="ai-job"),
    path(
        "jobs/<uuid:job_id>/messages/",
        AiJobMessagesView.as_view(),
        name="ai-job-messages",
    ),
    path(
        "jobs/<uuid:job_id>/retry/",
        AiJobRetryView.as_view(),
        name="ai-job-retry",
    ),
    path(
        "jobs/<uuid:job_id>/outcome/",
        AiJobOutcomeView.as_view(),
        name="ai-job-outcome",
    ),
    path("metrics/", AiMetricsView.as_view(), name="ai-metrics"),
    path("threads/", AiThreadCollectionView.as_view(), name="ai-threads"),
    path("threads/<uuid:thread_id>/", AiThreadView.as_view(), name="ai-thread"),
    path("threads/<uuid:thread_id>/timeline/", AiThreadTimelineView.as_view(), name="ai-thread-timeline"),
    path("threads/<uuid:thread_id>/attachments/", AiThreadAttachmentsView.as_view(), name="ai-thread-attachments"),
    path("attachments/", AiAttachmentCollectionView.as_view(), name="ai-attachments"),
    path("attachments/<uuid:attachment_id>/", AiAttachmentView.as_view(), name="ai-attachment"),
    path("attachments/<uuid:attachment_id>/content/", AiAttachmentContentView.as_view(), name="ai-attachment-content"),
    path("jobs/<uuid:job_id>/approve/", AiJobApproveView.as_view(), name="ai-job-approve"),
    path("jobs/<uuid:job_id>/undo-all/", AiJobUndoAllView.as_view(), name="ai-job-undo-all"),
]
