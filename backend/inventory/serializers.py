"""OpenAPI-visible contracts for the inventory API."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - set(self.fields):
            raise serializers.ValidationError("Unknown input fields")
        return super().to_internal_value(data)


class InventoryStockItemSerializer(serializers.Serializer):
    item_id = serializers.UUIDField()
    sku = serializers.CharField()
    name = serializers.CharField()
    category = serializers.CharField()
    unit = serializers.CharField()
    variant_key = serializers.CharField()
    on_hand_qty = serializers.DecimalField(max_digits=14, decimal_places=2)
    reserved_qty = serializers.DecimalField(max_digits=14, decimal_places=2)
    available_qty = serializers.DecimalField(max_digits=14, decimal_places=2)


class InventoryStockSerializer(serializers.Serializer):
    items = InventoryStockItemSerializer(many=True)


class InventoryMovementSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    item_id = serializers.UUIDField()
    movement_type = serializers.ChoiceField(
        choices=(
            "RECEIPT",
            "RESERVATION",
            "RELEASE",
            "CONSUMPTION",
            "ADJUSTMENT",
            "RETURN",
            "SCRAP",
        )
    )
    quantity = serializers.DecimalField(max_digits=14, decimal_places=2)
    order_id = serializers.UUIDField(allow_null=True)
    order_line_id = serializers.UUIDField(allow_null=True)
    lot_code = serializers.CharField(allow_null=True)
    note = serializers.CharField(allow_null=True)
    actor_id = serializers.UUIDField(allow_null=True)
    created_at = serializers.DateTimeField()


class InventoryMovementsSerializer(serializers.Serializer):
    movements = InventoryMovementSerializer(many=True)


class MovementListQuerySerializer(StrictSerializer):
    item_id = serializers.UUIDField(required=False)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=200, default=50)


class ReceiptLineRequestSerializer(StrictSerializer):
    order_line_id = serializers.UUIDField()
    received_qty = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0"))
    damaged_qty = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal("0"), default=0
    )
    lot_code = serializers.CharField(required=False, allow_null=True, max_length=100)
    rack_location = serializers.CharField(required=False, allow_null=True, max_length=50)
    note = serializers.CharField(required=False, allow_null=True, max_length=500)


class OrderReceiptRequestSerializer(StrictSerializer):
    receipt_key = serializers.CharField(max_length=100)
    note = serializers.CharField(required=False, allow_null=True, max_length=500)
    lines = ReceiptLineRequestSerializer(many=True, allow_empty=False)


class OrderReceivingLineSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    ordered_qty = serializers.DecimalField(max_digits=14, decimal_places=2)
    received_qty = serializers.DecimalField(max_digits=14, decimal_places=2)
    damaged_qty = serializers.DecimalField(max_digits=14, decimal_places=2)
    outstanding_qty = serializers.DecimalField(max_digits=14, decimal_places=2)
    purchasing_sku = serializers.CharField(allow_null=True)
    category = serializers.CharField(allow_null=True)
    unit = serializers.CharField(allow_null=True)
    physical_stock_identity = serializers.CharField(allow_null=True)
    specification = serializers.JSONField(allow_null=True)


class OrderReceiptSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    receipt_key = serializers.CharField()
    note = serializers.CharField(allow_null=True)
    received_by = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()


class OrderReceivingSerializer(serializers.Serializer):
    order = serializers.JSONField()
    lines = OrderReceivingLineSerializer(many=True)
    receipts = OrderReceiptSerializer(many=True)


class InventoryMovementRequestSerializer(StrictSerializer):
    item_id = serializers.UUIDField()
    movement_type = serializers.ChoiceField(choices=("ADJUSTMENT", "RETURN", "SCRAP"))
    quantity = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0"))
    lot_code = serializers.CharField(required=False, allow_null=True, max_length=100)
    note = serializers.CharField(max_length=500)
