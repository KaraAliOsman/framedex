"""A workshop's own series reaches the workshop once its owner confirms the rules."""

from uuid import UUID

import pytest

from authentication.errors import ContractAPIException
from catalogs import workshop_rules
from documents.repository import load_manufacturing_policies
from engine_api.inspection_repository import InspectorRepository
from pricing.repository import one

from .test_reference_prepare import prepare
from .test_shot09_documentary import as_user, documentary_tenant as documentary_tenant

pytestmark = pytest.mark.rls_integration


def test_pro6004_rules_are_proposed_then_confirmed_and_loadable(documentary_tenant):
    org, _, users, _ = documentary_tenant
    with as_user(users["OWNER"]):
        system_id = UUID(str(prepare(org, users["OWNER"])["id"]))
        proposal = workshop_rules.workshop_rules(org, system_id)
        assert proposal["state"] == "PENDING"
        # Steel goes in the frame, the outer sash and the mullion of PRO6004.
        assert {(rule["role"], rule["profile_angle_left"], rule["profile_angle_right"])
                for rule in proposal["reinforcement_rules"]} == {
            ("FRAME", "45.00", "45.00"), ("FRAME", "45.00", "90.00"), ("FRAME", "90.00", "45.00"),
            ("SASH", "45.00", "45.00"), ("MULLION_V", "90.00", "90.00")}
        with pytest.raises(Exception):
            InspectorRepository().load(system_id, org)

        confirmed = workshop_rules.confirm(org, system_id, users["OWNER"], {
            key: proposal[key] for key in ("chamber_clearance_mm", "inspector", "reinforcement_rules", "bead_offsets")})
        assert confirmed["state"] == "CONFIRMED" and confirmed["version"] == 1
        assert InspectorRepository().load(system_id, org).chamber_clearance_mm == 12
        ids = [one(f"SELECT id FROM public.{table} WHERE system_id=%s AND org_id=%s", [system_id, org])["id"]
               for table in ("manufacturing_placement_policies", "handle_requirement_policies",
                             "reinforcement_cut_policies")]
        policies = load_manufacturing_policies(system_id=system_id, org_id=org,
            placement_id=ids[0], handle_id=ids[1], reinforcement_id=ids[2])
        assert policies.handles.slots == [] and len(policies.reinforcement.rules) == 5

        changed = {**proposal["inspector"], "R08": {"max_spacing_mm": "700.00"}}
        again = workshop_rules.confirm(org, system_id, users["OWNER"], {
            **{key: confirmed[key] for key in ("chamber_clearance_mm", "reinforcement_rules", "bead_offsets")},
            "inspector": changed})
        assert again["version"] == 2 and again["inspector"]["R08"] == {"max_spacing_mm": "700.00"}


def test_reference_series_and_bad_values_are_refused(documentary_tenant):
    org, _, users, _ = documentary_tenant
    global_system = one("SELECT id FROM public.profile_systems WHERE is_global LIMIT 1")["id"]
    with as_user(users["OWNER"]):
        with pytest.raises(ContractAPIException):
            workshop_rules.workshop_rules(org, global_system)
        system_id = UUID(str(prepare(org, users["OWNER"])["id"]))
        proposal = workshop_rules.workshop_rules(org, system_id)
        broken = {**proposal["inspector"], "R02": {"min_ratio": "0"}}
        with pytest.raises(ContractAPIException):
            workshop_rules.confirm(org, system_id, users["OWNER"], {
                **{key: proposal[key] for key in ("chamber_clearance_mm", "reinforcement_rules", "bead_offsets")},
                "inspector": broken})
