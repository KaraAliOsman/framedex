from django.urls import path

from ai_gateway.views import AiAgentView, AiAskView, AiInvokeView

urlpatterns = [
    path("invoke/", AiInvokeView.as_view(), name="ai-invoke"),
    path("ask/", AiAskView.as_view(), name="ai-ask"),
    path("agent/", AiAgentView.as_view(), name="ai-agent"),
]
