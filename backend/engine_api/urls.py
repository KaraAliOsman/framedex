from django.urls import URLPattern, path

from engine_api.views import EngineCalculateView, EngineSystemsView
from engine_api.derivative_views import EngineInspectView, EngineOptimizeView

urlpatterns: list[URLPattern] = [
    path("systems/", EngineSystemsView.as_view(), name="engine-systems"),
    path("calculate/", EngineCalculateView.as_view(), name="engine-calculate"),
    path("inspect/", EngineInspectView.as_view(), name="engine-inspect"),
    path("optimize-cut/", EngineOptimizeView.as_view(), name="engine-optimize-cut"),
]
