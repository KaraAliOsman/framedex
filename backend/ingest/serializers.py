"""Import contracts — strict serializers for the ingestion surface.

Response envelopes expose an `import` key — a Python keyword, so the parent
serializer classes are built via type() with the field declared by string."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from documents.serializers import StrictSerializer
from engine_api.serializers import DecimalStringField
from ingest.parser import _OPENING_TYPES


class ExtractPayloadSerializer(StrictSerializer):
    import_id = serializers.UUIDField()


class ImportUploadSerializer(StrictSerializer):
    file = serializers.FileField()


class ImportResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    file_name = serializers.CharField()
    kind = serializers.CharField()
    status = serializers.CharField()
    candidates = serializers.ListField(child=serializers.DictField())
    warnings = serializers.ListField(child=serializers.CharField())
    result = serializers.ListField(child=serializers.DictField())
    error_code = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


ImportDetailResponseSerializer = type(
    "ImportDetailResponseSerializer",
    (serializers.Serializer,),
    {"import": ImportResponseSerializer()},
)


class ImportListResponseSerializer(serializers.Serializer):
    imports = ImportResponseSerializer(many=True)


ImportCreateResponseSerializer = type(
    "ImportCreateResponseSerializer",
    (serializers.Serializer,),
    {
        "import": ImportResponseSerializer(),
        "job": serializers.DictField(),
    },
)


class ConfirmItemSerializer(StrictSerializer):
    key = serializers.CharField(max_length=40)
    label = serializers.CharField(max_length=100, allow_blank=True)
    width_mm = DecimalStringField(
        max_digits=10, decimal_places=2, min_value=Decimal("250")
    )
    height_mm = DecimalStringField(
        max_digits=10, decimal_places=2, min_value=Decimal("250")
    )
    quantity = serializers.IntegerField(min_value=1, max_value=999)
    opening_type = serializers.ChoiceField(choices=sorted(_OPENING_TYPES))
    system_id = serializers.UUIDField()
    color = serializers.ChoiceField(choices=["WHITE"])
    glass_thickness_mm = DecimalStringField(
        max_digits=10, decimal_places=2, min_value=Decimal("1")
    )
    glass_spec = serializers.CharField(max_length=120)


class ImportConfirmSerializer(StrictSerializer):
    items = ConfirmItemSerializer(many=True, min_length=1, max_length=200)


ImportConfirmResponseSerializer = type(
    "ImportConfirmResponseSerializer",
    (serializers.Serializer,),
    {
        "import": ImportResponseSerializer(),
        "created": serializers.ListField(child=serializers.DictField()),
        "errors": serializers.ListField(child=serializers.DictField()),
    },
)
