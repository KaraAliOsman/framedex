from django.urls import URLPattern, path

from engine_api.views import (
    EngineAssemblyCalculateView,
    EngineCalculateView,
    EngineSystemsView,
    EngineLayoutView,
)
from engine_api.derivative_views import EngineInspectView, EngineOptimizeView

urlpatterns: list[URLPattern] = [
    path("systems/", EngineSystemsView.as_view(), name="engine-systems"),
    path("calculate/", EngineCalculateView.as_view(), name="engine-calculate"),
    path(
        "assembly/calculate/",
        EngineAssemblyCalculateView.as_view(),
        name="engine-assembly-calculate",
    ),
    path("layout/", EngineLayoutView.as_view(), name="engine-layout"),
    path("inspect/", EngineInspectView.as_view(), name="engine-inspect"),
    path("optimize-cut/", EngineOptimizeView.as_view(), name="engine-optimize-cut"),
]
