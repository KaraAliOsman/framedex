from django.urls import path

from ai_gateway.views import AiInvokeView

urlpatterns = [
    path("invoke/", AiInvokeView.as_view(), name="ai-invoke"),
]
