"""Multipart mappings and explicit previews for supplier prices."""

from rest_framework import serializers

from pricing.serializers import StrictSerializer, ImportRequestSerializer


class SupplierFileSerializer(StrictSerializer):
    file = serializers.FileField()


class SupplierReviewSerializer(ImportRequestSerializer):
    reason = serializers.CharField(max_length=700)
    review_token = serializers.CharField(required=False, max_length=10000)


class SupplierInspectionSerializer(serializers.Serializer):
    sheet = serializers.CharField()
    columns = serializers.ListField(child=serializers.CharField(allow_blank=True))
    suggested_mapping = serializers.DictField(child=serializers.CharField(allow_blank=True))
    preview = serializers.ListField(child=serializers.ListField(child=serializers.CharField(allow_blank=True)))
    total = serializers.IntegerField()


class SupplierPriceSerializer(serializers.Serializer):
    sku = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    unit = serializers.CharField()
    unit_cost = serializers.CharField()
    origin = serializers.ChoiceField(choices=["WORKSHOP"])


class SupplierPreviewSerializer(serializers.Serializer):
    items = SupplierPriceSerializer(many=True)
    total = serializers.IntegerField()
    applied = serializers.BooleanField()
    review_token = serializers.CharField(allow_null=True)
