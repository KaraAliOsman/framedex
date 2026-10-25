"""Workshop rules a workshop confirms for its own series.

A series created by a workshop quotes as soon as its profiles and prices exist,
but the workshop documents (work order, cut optimisation, assembly checklist)
also need four authorities that only the global reference families had:

* how steel is cut inside each welded or milled profile;
* where the glazing beads sit on each side;
* where the handle goes (structured openings already carry it in their
  opening rule, so the policy only lists legacy slots);
* the fourteen inspector rules plus the hardware chamber clearance.

Nothing here is applied silently. ``proposal`` derives what it can from the
series itself and offers general reference values for the rest, each labelled
with where it comes from; ``confirm`` stores exactly what the owner accepted.
Policies are immutable, so confirming again creates a new version.
"""

import json
from decimal import Decimal

from django.db import connection, transaction

from authentication.errors import contract_error
from authentication.rls import catalog_backend
from catalogs import service
from dekopen_engine.inspection_models import InspectorConfig
from dekopen_engine.manufacturing import (
    ManufacturingAuthorityError, handle_policy_from_json, placement_policy_from_json,
    reinforcement_policy_from_json,
)
from pricing.repository import one, rows

RULES = tuple(f"R{number:02d}" for number in range(1, 15))
SIDES = ("TOP", "RIGHT", "BOTTOM", "LEFT")

# General reference values used across the PVC and aluminium families DEKOPEN
# ships. They are a starting point the owner reviews, never a manufacturer fact.
REFERENCE_SOURCE = "Referencia general DEKOPEN para ventanas de PVC y aluminio"
INSPECTOR_REFERENCE = {
    "R01": {},
    "R02": {"min_ratio": "0.4000", "max_ratio": "2.5000", "suggested_ratio": "1.5000"},
    "R03": {"min_width_mm": "350.00", "max_width_mm": "1600.00", "max_height_mm": "2400.00"},
    "R04": {"monolithic_4_max_area_m2": "1.8000", "dvh_4_any_4_max_area_m2": "2.6000"},
    "R05": {"span_trigger_mm": "1800.00"},
    "R06": {},
    "R07": {"width_trigger_mm": "800.00", "required_bottom_drains": 3},
    "R08": {"max_spacing_mm": "800.00"},
    "R09": {"white_limit_mm": "4000.00", "foiled_limit_mm": "3000.00"},
    "R10": {"tolerance_mm": "1.50"},
    "R11": {"expected_mm": "12.00", "tolerance_mm": "1.50", "suggested_sash_overlap_mm": "8.00"},
    "R12": {"width_trigger_mm": "4500.00", "minimum_ix_cm4": "45.0000"},
    "R13": {"height_trigger_mm": "1200.00", "required_stay_arms": 2},
    "R14": {"weight_trigger_kg": "150.00", "required_carriages": 4, "minimum_capacity_kg": "80.00"},
}
CHAMBER_REFERENCE = "12.00"

# Profile cut angles the engine emits per role. Steel is cut square inside and
# keeps the length the engine already computes from the series' own rules.
_ANGLES = {
    "FRAME": (("45.00", "45.00"), ("45.00", "90.00"), ("90.00", "45.00")),
    "MULLION_V": (("90.00", "90.00"),),
    "MULLION_H": (("90.00", "90.00"),),
}
_WELDED = ("45.00", "45.00")


def _owned_system(org_id, system_id):
    system = service.retrieve(service.SYSTEMS, org_id, system_id)
    if system.get("is_global") or str(system.get("org_id")) != str(org_id):
        raise contract_error(409, "workshop_rules_reference_series",
            "Las series de referencia ya traen sus reglas de taller.")
    return system


def _reinforcement_rules(articles):
    roles = sorted({str(article["role"]) for article in articles
        if article.get("is_active", True) and (article.get("reinforcement_rule")
            or article.get("reinforcement_sku"))})
    return [{"role": role, "profile_angle_left": left, "profile_angle_right": right,
             "reinforcement_angle_left": "90.00", "reinforcement_angle_right": "90.00",
             "length_authority": "EXISTING_ENGINE", "compatible_with_existing_length": True}
            for role in roles for left, right in _ANGLES.get(role, (_WELDED,))]


def _latest(table, system_id, org_id):
    found = rows(f"SELECT id,version,authority::text FROM public.{table} "
                 "WHERE system_id=%s AND org_id=%s ORDER BY version DESC LIMIT 1", [system_id, org_id])
    if not found:
        return None
    return {"id": str(found[0]["id"]), "version": found[0]["version"],
            "authority": json.loads(found[0]["authority"])}


