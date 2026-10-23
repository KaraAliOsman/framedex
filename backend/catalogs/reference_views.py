"""Curated reference series of real manufacturers (dirección final 03).

A reference is knowledge with sources, not catalog authority: it never makes a
series quotable, manufacturable or CNC-ready. The registry is global and
versioned in the repository (`reference_series.json`); a company prepares its
own series from a reference through the manual catalog forms and review.
"""

import json
from functools import lru_cache
from pathlib import Path

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.serializers import ACTIVE_ORGANIZATION_HEADER, ErrorResponseSerializer
from catalogs.views import READ_ROLES, catalog_scope

REGISTRY = Path(__file__).with_name("reference_series.json")


@lru_cache(maxsize=1)
def registry() -> dict:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    for series in data["series"]:
        series["needs_manufacturer_manual"] = not series.get("facts") and not series.get("articles")
    return data


class ReferenceFactSerializer(serializers.Serializer):
    label = serializers.CharField()
    value = serializers.CharField()
    source = serializers.CharField()
    pages = serializers.CharField(allow_null=True, required=False)


class ReferenceArticleSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    role = serializers.CharField()
    source = serializers.CharField()
    pages = serializers.CharField(allow_null=True, required=False)


class ReferenceCapabilitiesSerializer(serializers.Serializer):
    reference = serializers.BooleanField()
    quotable = serializers.BooleanField()
    manufacturable = serializers.BooleanField()
    cnc = serializers.BooleanField()


class ReferenceSeriesSerializer(serializers.Serializer):
    id = serializers.CharField()
    manufacturer = serializers.CharField()
    series_code = serializers.CharField()
    series_name = serializers.CharField()
    material = serializers.CharField()
    family = serializers.CharField()
    uses = serializers.ListField(child=serializers.CharField())
    facts = ReferenceFactSerializer(many=True)
    articles = ReferenceArticleSerializer(many=True)
    sources = serializers.ListField(child=serializers.CharField())
    capabilities = ReferenceCapabilitiesSerializer()
    missing = serializers.ListField(child=serializers.CharField())
    incidents = serializers.ListField(child=serializers.CharField())
    # Verified identity values to prefill the manual series form (strings,
    # lexemes as written; never dimensions the source does not state).
    seed = serializers.DictField(child=serializers.CharField())
    # P10: no cited fact or article yet — the series exists only as a name
    # until the manufacturer's manual is incorporated.
    needs_manufacturer_manual = serializers.BooleanField()


class ReferenceSourceSerializer(serializers.Serializer):
    title = serializers.CharField()
    holder = serializers.CharField()
    kind = serializers.CharField()
    sha256 = serializers.CharField(allow_null=True)
    pages_total = serializers.IntegerField(allow_null=True)
    url = serializers.CharField(allow_null=True)


class ReferenceRegistrySerializer(serializers.Serializer):
    version = serializers.CharField()
    note = serializers.CharField()
    series = ReferenceSeriesSerializer(many=True)
    sources = serializers.DictField(child=ReferenceSourceSerializer())


class ReferenceSeriesView(APIView):
    @extend_schema(
        operation_id="catalog_reference_series",
        tags=["catalogs"],
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        responses={200: ReferenceRegistrySerializer, 403: ErrorResponseSerializer},
    )
    def get(self, request):
        with catalog_scope(request, roles=READ_ROLES):
            return Response(registry())
