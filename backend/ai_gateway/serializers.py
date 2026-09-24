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


class AiAskRequestSerializer(serializers.Serializer):
    surface = serializers.CharField(min_length=2, max_length=40)
    refs = serializers.DictField(required=False)
    question = serializers.CharField(min_length=1, max_length=2000)
    operation_key = serializers.CharField(min_length=8, max_length=120)

    def validate_refs(self, value):
        # Refs are identifiers only — the server resolves them into the typed
        # context itself. Anything else (a nested blob, a payload-shaped
        # object) is not an identity and is refused.
        for key, item in value.items():
            if not isinstance(key, str) or not isinstance(item, (str, int)) or isinstance(item, bool):
                raise serializers.ValidationError(
                    "Las referencias de contexto deben ser identificadores simples."
                )
        return value


class AiAskActionSerializer(serializers.Serializer):
    kind = serializers.CharField()
    path = serializers.CharField()
    label = serializers.CharField()


class AiAskResponseSerializer(serializers.Serializer):
    audit_id = serializers.CharField()
    model = serializers.CharField()
    credits_debited = serializers.IntegerField()
    answer = serializers.CharField()
    actions = AiAskActionSerializer(many=True)
    warnings = serializers.ListField(child=serializers.CharField())


class _RefsDictField(serializers.DictField):
    """Identity refs are name → identifier only — anything payload-shaped is
    not an identity and is refused, mirroring the ask contract."""

    def run_validation(self, data=serializers.empty):
        value = super().run_validation(data)
        for key, item in value.items():
            if not isinstance(key, str) or not isinstance(item, (str, int)) or isinstance(item, bool):
                raise serializers.ValidationError(
                    "Las referencias de contexto deben ser identificadores simples."
                )
        return value


class AiAgentHistorySerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["user", "agent"])
    content = serializers.CharField(min_length=1, max_length=2000)


class AiAgentRequestSerializer(serializers.Serializer):
    surface = serializers.CharField(min_length=2, max_length=40)
    refs = _RefsDictField(required=False)
    goal = serializers.CharField(min_length=1, max_length=2000)
    product = serializers.DictField(required=False)
    history = AiAgentHistorySerializer(many=True, required=False, max_length=6)
    operation_key = serializers.CharField(min_length=8, max_length=120)


class AiAgentStepSerializer(serializers.Serializer):
    kind = serializers.CharField()
    label = serializers.CharField()
    path = serializers.CharField(required=False)
    action = serializers.CharField(required=False)
    ops = serializers.ListField(child=serializers.DictField(), required=False)


class AiAgentQuerySerializer(serializers.Serializer):
    surface = serializers.CharField()
    status = serializers.CharField()


class AiAgentRejectedSerializer(serializers.Serializer):
    op = serializers.CharField(allow_null=True)
    reason = serializers.CharField()


class AiAgentResponseSerializer(serializers.Serializer):
    audit_id = serializers.CharField()
    model = serializers.CharField()
    credits_debited = serializers.IntegerField()
    reply = serializers.CharField()
    steps = AiAgentStepSerializer(many=True)
    queries = AiAgentQuerySerializer(many=True)
    warnings = serializers.ListField(child=serializers.CharField())
    rejected = AiAgentRejectedSerializer(many=True)
