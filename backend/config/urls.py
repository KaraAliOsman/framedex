"""Canonical SHOT-04 API routes."""

from django.urls import URLPattern, URLResolver, include, path
from drf_spectacular.views import SpectacularAPIView

urlpatterns: list[URLPattern | URLResolver] = [
    path("api/v1/auth/", include("authentication.urls")),
    path("api/v1/engine/", include("engine_api.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="openapi-schema"),
]
