"""Tenant accessory policy, revision-bound services and engine previews."""

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
import json
from zoneinfo import ZoneInfo

from django.db import connection
from drf_spectacular.utils import extend_schema
from psycopg import sql
from pydantic import TypeAdapter
from rest_framework import serializers
from rest_framework.views import APIView

from authentication.errors import contract_error
from authentication.rls import tx_aborted
from dekopen_engine.extra_models import ExtraAuthority, ExtraPolicy, ExtraSelection
from dekopen_engine.extras import price_facts, project_lines, service_price
from engine_api.adapter import engine_result_from_api, normalized_root_from_api
from engine_api.repository import SystemParamsRepository
from engine_api.serializers import EngineCalculateRequestSerializer
from pricing.repository import PricingRepository, json_text, one, rows
from pricing.serializers import StrictSerializer
from pricing.views import ERRORS, scope, validate
from projects.views import SCHEMA, response


@contextmanager
def extra_backend():
    # Parameter loaders can enter from several trusted roles. Restore the
    # exact caller role, including failure paths; never broaden tenant RLS.
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_user")
        role = cursor.fetchone()[0]
        cursor.execute("SET LOCAL ROLE pricing_backend")
    try:
        yield
    finally:
        if not tx_aborted():
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))


def load_policy(org_id):
    with extra_backend():
        found = rows("SELECT policy::text FROM public.organization_extra_settings WHERE org_id=%s", [org_id])
    return ExtraPolicy.model_validate_json(found[0]["policy"]) if found else ExtraPolicy()


def lock_policy(org_id):
    rows("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",[str(org_id)+':extras'])


def public_definition(item):
    return {key:value for key,value in item.model_dump(mode="json").items() if key != "cost_rate" and key != "zones"} | {
        "zones": {name:{"selling_rate":str(rate.selling_rate)} for name,rate in item.zones.items()}}


def policy_record(org_id):
    with extra_backend():
        found = rows("SELECT policy::text,revision FROM public.organization_extra_settings WHERE org_id=%s", [org_id])
    policy = ExtraPolicy.model_validate_json(found[0]["policy"]) if found else ExtraPolicy()
    return {"policy":policy.model_dump(mode="json"), "revision":found[0]["revision"] if found else 0}


def selections_for(org_id, project_id, revision):
    with extra_backend():
        found = rows("SELECT selections::text FROM public.project_extra_services WHERE org_id=%s AND project_id=%s AND revision_code=%s",
            [org_id,project_id,revision])
    return TypeAdapter(list[ExtraSelection]).validate_json(found[0]["selections"]) if found else []


def converted_lines(repo, lines):
    converted = []
    for item in lines:
        converted.append(item.model_copy(update={"currency":repo.currency,
            **{key:repo.convert(getattr(item,key),item.currency) for key in
               ("cost_rate","selling_rate","total_cost","total_price")}}))
    return converted


def service_lines(org_id, project, positions, repo):
    policy = load_policy(org_id)
    selections = selections_for(org_id,project["id"],project["current_revision"])
    authority = ExtraAuthority(schema_version=1,definitions=[item for item in policy.services if item.scope == "PROJECT"],source="Organización")
    return converted_lines(repo, project_lines(authority,selections,
        [(position["width_mm"],position["height_mm"],int(position["quantity"])) for position in positions])) if selections else []


def apply_position_defaults(org_id, design):
    """Apply only to newly created position intent, never a sealed snapshot."""
    policy = load_policy(org_id)
    if not policy.position_defaults:
        return design
    design = deepcopy(design)
    tree = design["parametric_tree"]
    modules = tree["assembly"]["modules"] if tree.get("version") == "product-v2" else [{"tree":tree}]
    params = SystemParamsRepository().load_visible(design["system_id"],org_id)
    known = {item.code for item in params.extra_authority.definitions if item.scope == "POSITION"} if params.extra_authority else set()
    for module in modules:
        intent = module["tree"]
        existing = {item["code"] for item in intent.get("extras",[])}
        # A catalog-specific template cannot silently disappear on a different
        # series. The estimator must choose compatible defaults in Settings.
        if any(item.code not in known for item in policy.position_defaults):
            raise contract_error(422,"extra_template_incompatible","La plantilla de extras no corresponde a esta serie. Revísala en Ajustes.")
        intent["extras"] = [*intent.get("extras",[]),*(item.model_dump(mode="json") for item in policy.position_defaults if item.code not in existing)]
    return design


