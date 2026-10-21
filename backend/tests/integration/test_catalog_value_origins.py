"""Real RLS, exact historical values, and verification invalidation."""

from decimal import Decimal

from django.db import DatabaseError, transaction
import pytest

from authentication.rls import catalog_backend
from catalogs import service
from catalogs.family_templates import family_template
from catalogs.serializers import SystemWriteSerializer
from catalogs.value_origins import annotated_cells, cells, cell_history, latest_versions, record_origin
from pricing.repository import json_text, one, rows

from .test_shot09_documentary import as_user, documentary_tenant as documentary_tenant

pytestmark = pytest.mark.rls_integration


def create_series(org, actor, *, suggested=False):
    template = family_template("pvc-casement-60-70")
    serializer = SystemWriteSerializer(data={**template["system"], "name": "Proline PRO6004 · prueba",
        "code": "PRO6004-TEST", "version": 1, "is_active": True})
    assert serializer.is_valid(), serializer.errors
    annotations = {field: {"origin": "SUGGESTED", "source_ref": template["source_ref"]}
        for field, _ in cells(serializer.validated_data)} if suggested else {}
    with annotated_cells(annotations):
        return service.create(service.SYSTEMS, org, serializer.validated_data, actor_id=actor)


def test_suggested_edit_confirmation_history_and_missing_values(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        system = create_series(org, actor, suggested=True)
        history = cell_history(org, system["id"], "profile_systems", system["id"], "glass_clearance_white_mm")
        assert len(history) == 1 and history[0]["origin"] == "SUGGESTED"
        assert history[0]["value_numeric"] == Decimal("5") and history[0]["value_json"] is None
        assert history[0]["set_by"] == actor
        current = service.update(service.SYSTEMS, org, system["id"], {"glass_clearance_white_mm": "4.25"},
            expected_revision='"' + system["revision"] + '"', actor_id=actor)
        history = cell_history(org, system["id"], "profile_systems", system["id"], "glass_clearance_white_mm")
        assert [item["value"] for item in history] == [Decimal("4.25"), Decimal("5")]
        assert history[0]["previous_value"] == Decimal("5") and history[0]["previous_id"] == history[1]["id"]
        assert history[0]["origin"] == "WORKSHOP"
        record_origin(org_id=org, system_id=system["id"], table="profile_systems", row=current,
            field_name="rebate_depth_mm", origin="WORKSHOP", source_ref="Confirmado en el taller", actor_id=actor)
        current = service.update(service.SYSTEMS, org, system["id"], {"rebate_depth_mm": None},
            expected_revision='"' + current["revision"] + '"', actor_id=actor)
        assert "rebate_depth_mm" not in dict(cells(current))
        cleared = cell_history(org, system["id"], "profile_systems", system["id"], "rebate_depth_mm")
        assert cleared[0]["value"] is None and cleared[0]["previous_value"] == Decimal("15")
        # Template annotations were scoped to its write, not the connection.
        assert history[0]["source_ref"] == "Escrito por el taller"


def test_tenant_isolation_backend_actor_and_append_only_guards(documentary_tenant):
    org, other, users, foreign = documentary_tenant
    with as_user(users["OWNER"]):
        system = create_series(org, users["OWNER"])
        versions = latest_versions(org, system["id"])
        assert versions
        with catalog_backend():
            one("INSERT INTO public.catalog_series_setup(system_id,org_id,template_id,template_version) "
                "VALUES(%s,%s,'pvc-casement-60-70',1) RETURNING system_id", [system["id"], org])
    with as_user(foreign):
        assert not latest_versions(org, system["id"])
        assert not rows("SELECT * FROM public.catalog_series_setup WHERE system_id=%s", [system["id"]])
        with pytest.raises(DatabaseError), transaction.atomic():
            record_origin(org_id=other, system_id=system["id"], table="profile_systems", row=system,
                field_name="depth_mm", origin="WORKSHOP", source_ref="Foreign", actor_id=foreign)
    with as_user(users["ESTIMATOR"]):
        assert latest_versions(org, system["id"])
        with pytest.raises(DatabaseError), transaction.atomic():
            record_origin(org_id=org, system_id=system["id"], table="profile_systems", row=system,
                field_name="depth_mm", origin="WORKSHOP", source_ref="Not allowed", actor_id=users["ESTIMATOR"])
    with pytest.raises(DatabaseError), transaction.atomic():
        one("UPDATE public.catalog_value_history SET source_ref='rewritten' WHERE id=%s RETURNING id", [versions[0]["id"]])
    with pytest.raises(DatabaseError), transaction.atomic():
        one("DELETE FROM public.catalog_value_history WHERE id=%s RETURNING id", [versions[0]["id"]])


def test_manual_origin_requires_matching_reviewed_document_and_exact_current_value(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        system = create_series(org, actor)
        with pytest.raises(DatabaseError), transaction.atomic():
            record_origin(org_id=org, system_id=system["id"], table="profile_systems", row=system,
                field_name="depth_mm", origin="MANUAL", source_ref="Unsupported claim", actor_id=actor)
        with catalog_backend():
            evidence = one("INSERT INTO public.catalog_parameter_evidence(org_id,authority_table,row_id,"
                "field_name,source_document,source_page,canonical_value,declared_by,review_state,reviewed_by,reviewed_at,extraction_method) "
                "VALUES(%s,'profile_systems',%s,'depth_mm','Manual de prueba.pdf',14,%s::jsonb,%s,'REVIEWED',%s,now(),'MANUAL') RETURNING id",
                [org, system["id"], json_text("60.00"), actor, actor])
        record_origin(org_id=org, system_id=system["id"], table="profile_systems", row=system,
            field_name="depth_mm", origin="MANUAL", source_ref="Manual de prueba.pdf · pág. 14", actor_id=actor, evidence_id=evidence["id"])
        current = service.update(service.SYSTEMS, org, system["id"], {"depth_mm": "61.00"},
            expected_revision='"' + system["revision"] + '"', actor_id=actor)
        with pytest.raises(DatabaseError), transaction.atomic():
            record_origin(org_id=org, system_id=system["id"], table="profile_systems", row=current,
                field_name="depth_mm", origin="MANUAL", source_ref="Stale manual", actor_id=actor, evidence_id=evidence["id"])
        history = cell_history(org, system["id"], "profile_systems", system["id"], "depth_mm")
        assert history[0]["origin"] == "WORKSHOP" and history[1]["origin"] == "MANUAL"


def test_verification_is_cleared_when_any_rule_changes(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        system = create_series(org, actor)
        with catalog_backend():
            one("INSERT INTO public.catalog_series_setup(system_id,org_id,verified_at,verified_by,verified_hash) "
                "VALUES(%s,%s,now(),%s,%s) RETURNING system_id", [system["id"], org, actor, "sha256:" + "a" * 64])
        service.update(service.SYSTEMS, org, system["id"], {"rebate_depth_mm": "14.00"},
            expected_revision='"' + system["revision"] + '"', actor_id=actor)
        setup = one("SELECT * FROM public.catalog_series_setup WHERE system_id=%s", [system["id"]])
        assert setup["verified_at"] is setup["verified_by"] is setup["verified_hash"] is None
