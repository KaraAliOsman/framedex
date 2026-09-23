from django.urls import path

from production.views import (
    ProductionOrderDetailView,
    ProductionOrderListView,
    ProductionOrderOptimizeView,
    ProductionOrderRemakeView,
    ProductionReleaseView,
    ProductionStepTransitionView,
    WorkCenterListView,
)

urlpatterns = [
    path("orders/", ProductionOrderListView.as_view(), name="production-orders"),
    path(
        "orders/<uuid:order_id>/",
        ProductionOrderDetailView.as_view(),
        name="production-order-detail",
    ),
    path(
        "orders/<uuid:order_id>/optimize/",
        ProductionOrderOptimizeView.as_view(),
        name="production-order-optimize",
    ),
    path(
        "orders/<uuid:order_id>/remake/",
        ProductionOrderRemakeView.as_view(),
        name="production-order-remake",
    ),
    path(
        "steps/<uuid:step_id>/transition/",
        ProductionStepTransitionView.as_view(),
        name="production-step-transition",
    ),
    path(
        "versions/<uuid:version_id>/release/",
        ProductionReleaseView.as_view(),
        name="production-release",
    ),
    path("work-centers/", WorkCenterListView.as_view(), name="production-work-centers"),
]
