"""Exercise template creation, six tabs and atomic exact edits under real RLS."""

from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import transaction

from authentication.errors import ContractAPIException
from catalogs import evidence, series, service
from authentication.rls import catalog_backend
from catalogs.series_serializers import SeriesCreateSerializer, SeriesSheetSerializer
from catalogs.value_origins import cell_history
from pricing.repository import one
from engine_api.repository import SystemParamsRepository
from engine_api.adapter import calculate_from_api

from .test_shot09_documentary import as_user, documentary_tenant as documentary_tenant
from .test_shot08_pricing import owner_client

pytestmark = pytest.mark.rls_integration


def pro6004_input():
    return {"template_id": "pvc-casement-60-70", "template_version": 1,
        "name": "Proline PRO6004", "code": "PRO6004-" + uuid4().hex[:8], "manufacturer": "Proline",
        "profiles": [
            {"sku": "PRO-F", "name": "Marco del taller", "role": "FRAME", "face_width_mm": "60.00",
                "reinforcement_sku": "STEEL-F", "screw_sku": "SCREW-F"},
            {"sku": "PRO-S", "name": "Hoja del taller", "role": "SASH", "face_width_mm": "60.00",
                "reinforcement_sku": "STEEL-S", "screw_sku": "SCREW-S"},
            {"sku": "PRO-B", "name": "Junquillo del taller", "role": "GLAZING_BEAD", "face_width_mm": "20.00"}],
        "glazing": [{"bead_sku": "PRO-B", "glass_thickness_mm": "24.00", "bead_width_mm": "20.00"}],
        "hardware": [{"sku": "PRO-TURN", "name": "Abatible del taller", "opening_type": "TURN",
            "contents": [{"sku": "HINGE", "name": "Bisagra", "qty": "2", "unit": "unit"}]}]}


def create(org, actor, **overrides):
    validator = SeriesCreateSerializer(data={**pro6004_input(), **overrides})
    assert validator.is_valid(), validator.errors
    return series.create_from_template(org, actor, validator.validated_data)


def address(sheet, *, resource="systems", field="glass_clearance_white_mm"):
    return next({key: item[key] for key in ("resource", "row_id", "field")} for item in sheet["cells"]
        if item["resource"] == resource and item["field"] == field)


def test_template_sheet_preserves_user_inputs_and_defaults_with_six_tabs(documentary_tenant):
    org, _, users, _ = documentary_tenant
    with as_user(users["OWNER"]):
        sheet = create(org, users["OWNER"])
        public = SeriesSheetSerializer(sheet).data
        assert set(public["tabs"]) == {"profiles", "rules", "hardware", "glazing_colors", "typologies", "prices"}
        assert sheet["setup"]["template_id"] == "pvc-casement-60-70"
        assert sheet["setup"]["verified_at"] is None
        assert any(cell["field"] == "face_width_mm" and cell["origin"] == "WORKSHOP" for cell in sheet["cells"])
        assert any(cell["field"] == "cut_rule.welding_loss_per_end_mm" and cell["value"] == "3.00"
            and cell["origin"] == "SUGGESTED" for cell in sheet["cells"])
        assert all(cell["origin"] == "WORKSHOP" for cell in sheet["cells"]
            if cell["field"] in {"reinforcement_sku", "reinforcement_rule.reinforcement_sku", "reinforcement_rule.screw_sku"} and cell["value"])
        assert len(sheet["tabs"]["glazing_colors"]["beads"]) == 1
        assert len(sheet["tabs"]["hardware"]) == 1
        assert not sheet["tabs"]["prices"]["items"]
        assert not series.price_items(org, sheet["id"])