class PolicyWriteSerializer(StrictSerializer):
    policy = serializers.JSONField()
    expected_revision = serializers.IntegerField(min_value=0)
    reason = serializers.CharField(max_length=1000)

    def validate_policy(self, value):
        try:
            return ExtraPolicy.model_validate_json(json_text(value)).model_dump(mode="json")
        except (ValueError,TypeError) as error:
            raise serializers.ValidationError(str(error)) from error


class PolicyResponseSerializer(serializers.Serializer):
    policy = serializers.JSONField()
    revision = serializers.IntegerField()


class ExtraPolicyView(APIView):
    @extend_schema(operation_id="organizationExtraPolicy",responses={200:PolicyResponseSerializer,**ERRORS},**SCHEMA)
    def get(self, request):
        with scope(request,{"OWNER"}) as (_,_,org):
            return response(policy_record(org))

    @extend_schema(operation_id="organizationExtraPolicySave",request=PolicyWriteSerializer,
        responses={200:PolicyResponseSerializer,**ERRORS},**SCHEMA)
    def put(self, request):
        data = validate(PolicyWriteSerializer,request.data)
        with scope(request,{"OWNER"}) as (token,_,org), extra_backend():
            lock_policy(org)
            current = policy_record(org)
            if current["revision"] != data["expected_revision"]:
                raise contract_error(409,"stale_extra_policy","Otra persona cambió la plantilla. Recarga antes de guardar.")
            next_revision = current["revision"]+1
            rows("INSERT INTO public.organization_extra_settings(org_id,policy,revision) VALUES(%s,%s::jsonb,%s) "
                "ON CONFLICT(org_id) DO UPDATE SET policy=EXCLUDED.policy,revision=EXCLUDED.revision,updated_at=clock_timestamp() RETURNING revision",
                [org,json_text(data["policy"]),next_revision])
            rows("INSERT INTO public.organization_extra_history(org_id,revision,policy,actor_id,reason) VALUES(%s,%s,%s::jsonb,%s,%s) RETURNING revision",
                [org,next_revision,json_text(data["policy"]),token.user_id,data["reason"]])
            return response(policy_record(org))


class ServicesWriteSerializer(StrictSerializer):
    selections = serializers.ListField(child=serializers.JSONField(),max_length=30)
    expected_updated_at = serializers.DateTimeField()

    def validate_selections(self,value):
        try:
            return TypeAdapter(list[ExtraSelection]).validate_json(json_text(value))
        except (ValueError,TypeError) as error:
            raise serializers.ValidationError(str(error)) from error


class ServicesResponseSerializer(serializers.Serializer):
    definitions = serializers.ListField(child=serializers.JSONField())
    selections = serializers.ListField(child=serializers.JSONField())
    lines = serializers.ListField(child=serializers.JSONField())
    updated_at = serializers.DateTimeField()
    currency = serializers.CharField()
    locked = serializers.BooleanField()
    reason = serializers.CharField(allow_null=True)


def services_response(org,project):
    from projects.service import _priced
    from dekopen_engine.commercial import PricingError
    from pricing.service import pricing_public_detail
    reason, lines = None, []
    with extra_backend():
        currency = one("SELECT currency FROM public.tenancy_organizations WHERE id=%s",[org])["currency"]
    locked = project["status"] != "DRAFT" or _priced(org,project["id"],project["current_revision"])
    if locked:
        from projects.service import _pricing_authority
        operation = _pricing_authority(org,project["id"],project["current_revision"])
        if operation:
            with extra_backend():
                frozen = one("SELECT result::text,input_snapshot::text FROM public.pricing_operations WHERE id=%s AND org_id=%s",[operation["id"],org])
            stored = json.loads(frozen["result"])
            policy = ExtraPolicy.model_validate_json(json_text(json.loads(frozen['input_snapshot']).get('extra_policy',{}).get('policy',{})))
            public_lines = [{key:value for key,value in item.items() if key not in {"cost_rate","total_cost"}} for item in stored.get("services",[])]
            reason = None
        else:
            policy = ExtraPolicy()
            public_lines = []
            reason = "Sin dato: esta revisión no tiene una autoridad de servicios sellada."
    else:
        policy = load_policy(org)
        positions = rows("SELECT width_mm,height_mm,quantity FROM public.project_positions WHERE project_id=%s AND org_id=%s",[project["id"],org])
        with extra_backend():
            repo = PricingRepository(org,datetime.now(ZoneInfo("America/Santiago")).date(),currency)
            try:
                lines = service_lines(org,project,positions,repo)
            except PricingError as error:
                reason = "Sin dato: " + pricing_public_detail(error.code)
            except ValueError as error:
                reason = str(error)
        public_lines = [{key:value for key,value in service_price(item,currency).items() if key not in {"cost_rate","total_cost"}} for item in lines]
    return {"definitions":[public_definition(item) for item in policy.services if item.scope == "PROJECT"],
        "selections":[item.model_dump(mode="json") for item in selections_for(org,project["id"],project["current_revision"])],
        "lines":public_lines,
        "currency":currency,"updated_at":project["updated_at"],"reason":reason,
        "locked":locked}


