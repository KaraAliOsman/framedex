"""One read-only works index, including the exact legacy quotation cohort.

Stage selection uses the existing engine-backed projection. Only the requested
page loads public project details; no fixed recent-project cap drops old offers.
"""

from collections import Counter

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.views import APIView

from analytics.serializers import QuotationIndexItemSerializer, QuotationIndexQuerySerializer
from analytics.today import matching_quotations
from authentication.errors import contract_error
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from pricing.repository import rows
from pricing.views import ERRORS, scope
from projects.progress import STAGES, project_progress
from projects.serializers import ProjectResponseSerializer
from projects.service import list_projects
from projects.views import response


class WorksQuerySerializer(QuotationIndexQuerySerializer):
    q = serializers.CharField(required=False, allow_blank=True, max_length=255, default="")
    view = serializers.ChoiceField(required=False, default="", choices=["", "quotes"])
    stage = serializers.ChoiceField(required=False, default="", choices=["", *STAGES])
    status = serializers.ChoiceField(required=False, default="", allow_blank=True, choices=[
        "DRAFT", "QUOTED", "APPROVED", "IN_PRODUCTION", "COMPLETED", "CANCELLED",
    ])
    sort = serializers.ChoiceField(required=False, default="", choices=["", "updated", "name"])


class WorkIndexItemSerializer(ProjectResponseSerializer):
    quotation = QuotationIndexItemSerializer(allow_null=True)


class WorksResponseSerializer(serializers.Serializer):
    items = WorkIndexItemSerializer(many=True)
    total = serializers.IntegerField()
    matching = serializers.IntegerField()
    counts = serializers.DictField(child=serializers.IntegerField())
    offset = serializers.IntegerField()
    limit = serializers.IntegerField()


def works_index(org_id, role, *, q="", view="", stage="", status="", sort="",
                attention="", phase="", currency="", offset=0, limit=50):
    quote_view = view == "quotes" or bool(attention or phase or currency)
    if quote_view and role not in {"OWNER", "ESTIMATOR"}:
        raise contract_error(403, "role_not_allowed", "El seguimiento de cotizaciones requiere acceso comercial.")
    # The role-aware HTTP boundary sets verified caller claims; every query also
    # carries org_id. An explicit ID list never widens RLS in list_projects.
    candidates = rows(
        "SELECT id,code,name,client_name,status::text,current_revision,updated_at "
        "FROM public.projects WHERE org_id=%s ORDER BY updated_at DESC,id", [org_id],
    )
    quotes = {}
    if quote_view:
        _, quotation_items = matching_quotations(org_id, query=q, attention=attention,
                                                phase=phase, currency=currency)
        quotes = {item['project_id']: item for item in quotation_items}
        candidates = [item for item in candidates if str(item['id']) in quotes]
        # Legacy /quotes defaults to emission order, not project activity order.
        rank = {identity: index for index, identity in enumerate(quotes)}
        candidates.sort(key=lambda item: rank[str(item['id'])])
    else:
        needle = q.strip().casefold()
        candidates = [item for item in candidates if needle in
                      ' '.join(item[key] for key in ('code', 'name', 'client_name')).casefold()]
    if status:
        candidates = [item for item in candidates if item['status'] == status]
    if sort == 'name':
        candidates.sort(key=lambda item: ((item['name'] or item['code']).casefold(), str(item['id'])))
    elif sort == 'updated':
        candidates.sort(key=lambda item: str(item['id']))
        candidates.sort(key=lambda item: item['updated_at'], reverse=True)
    progress = project_progress(org_id, [item['id'] for item in candidates])
    counts = Counter(item['stage'] for item in progress.values())
    filtered = [item for item in candidates if not stage or progress[str(item['id'])]['stage'] == stage]
    page = filtered[offset:offset + limit]
    details = {str(item['id']): item for item in list_projects(
        org_id, project_ids=[item['id'] for item in page], progress=progress,
    )}
    # A successor or price edit between the selection and detail reads must
    # never pair a new draft with the previous revision's projected sale.
    for item in page:
        detail = details.get(str(item['id']))
        quote = quotes.get(str(item['id']))
        if (detail is None or any(detail[key] != item[key]
                for key in ('current_revision', 'status', 'updated_at'))
                or (quote and quote['revision_code'] != detail['current_revision'])):
            raise contract_error(409, "works_changed", "La lista cambió. Vuelve a cargar las obras.")
    return {
        'items': [{**details[str(item['id'])], 'quotation': quotes.get(str(item['id']))} for item in page],
        'total': len(filtered), 'matching': len(candidates),
        'counts': {value: counts[value] for value in STAGES}, 'offset': offset, 'limit': limit,
    }


class WorksView(APIView):
    @extend_schema(operation_id="projects_works",
        parameters=[ACTIVE_ORGANIZATION_HEADER, WorksQuerySerializer],
        request=None, responses={200: WorksResponseSerializer, **ERRORS}, tags=["projects"])
    def get(self, request):
        query = WorksQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        with scope(request, ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")) as (_, tenant, org_id):
            return response(works_index(org_id, tenant.active_organization.role, **query.validated_data))
