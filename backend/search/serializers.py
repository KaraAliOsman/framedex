from __future__ import annotations

from rest_framework import serializers


class SearchResultSerializer(serializers.Serializer):
    group = serializers.CharField()
    id = serializers.CharField()
    title = serializers.CharField()
    subtitle = serializers.CharField(allow_null=True, required=False)
    path = serializers.CharField()


class SearchResponseSerializer(serializers.Serializer):
    results = SearchResultSerializer(many=True)