def copy_services(org_id,source,destination):
    selections = selections_for(org_id,source["id"],source["current_revision"])
    if selections:
        with extra_backend():
            rows("INSERT INTO public.project_extra_services(org_id,project_id,revision_code,selections) VALUES(%s,%s,%s,%s::jsonb) RETURNING updated_at",
                [org_id,destination["id"],destination["current_revision"],json_text([item.model_dump(mode="json") for item in selections])])


class ProjectServicesView(APIView):
    @extend_schema(operation_id="projectExtraServices",responses={200:ServicesResponseSerializer,**ERRORS},**SCHEMA)
    def get(self,request,project_id):
        from projects.service import project_row
        with scope(request,{"OWNER","ESTIMATOR","WORKSHOP_MANAGER"}) as (_,_,org):
            return response(services_response(org,project_row(org,project_id)))

    @extend_schema(operation_id="projectExtraServicesSave",request=ServicesWriteSerializer,
        responses={200:ServicesResponseSerializer,**ERRORS},**SCHEMA)
    def put(self,request,project_id):
        from projects.service import editable, unchanged
        data = validate(ServicesWriteSerializer,request.data)
        with scope(request,{"OWNER","ESTIMATOR"}) as (_,_,org):
            project = editable(org,project_id)
            unchanged(project,data["expected_updated_at"])
            policy = load_policy(org)
            authority = ExtraAuthority(schema_version=1,definitions=[item for item in policy.services if item.scope == "PROJECT"],source="Organización")
            positions = rows("SELECT width_mm,height_mm,quantity,bom_snapshot FROM public.project_positions WHERE project_id=%s AND org_id=%s",[project_id,org])
            try:
                lines = project_lines(authority,data["selections"],[(p["width_mm"],p["height_mm"],int(p["quantity"])) for p in positions]) if data["selections"] else []
                if any(item.installation for item in lines) and any(
                    fact.get("installation") for p in positions for fact in (p["bom_snapshot"].get("extras",[]) if isinstance(p["bom_snapshot"],dict) else json.loads(p["bom_snapshot"]).get("extras",[]))):
                    raise ValueError("La instalación ya se seleccionó en una posición. Usa una sola regla para el proyecto.")
            except ValueError as error:
                raise contract_error(422,"extra_services_invalid",str(error)) from error
            with extra_backend():
                rows("INSERT INTO public.project_extra_services(org_id,project_id,revision_code,selections) VALUES(%s,%s,%s,%s::jsonb) "
                    "ON CONFLICT(org_id,project_id,revision_code) DO UPDATE SET selections=EXCLUDED.selections,updated_at=clock_timestamp() RETURNING updated_at",
                    [org,project_id,project["current_revision"],json_text([item.model_dump(mode="json") for item in data["selections"]])])
            project["updated_at"] = rows("UPDATE public.projects SET updated_at=clock_timestamp() WHERE id=%s AND org_id=%s RETURNING updated_at",[project_id,org])[0]["updated_at"]
            return response(services_response(org,project))


class ExtrasPreviewResponseSerializer(serializers.Serializer):
    available_codes = serializers.ListField(child=serializers.CharField())
    available_by_module = serializers.DictField(child=serializers.ListField(child=serializers.CharField()))
    target_module_id = serializers.CharField(allow_null=True)
    leaf_targets = serializers.ListField(child=serializers.JSONField())
    extras = serializers.ListField(child=serializers.JSONField())
    suggestions = serializers.ListField(child=serializers.JSONField())
    currency = serializers.CharField()
    total_price = serializers.CharField(allow_null=True)
    reason = serializers.CharField(allow_null=True)


class ExtrasPreviewRequestSerializer(EngineCalculateRequestSerializer):
    target_module_id = serializers.CharField(required=False, max_length=150)


