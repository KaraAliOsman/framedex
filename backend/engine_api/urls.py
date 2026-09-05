from django.urls import URLPattern, path

from engine_api.views import EngineCalculateView, EngineSystemsView

urlpatterns: list[URLPattern] = [
    path("systems/", EngineSystemsView.as_view(), name="engine-systems"),
    path("calculate/", EngineCalculateView.as_view(), name="engine-calculate"),
]
