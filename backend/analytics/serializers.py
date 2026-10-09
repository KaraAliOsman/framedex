from rest_framework import serializers


class OperationalSummaryCommercialItemSerializer(serializers.Serializer):
    currency = serializers.CharField()
    quoted = serializers.CharField()
    booked = serializers.CharField()
    collected = serializers.CharField()


class OperationalSummarySerializer(serializers.Serializer):
    schema = serializers.CharField()
    work_orders = serializers.DictField()
    supplier_orders = serializers.DictField()
    throughput_30d = serializers.DictField()
    avg_release_to_dispatch_hours = serializers.FloatField(allow_null=True)
    inventory = serializers.DictField()
    prep = serializers.DictField()
    deliveries = serializers.DictField()
    documents = serializers.DictField()
    projects = serializers.DictField()
    commercial = OperationalSummaryCommercialItemSerializer(many=True)
    recent_events = serializers.ListField()


class TodayActionSerializer(serializers.Serializer):
    key = serializers.CharField()
    kind = serializers.CharField()
    entity_code = serializers.CharField()
    entity_name = serializers.CharField()
    title = serializers.CharField()
    reason = serializers.CharField(allow_blank=True)
    verb = serializers.CharField()
    href = serializers.CharField()
    due_on = serializers.DateField(allow_null=True)
    blocking = serializers.BooleanField()
    consequence = serializers.CharField()
    amount = serializers.CharField(allow_null=True)
    currency = serializers.CharField(allow_null=True)
    balance_total = serializers.CharField(allow_null=True)
    balance_collected = serializers.CharField(allow_null=True)
    source = serializers.CharField(allow_null=True)
    operation_id = serializers.UUIDField(allow_null=True)


class PipelinePhaseSerializer(serializers.Serializer):
    phase = serializers.CharField()
    currency = serializers.CharField(allow_null=True)
    amount = serializers.CharField(allow_null=True)
    count = serializers.IntegerField()
    unknown_count = serializers.IntegerField()
    href = serializers.CharField()
    source = serializers.CharField()


class TodayResponseSerializer(serializers.Serializer):
    today = serializers.DateField()
    actions = TodayActionSerializer(many=True)
    pipeline = PipelinePhaseSerializer(many=True)
    source = serializers.CharField()


class QuotationIndexItemSerializer(serializers.Serializer):
    project_id = serializers.UUIDField()
    project_code = serializers.CharField()
    project_name = serializers.CharField()
    client_name = serializers.CharField(allow_blank=True)
    revision_code = serializers.CharField()
    state = serializers.CharField()
    phase = serializers.CharField()
    valid_until = serializers.DateField(allow_null=True)
    view_count = serializers.IntegerField()
    last_viewed_at = serializers.DateTimeField(allow_null=True)
    response_note = serializers.CharField(allow_null=True)
    total = serializers.CharField(allow_null=True)
    currency = serializers.CharField(allow_null=True)
    source = serializers.CharField()
    href = serializers.CharField()


class QuotationIndexResponseSerializer(serializers.Serializer):
    items = QuotationIndexItemSerializer(many=True)
    total = serializers.IntegerField()
    offset = serializers.IntegerField()
    limit = serializers.IntegerField()
    today = serializers.DateField()


class QuotationIndexQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, max_length=80, default="")
    attention = serializers.ChoiceField(required=False, default="", choices=[
        "", "expiring", "viewed", "response", "expired", "unshared", "pending", "approved", "link_expired",
    ])
    offset = serializers.IntegerField(min_value=0, default=0)
    limit = serializers.IntegerField(min_value=1, max_value=200, default=50)
    phase = serializers.ChoiceField(required=False, default="", choices=[
        "", "QUOTED", "APPROVED", "IN_PRODUCTION", "COMPLETED",
    ])
    currency = serializers.ChoiceField(required=False, default="", choices=["", "CLP", "USD", "UF", "unknown"])