class ExtrasPreviewView(APIView):
    @extend_schema(operation_id="positionExtrasPreview",request=ExtrasPreviewRequestSerializer,
        responses={200:ExtrasPreviewResponseSerializer,**ERRORS},**SCHEMA)
    def post(self,request):
        from dekopen_engine.commercial import PricingError
        from pricing.service import pricing_public_detail
        data = validate(ExtrasPreviewRequestSerializer,request.data)
        with scope(request,{"OWNER","ESTIMATOR"}) as (_,_,org):
            try:
                params = SystemParamsRepository().load_visible(data["system_id"],org)
                result = engine_result_from_api(tree=data["parametric_tree"],color=data["color"],params=params,
                    nominal_width_mm=data["nominal_width_mm"],nominal_height_mm=data["nominal_height_mm"],
                    coupler_articles=SystemParamsRepository().load_coupler_articles(data["system_id"],org))
                from dekopen_engine.geometry import accessory_leaves, compute_geometry
                from decimal import Decimal
                tree = data['parametric_tree']
                modules = tree['assembly']['modules'] if tree.get('version') == 'product-v2' else [
                    {'tree':tree,'width_mm':data['nominal_width_mm'],'height_mm':data['nominal_height_mm']}]
                target = data.get('target_module_id')
                if target is not None and (tree.get('version') != 'product-v2' or not any(module['id'] == target for module in modules)):
                    raise ValueError('El módulo seleccionado no existe en este diseño. Recarga la posición.')
                leaf_targets, available_by_module, classic_codes = [], {}, []
                definitions = [item for item in params.extra_authority.definitions if item.scope == 'POSITION'] if params.extra_authority else []
                for module in modules:
                    if module.get('contour') or module.get('frameless'):
                        if module['tree'].get('extras') or module.get('id') == target:
                            raise ValueError('Esta forma no declara una autoridad de accesorios; revisa su catálogo.')
                        available_by_module[module['id']] = []
                        continue
                    root = normalized_root_from_api(parametric_tree=module['tree'],nominal_width_mm=Decimal(module['width_mm']),
                        nominal_height_mm=Decimal(module['height_mm']),color=data['color'],params=params)
                    computation = compute_geometry(root,params,finish=data['color'])
                    targets = accessory_leaves(computation,root)
                    movements = {leaf.opening.movement.value for leaf in targets}
                    codes = [item.code for item in definitions if not item.allowed_movements or movements.intersection(item.allowed_movements)]
                    if tree.get('version') == 'product-v2':
                        available_by_module[module['id']] = codes
                    else:
                        classic_codes = codes
                    if target is not None and module['id'] != target:
                        continue
                    if target is not None:
                        # Return local facts/selection targets for the selected
                        # tree, after validating the complete assembly above.
                        result = computation.result
                        if result is None:
                            raise ValueError('El módulo necesita completar su fabricación antes de calcular accesorios.')
                    prefix = str(module['id'])+'|' if tree.get('version') == 'product-v2' else ''
                    if target is not None:
                        prefix = ''
                    leaf_targets.extend({'bay_id':prefix+leaf.bay_id,'leaf_id':prefix+leaf.leaf_id if leaf.leaf_id else None,
                        'width_mm':str(leaf.width_mm),'height_mm':str(leaf.height_mm),'movement':leaf.opening.movement.value,
                        **({'module_id':module['id']} if tree.get('version') == 'product-v2' else {})} for leaf in targets)
                # A whole assembly has no single selection target. Consumers
                # must choose its module map or request an explicit target.
                available_codes = available_by_module[target] if target else classic_codes
            except ValueError as error:
                raise contract_error(422,"position_extras_invalid",str(error)) from error
            with extra_backend():
                currency = one("SELECT currency FROM public.tenancy_organizations WHERE id=%s",[org])["currency"]
                repo = PricingRepository(org,datetime.now(ZoneInfo("America/Santiago")).date(),currency)
                try:
                    lines = converted_lines(repo,price_facts(params.extra_authority,result.extras)) if result.extras else []
                except PricingError as error:
                    return response({"available_codes":available_codes,"available_by_module":available_by_module,"target_module_id":target,"leaf_targets":leaf_targets,"extras":[fact.model_dump(mode="json") for fact in result.extras],
                        "suggestions":[item.model_dump(mode="json") for item in result.extra_suggestions],"currency":currency,
                        "total_price":None,"reason":pricing_public_detail(error.code)})
            return response({"available_codes":available_codes,"available_by_module":available_by_module,"target_module_id":target,"leaf_targets":leaf_targets,"extras":[{key:value for key,value in service_price(item,currency).items() if key not in {"cost_rate","total_cost"}} for item in lines],
                "suggestions":[item.model_dump(mode="json") for item in result.extra_suggestions],"currency":currency,
                "total_price":str(sum((item.total_price for item in lines),start=0)),"reason":None})
