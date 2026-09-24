from django.urls import path

from ai_gateway.views import AiAskView, AiInvokeView

urlpatterns = [
    path("invoke/", AiInvokeView.as_view(), name="ai-invoke"),
    path("ask/", AiAskView.as_view(), name="ai-ask"),
]
