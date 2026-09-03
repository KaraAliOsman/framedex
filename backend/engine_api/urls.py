from django.urls import URLPattern, path

from engine_api.views import EngineCalculateView

urlpatterns: list[URLPattern] = [
    path("calculate/", EngineCalculateView.as_view(), name="engine-calculate"),
]
