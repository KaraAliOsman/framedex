from django.urls import path

from inventory.views import (
    InventoryMovementsView,
    InventoryStockView,
    OrderReceiptCreateView,
    OrderReceivingView,
)

urlpatterns = [
    path("stock/", InventoryStockView.as_view(), name="inventory-stock"),
    path("movements/", InventoryMovementsView.as_view(), name="inventory-movements"),
    path(
        "orders/<uuid:order_id>/receiving/",
        OrderReceivingView.as_view(),
        name="inventory-order-receiving",
    ),
    path(
        "orders/<uuid:order_id>/receipts/",
        OrderReceiptCreateView.as_view(),
        name="inventory-order-receipts",
    ),
]