def workshop_rules(org_id, system_id):
    system = _owned_system(org_id, system_id)
    articles = service.list_rows(service.ARTICLES, org_id, system_id)
    reinforcement = _latest("reinforcement_cut_policies", system_id, org_id)
    placement = _latest("manufacturing_placement_policies", system_id, org_id)
    handles = _latest("handle_requirement_policies", system_id, org_id)
    inspector = {row["rule_id"]: json.loads(row["params"]) for row in rows(
        "SELECT rule_id,params::text FROM public.inspector_rule_configs "
        "WHERE system_id=%s AND org_id=%s AND is_active", [system_id, org_id])}
    clearance = system.get("chamber_clearance_mm")
    confirmed = bool(reinforcement and placement and handles and clearance is not None
                     and set(inspector) == set(RULES))
    derived = _reinforcement_rules(articles)
    return {
        "system_id": str(system_id),
        "state": "CONFIRMED" if confirmed else "PENDING",
        "version": reinforcement["version"] if reinforcement else None,
        "chamber_clearance_mm": str(clearance) if clearance is not None else CHAMBER_REFERENCE,
        "inspector": {rule: inspector.get(rule, INSPECTOR_REFERENCE[rule]) for rule in RULES},
        "reinforcement_rules": reinforcement["authority"]["rules"] if reinforcement else derived,
        "bead_offsets": placement["authority"]["bead_offsets"] if placement else {
            side: {"x_mm": "0.00", "y_mm": "0.00"} for side in SIDES},
        "sources": {
            "inspector": "Confirmado por el taller" if confirmed else REFERENCE_SOURCE,
            "reinforcement": "Cortes de perfil que llevan acero. El acero va recto, con el largo "
                             "que calcula la regla de refuerzo de la serie.",
            "beads": "Al ras del vidrio en los cuatro lados.",
            "handles": "Cada apertura usa la regla de manilla declarada en la serie.",
        },
        "pending_reinforcement": not derived,
    }


def _numbers(params):
    return {key: Decimal(str(value)) for key, value in params.items()}


def _decimal_payload(value):
    return json.loads(json.dumps(value), parse_float=Decimal)


def confirm(org_id, system_id, actor_id, data):
    system = _owned_system(org_id, system_id)
    clearance = Decimal(str(data["chamber_clearance_mm"]))
    inspector = {rule: data["inspector"].get(rule, {}) for rule in RULES}
    try:
        InspectorConfig.model_validate({rule: {key: Decimal(str(value)) for key, value in params.items()}
                                        for rule, params in inspector.items()})
    except ValueError as error:
        raise contract_error(400, "workshop_rules_invalid", "Revisa los valores de inspección.") from error
    with transaction.atomic():
        version = (one("SELECT COALESCE(MAX(version),0) AS v FROM public.reinforcement_cut_policies "
                       "WHERE system_id=%s AND org_id=%s", [system_id, org_id])["v"] or 0) + 1
        code = str(system["code"]).upper()
        policies = {
            "reinforcement_cut_policies": ({"schema_version": 1, "policy_id": f"{code}_REFUERZO_V{version}",
                "version": version, "rules": data["reinforcement_rules"]}, reinforcement_policy_from_json),
            "manufacturing_placement_policies": ({"schema_version": 1,
                "policy_id": f"{code}_COLOCACION_V{version}", "version": version,
                "sliding_leaf_offsets": {}, "sliding_infill_offsets": {},
                "bead_offsets": data["bead_offsets"]}, placement_policy_from_json),
            "handle_requirement_policies": ({"schema_version": 1, "policy_id": f"{code}_MANILLAS_V{version}",
                "version": version, "slots": []}, handle_policy_from_json),
        }
        for authority, parse in policies.values():
            try:
                parse(_decimal_payload(authority))
            except ManufacturingAuthorityError as error:
                raise contract_error(400, "workshop_rules_invalid",
                    "Revisa las reglas de refuerzo y junquillos.") from error
        if system.get("chamber_clearance_mm") is None or Decimal(str(system["chamber_clearance_mm"])) != clearance:
            service.update(service.SYSTEMS, org_id, system_id,
                {"chamber_clearance_mm": str(clearance)},
                expected_revision=f'"{system["revision"]}"', actor_id=actor_id)
        with catalog_backend():
            for table, (authority, _) in policies.items():
                one(f"INSERT INTO public.{table}(system_id,org_id,version,authority) "
                    "VALUES(%s,%s,%s,%s::jsonb) RETURNING id",
                    [system_id, org_id, version, json.dumps(authority)])
            # Only a rule that is new or changed is written: a series already
            # used in a work accepts its first declaration but keeps what it
            # declared (the database refuses that change).
            current = {row["rule_id"]: (row["is_active"], _numbers(json.loads(row["params"]))) for row in rows(
                "SELECT rule_id,is_active,params::text FROM public.inspector_rule_configs "
                "WHERE system_id=%s AND org_id=%s", [system_id, org_id])}
            with connection.cursor() as cursor:
                for rule, params in inspector.items():
                    if current.get(rule) == (True, _numbers(params)):
                        continue
                    cursor.execute("SELECT private.declare_inspector_rule(%s,%s,%s,%s::jsonb)",
                                   [system_id, org_id, rule, json.dumps(params)])
    return workshop_rules(org_id, system_id)
