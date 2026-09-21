"""Canonical SHOT-04 API routes."""

from django.urls import URLPattern, URLResolver, include, path
from drf_spectacular.views import SpectacularAPIView
from config.health import live, ready

urlpatterns: list[URLPattern | URLResolver] = [
    path('api/v1/billing/', include('billing.urls')),
    path('health/live/', live),
    path('health/ready/', ready),
    path("api/v1/catalogs/", include("catalogs.urls")),
    path("api/v1/", include("projects.urls")),
    path("api/v1/documents/", include("documents.urls")),
    path("api/v1/purchasing/", include("purchasing.urls")),
    path("api/v1/pricing/", include("pricing.urls")),
    path("api/v1/auth/", include("authentication.urls")),
    path("api/v1/engine/", include("engine_api.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="openapi-schema"),
]
