"""Tenant goldens seal real engine output and protect every catalog write path."""

from decimal import Decimal as D
from copy import deepcopy

from django.db import DatabaseError, transaction
import pytest

from authentication.errors import ContractAPIException
from catalogs import reference_windows as windows, series, service
from catalogs.reference_protection import protect_changes
from catalogs.use_levels import require_use, series_use
from pricing.repository import one

from .test_catalog_series_sheet import address
from .test_catalog_interchange import imported
from .test_catalog_use_levels import priced_series, tree
from .test_shot08_pricing import owner_client
from .test_shot09_documentary import as_user, documentary_tenant as documentary_tenant

pytestmark = pytest.mark.rls_integration


def request_data():
    return {"parametric_tree": tree(), "nominal_width_mm": D("1200"), "nominal_height_mm": D("1100"), "color": "WHITE"}


def verified(org, actor):
    sheet = priced_series(org, actor)
    trial = windows.trial(org, sheet["id"], request_data())
    reference = windows.verify(org, sheet["id"], actor, {**request_data(), "revision": sheet["revision"],
        "calculation_token": trial["calculation_token"], "confirmed": True, "confirm_suggested": True})
    return series.series_sheet(org, sheet["id"]), reference


def test_human_confirmation_seals_engine_output_and_reaches_manufacturable(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet, reference = verified(org, actor)
        assert require_use(org, sheet["id"], "MANUFACTURABLE")["verified"]
        saved = windows.references(org, sheet["id"])
        assert len(saved) == 1 and saved[0]["id"] == reference["id"]
        assert saved[0]["input"]["nominal_width_mm"] == "1200"
        assert saved[0]["expected_output"]["profile_cuts"][0]["length_mm"] == "1206.00"
        assert "assumptions" not in saved[0]["expected_output"]
        assert windows.progress(org, sheet["id"])["step"] == 5


def test_differences_and_stale_calculations_never_stamp_verification(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet = priced_series(org, actor)
        calculated = windows.trial(org, sheet["id"], request_data())
        base = {**request_data(), "revision": sheet["revision"], "calculation_token": calculated["calculation_token"], "confirmed": True}
        for changed in ({"manual_values": {"profile_cuts:0:length_mm": D("1207")}},
                {"nominal_width_mm": D("1201")}, {"calculation_token": "tampered"}, {"confirmed": False}):
            with pytest.raises(ContractAPIException), transaction.atomic():
                windows.verify(org, sheet["id"], actor, {**base, **changed})
        assert not windows.references(org, sheet["id"])
        assert not series_use(org, sheet["id"])["verified"]


def test_rule_correction_recalculates_then_seals_the_exact_new_window(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet = priced_series(org, actor)
        original = windows.trial(org, sheet["id"], request_data())
        sash = next(row for row in original["measurements"] if row["role"] == "SASH")
        target = D(sash["value_mm"]) + D("2")
        proposals = windows.proposals(org, sheet["id"], {**request_data(), "measurement_key": sash["key"], "target_mm": target})
        selected = next(item for item in proposals["items"] if item["change"]["field"] == "sash_overlap_mm")
        sheet = series.edit_cells(org, sheet["id"], actor, {"revision": proposals["revision"], "changes": [selected["change"]]})
        data = {**request_data(), "manual_values": {sash["key"]: target}}
        recalculated = windows.trial(org, sheet["id"], data)
        assert next(row for row in recalculated["measurements"] if row["key"] == sash["key"])["matches"]
        windows.verify(org, sheet["id"], actor, {**data, "revision": sheet["revision"], "calculation_token": recalculated["calculation_token"],
            "confirmed": True, "confirm_suggested": True})
        assert require_use(org, sheet["id"], "MANUFACTURABLE")["verified"]


def test_proposals_also_respect_the_catalog_storage_constraints(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet = priced_series(org, actor)
        trial = windows.trial(org, sheet["id"], request_data())
        bead = next(row for row in trial["measurements"] if row["role"] == "GLAZING_BEAD")
        proposals = windows.proposals(org, sheet["id"], {**request_data(), "measurement_key": bead["key"],
            "target_mm": D(bead["value_mm"]) - D("30")})
        assert proposals["items"] == []  # The catalog's bead addition cannot be negative.


def test_protected_sheet_edit_rolls_back_and_requires_exact_review_token(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet, _ = verified(org, actor)
        original = deepcopy(windows.references(org, sheet["id"]))
        change = {**address(sheet, field="sash_overlap_mm"), "value": "9"}
        data = {"revision": sheet["revision"], "changes": [change]}
        with pytest.raises(ContractAPIException) as raised:
            series.edit_cells(org, sheet["id"], actor, data)
        assert raised.value.contract_code == "catalog_reference_changed"
        review = raised.value.extra["golden_review"]
        assert review["changes"][0]["before"] != review["changes"][0]["after"]
        assert series.series_sheet(org, sheet["id"])["revision"] == sheet["revision"]
        for invalid_data, token in ((data, "tampered"), ({**data, "changes": [{**change, "value": "10"}]}, review["review_token"])):
            with pytest.raises(ContractAPIException), protect_changes(org, token):
                series.edit_cells(org, sheet["id"], actor, invalid_data)
        with protect_changes(org, review["review_token"]):
            series.edit_cells(org, sheet["id"], actor, data)
        assert not series_use(org, sheet["id"])["verified"]
        assert windows.references(org, sheet["id"]) == original


def test_direct_resource_update_cannot_bypass_reference_review(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet, _ = verified(org, actor)
        current = service.retrieve(service.SYSTEMS, org, sheet["id"])
        with pytest.raises(ContractAPIException) as raised:
            service.update(service.SYSTEMS, org, sheet["id"], {"sash_overlap_mm": D("9")},
                expected_revision='"' + current["revision"] + '"', actor_id=actor)
        assert raised.value.contract_code == "catalog_reference_changed"
        assert service.retrieve(service.SYSTEMS, org, sheet["id"])["sash_overlap_mm"] == current["sash_overlap_mm"]


def test_multirow_batch_compares_the_final_window_and_ignores_cancelled_intermediate_changes(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet, _ = verified(org, actor)
        sash = next(row for row in sheet["tabs"]["profiles"] if row["role"] == "SASH")
        # An outer publication may contain compensating rule edits. The final
        # full window, including glass, changes here, so it still needs review.
        with pytest.raises(ContractAPIException), protect_changes(org):
            series.edit_cells(org, sheet["id"], actor, {"revision": sheet["revision"], "changes": [
                {**address(sheet, field="sash_overlap_mm"), "value": "9"},
                {"resource": "articles", "row_id": sash["id"], "field": "cut_rule.welding_loss_per_end_mm", "value": "2"}]})
        with protect_changes(org):
            first = service.retrieve(service.SYSTEMS, org, sheet["id"])
            updated = service.update(service.SYSTEMS, org, sheet["id"], {"sash_overlap_mm": D("9")},
                expected_revision='"' + first["revision"] + '"', actor_id=actor)
            service.update(service.SYSTEMS, org, sheet["id"], {"sash_overlap_mm": D("8")},
                expected_revision='"' + updated["revision"] + '"', actor_id=actor)


def test_reference_is_immutable_and_foreign_tenant_cannot_read_it(documentary_tenant):
    org, other, users, foreign = documentary_tenant
    with as_user(users["OWNER"]):
        sheet, reference = verified(org, users["OWNER"])
    for statement in ("UPDATE public.catalog_reference_windows SET expected_output='{}' WHERE id=%s",
            "DELETE FROM public.catalog_reference_windows WHERE id=%s"):
        with pytest.raises(DatabaseError), transaction.atomic():
            one(statement + " RETURNING id", [reference["id"]])
    with as_user(foreign):
        assert one("SELECT count(*) AS count FROM public.catalog_reference_windows WHERE org_id=%s", [org])["count"] == 0
        with pytest.raises(ContractAPIException):
            windows.references(other, sheet["id"])


def test_progress_is_tenant_scoped_resumable_and_optimistic(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet = priced_series(org, actor)
        previous = windows.progress(org, sheet["id"])
        saved = windows.progress(org, sheet["id"], {"step": 4, "revision": previous["revision"], "state": {"trial": request_data()}})
        assert saved["revision"] == previous["revision"] + 1
        assert windows.progress(org, sheet["id"])["state"]["trial"]["nominal_width_mm"] == "1200"
        with pytest.raises(ContractAPIException):
            windows.progress(org, sheet["id"], {"step": 2, "revision": previous["revision"], "state": {}})


@pytest.mark.parametrize("saved_progress", [False, True])
def test_verification_invalidates_older_progress_without_losing_saved_state(documentary_tenant, saved_progress):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet = priced_series(org, actor)
        previous = windows.progress(org, sheet["id"])
        if saved_progress:
            previous = windows.progress(org, sheet["id"], {"step": 4, "revision": previous["revision"],
                "state": {"prices_file_name": "precios.xlsx"}})
        trial = windows.trial(org, sheet["id"], request_data())
        windows.verify(org, sheet["id"], actor, {**request_data(), "revision": sheet["revision"],
            "calculation_token": trial["calculation_token"], "confirmed": True, "confirm_suggested": True})
        current = windows.progress(org, sheet["id"])
        assert current["step"] == 5 and current["revision"] == previous["revision"] + 1
        assert current["state"] == previous["state"]
        with pytest.raises(ContractAPIException) as raised:
            windows.progress(org, sheet["id"], {"step": 2, "revision": previous["revision"], "state": {}})
        assert raised.value.contract_code == "catalog_progress_stale"
        assert windows.progress(org, sheet["id"]) == current


def test_api_enforces_role_and_does_not_accept_client_expected_output(documentary_tenant):
    org, _, users, _ = documentary_tenant
    with as_user(users["OWNER"]):
        sheet = priced_series(org, users["OWNER"])
    path = f"/api/v1/catalogs/series/{sheet['id']}/trial/"
    data = {**request_data(), "nominal_width_mm": "1200", "nominal_height_mm": "1100"}
    headers = {"HTTP_X_ORGANIZATION_ID": str(org)}
    for role in ("OWNER", "WORKSHOP_MANAGER", "ESTIMATOR"):
        response = owner_client(users[role]).post(path, data, format="json", **headers)
        assert response.status_code == 200, response.data
    assert owner_client(users["INSTALLER"]).post(path, data, format="json", **headers).status_code == 403
    assert owner_client(users["OWNER"]).post(path, {**data, "expected_output": {}}, format="json", **headers).status_code == 400
    assert owner_client(users["ESTIMATOR"]).post(path + "verify/", {**data, "confirmed": True}, format="json", **headers).status_code == 403


def test_http_review_header_confirms_only_the_change_the_human_reviewed(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet, _ = verified(org, actor)
    client = owner_client(actor)
    path = f"/api/v1/catalogs/series/{sheet['id']}/cells/"
    data = {"revision": sheet["revision"], "changes": [{**address(sheet, field="sash_overlap_mm"), "value": "9"}]}
    headers = {"HTTP_X_ORGANIZATION_ID": str(org)}
    blocked = client.patch(path, data, format="json", **headers)
    assert blocked.status_code == 409, blocked.data
    review = blocked.json()["golden_review"]
    assert review["changes"][0]["before"]["measurements"]
    accepted = client.patch(path, data, format="json", HTTP_X_CATALOG_REVIEW=review["review_token"], **headers)
    assert accepted.status_code == 200, accepted.data
    assert not accepted.json()["usage"]["verified"]


def test_reviewed_import_cannot_bypass_the_same_reference_confirmation(documentary_tenant):
    from ingest import catalog_review
    from ingest.catalog_template import candidate

    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet, _ = verified(org, actor)
    sash = next(row for row in sheet["tabs"]["profiles"] if row["role"] == "SASH")
    entry = candidate("Roles y reglas de corte", {**sash["cut_rule"], "system_code": sheet["tabs"]["rules"]["code"],
        "sku": sash["sku"], "role": "SASH", "welding_loss_per_end_mm": "4", "source": "Manual sintético · página 1"},
        key="cut1", row=2, method="XLSX")
    import_id, items = imported(org, actor, [entry])
    with as_user(actor):
        diff = catalog_review.preview(org_id=org, import_id=import_id, items=items)
        assert not diff["errors"], diff["errors"]
        with pytest.raises(ContractAPIException) as raised:
            catalog_review.publish(org_id=org, actor_id=actor, import_id=import_id, items=items, review_token=diff["review_token"])
        assert raised.value.contract_code == "catalog_reference_changed"
        assert one("SELECT status FROM public.catalog_imports WHERE id=%s", [import_id])["status"] == "REVIEW_READY"
        with protect_changes(org, raised.value.extra["golden_review"]["review_token"]):
            result = catalog_review.publish(org_id=org, actor_id=actor, import_id=import_id, items=items, review_token=diff["review_token"])
        assert not result["errors"]
        assert len(windows.references(org, sheet["id"])) == 1
