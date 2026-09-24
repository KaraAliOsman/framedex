import json

from rest_framework import serializers

MAX_INPUT_BYTES = 65_536


class AiInvokeRequestSerializer(serializers.Serializer):
    capability = serializers.CharField(min_length=2, max_length=100)
    tool_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    operation_key = serializers.CharField(min_length=8, max_length=120)
    input_payload = serializers.DictField()

    def validate_input_payload(self, value):
        # Measure the real UTF-8 wire size — ensure_ascii would count the
        # \uXXXX escapes and reject unicode-heavy payloads far below 64 KB.
        encoded = json.dumps(value, default=str, ensure_ascii=False).encode("utf-8")
        if len(encoded) > MAX_INPUT_BYTES:
            raise serializers.ValidationError(
                "input_payload excede el límite de 64 KB."
            )
        return value


class AiInvokeResponseSerializer(serializers.Serializer):
    audit_id = serializers.CharField()
    capability = serializers.CharField()
    model = serializers.CharField()
    output = serializers.CharField()
    tokens_prompt = serializers.IntegerField()
    tokens_completion = serializers.IntegerField()
    latency_ms = serializers.IntegerField()
    credits_debited = serializers.IntegerField()