def test_edit_confirm_history_and_stale_lot_are_atomic(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet = create(org, actor)
        cell = address(sheet)
        updated = series.edit_cells(org, sheet["id"], actor, {"revision": sheet["revision"],
            "changes": [{**cell, "value": "4.25"}, {**address(sheet, resource="articles", field="cut_rule.welding_loss_per_end_mm"), "value": "2.75"}]})
        assert updated["tabs"]["rules"]["glass_clearance_white_mm"] == Decimal("4.25")
        assert updated["revision"] != sheet["revision"]
        with pytest.raises(ContractAPIException, match="serie cambió"), transaction.atomic():
            series.confirm_cells(org, sheet["id"], actor, {"revision": sheet["revision"], "cells": [address(sheet, field="rebate_depth_mm")]})
        confirmed = series.confirm_cells(org, sheet["id"], actor, {"revision": updated["revision"], "cells": [address(sheet, field="rebate_depth_mm")]})
        assert next(item for item in confirmed["cells"] if item["resource"] == "systems" and item["field"] == "rebate_depth_mm")["origin"] == "WORKSHOP"
        history = series.history(org, sheet["id"], cell)["items"]
        assert history[0]["value"] == "4.25" and history[0]["previous_value"] == "5.00"
        assert history[0]["set_by"] == actor
        with pytest.raises(ContractAPIException), transaction.atomic():
            series.edit_cells(org, sheet["id"], actor, {"revision": confirmed["revision"], "changes": [
                {**cell, "value": "3.00"}, {**cell, "field": "rebate_depth_mm", "value": "-1"}]})
        assert series.series_sheet(org, sheet["id"])["revision"] == confirmed["revision"]
        assert len(cell_history(org, sheet["id"], "profile_systems", sheet["id"], cell["field"])) == 2


def test_failing_create_rolls_back_series_and_history(documentary_tenant):
    org, _, users, _ = documentary_tenant
    with as_user(users["OWNER"]):
        count = one("SELECT count(*) AS n FROM public.catalog_value_history WHERE org_id=%s", [org])["n"]
        with pytest.raises(ContractAPIException), transaction.atomic():
            create(org, users["OWNER"], glazing=[{"bead_sku": "MISSING", "glass_thickness_mm": "24", "bead_width_mm": "20"}])
        assert not service.list_rows(service.SYSTEMS, org) or all(row["org_id"] is None for row in service.list_rows(service.SYSTEMS, org))
        assert one("SELECT count(*) AS n FROM public.catalog_value_history WHERE org_id=%s", [org])["n"] == count


def test_foreign_sheet_and_cross_series_cells_are_rejected(documentary_tenant):
    org, other, users, foreign = documentary_tenant
    with as_user(users["OWNER"]):
        first = create(org, users["OWNER"])
        second = create(org, users["OWNER"])
        with pytest.raises(ContractAPIException), transaction.atomic():
            series.edit_cells(org, first["id"], users["OWNER"], {"revision": first["revision"], "changes": [
                {**address(second), "value": "4.00"}]})
    with as_user(foreign), pytest.raises(ContractAPIException), transaction.atomic():
        series.series_sheet(other, first["id"])


def test_http_sheet_history_permissions_and_owner_prices(documentary_tenant):
    org, other, users, foreign = documentary_tenant
    headers = {"HTTP_X_ORGANIZATION_ID": str(org)}
    owner = owner_client(users["OWNER"])
    response = owner.post("/api/v1/catalogs/series/", pro6004_input(), format="json", **headers)
    assert response.status_code == 201, response.data
    sheet = response.json()
    assert sheet["tabs"]["prices"]["can_view"] is True
    path = f"/api/v1/catalogs/series/{sheet['id']}/"
    estimator = owner_client(users["ESTIMATOR"])
    read = estimator.get(path, **headers)
    assert read.status_code == 200 and not read.json()["tabs"]["prices"]["can_view"]
    assert read.json()["tabs"]["prices"]["items"] == []
    assert estimator.post(path + "confirm/", {}, format="json", **headers).status_code == 403
    assert owner_client(users["INSTALLER"]).get(path, **headers).status_code == 403
    assert owner_client(foreign).get(path, HTTP_X_ORGANIZATION_ID=str(other)).status_code == 404
    cell = address(sheet)
    changed = owner.patch(path + "cells/", {"revision": sheet["revision"], "changes": [{**cell, "value": "4.75"}]}, format="json", **headers)
    assert changed.status_code == 200, changed.data
    history = estimator.get(path + "history/", {**cell, "row_id": str(cell["row_id"])}, **headers)
    assert history.status_code == 200, history.data
    assert history.json()["items"][0]["previous_value"] == "5.00"


def test_existing_reviews_append_confirmed_and_document_origins(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["WORKSHOP_MANAGER"]
    with as_user(actor):
        sheet = create(org, actor)
        system = sheet["tabs"]["rules"]
        service.review(service.SYSTEMS, org, sheet["id"], actor, expected_revision='"' + system["revision"] + '"')
        confirmed = cell_history(org, sheet["id"], "profile_systems", sheet["id"], "glass_clearance_white_mm")
        assert confirmed[0]["origin"] == "WORKSHOP" and confirmed[1]["origin"] == "SUGGESTED"
        profile = next(item for item in sheet["tabs"]["profiles"] if item["role"] == "FRAME")
        declared = evidence.declare_evidence(org_id=org, actor_id=actor, values={"authority_table": "profile_articles",
            "row_id": profile["id"], "field_name": "cut_rule.welding_loss_per_end_mm", "canonical_value": "3.00",
            "source_document": "Manual del taller.pdf", "source_page": 14, "extraction_method": "MANUAL"})
        evidence.review_evidence(org_id=org, evidence_id=declared["id"], actor_id=actor, state="REVIEWED")
        history = cell_history(org, sheet["id"], "profile_articles", profile["id"], "cut_rule.welding_loss_per_end_mm")
        assert history[0]["origin"] == "MANUAL" and history[0]["evidence_id"]
        assert history[1]["origin"] == "SUGGESTED"


def test_new_deleted_profiles_invalidate_verification_without_erasing_history(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet = create(org, actor)
        def verify():
            with catalog_backend():
                one("UPDATE public.catalog_series_setup SET verified_at=now(),verified_by=%s,verified_hash=%s "
                    "WHERE system_id=%s RETURNING system_id", [actor, "sha256:" + "a" * 64, sheet["id"]])
        verify()
        profile = service.create(service.ARTICLES, org, {"system_id": sheet["id"], "sku": "PRO-M",
            "name": "Travesaño", "role": "MULLION_V", "material": "PVC", "face_width_mm": Decimal("60")}, actor_id=actor)
        assert series.series_sheet(org, sheet["id"])["setup"]["verified_at"] is None
        verify()
        service.delete(service.ARTICLES, org, profile["id"], expected_revision='"' + profile["revision"] + '"')
        assert series.series_sheet(org, sheet["id"])["setup"]["verified_at"] is None
        assert series.history(org, sheet["id"], {"resource": "articles", "row_id": profile["id"], "field": "face_width_mm"})["items"]


def test_real_series_calculation_reports_only_consumed_suggestions(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet = create(org, actor)
        params = SystemParamsRepository().load_visible(sheet["id"], org)
        result = calculate_from_api(parametric_tree={"id": "B1", "type": "BAY", "opening_type": "TURN_LEFT",
            "glass_spec": "4-16-4", "glass_thickness_mm": "24", "glass_article_sku": "GLASS-24"},
            nominal_width_mm=Decimal("1200"), nominal_height_mm=Decimal("1100"), color="WHITE", params=params)
        assert result.profile_cuts and result.glasses and result.assumptions
        assert any(item.rule == "SYSTEM:glass_clearance_white_mm" for item in result.assumptions)
        assert not any("glass_clearance_foil_mm" in item.rule for item in result.assumptions)
        assert not any("face_width_mm" in item.rule for item in result.assumptions)
        suggested = [{key: cell[key] for key in ("resource", "row_id", "field")} for cell in sheet["cells"] if cell["origin"] == "SUGGESTED"]
        series.confirm_cells(org, sheet["id"], actor, {"revision": sheet["revision"], "cells": suggested})
        params = SystemParamsRepository().load_visible(sheet["id"], org)
        confirmed = calculate_from_api(parametric_tree={"id": "B1", "type": "BAY", "opening_type": "TURN_LEFT",
            "glass_spec": "4-16-4", "glass_thickness_mm": "24", "glass_article_sku": "GLASS-24"},
            nominal_width_mm=Decimal("1200"), nominal_height_mm=Decimal("1100"), color="WHITE", params=params)
        assert not confirmed.assumptions
        assert confirmed.profile_cuts == result.profile_cuts and confirmed.glasses == result.glasses
