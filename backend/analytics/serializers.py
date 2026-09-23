from rest_framework import serializers


class OperationalSummarySerializer(serializers.Serializer):
    schema = serializers.CharField()
    work_orders = serializers.DictField()
    supplier_orders = serializers.DictField()
    throughput_30d = serializers.DictField()
    avg_release_to_dispatch_hours = serializers.FloatField(allow_null=True)
    inventory = serializers.DictField()
    documents = serializers.DictField()
    projects = serializers.DictField()
    recent_events = serializers.ListField()
