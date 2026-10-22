"""No extracted number becomes a catalog value before human publication."""

from copy import deepcopy
from decimal import Decimal
from uuid import uuid4
import json

import pytest

from catalogs import service
from ingest import catalog_ai, catalog_review
from ingest.catalog_double_read import compare_reads
from pricing.repository import one

from .test_catalog_interchange import imported
from .test_catalog_use_levels import priced_series
from .test_shot09_documentary import as_user, documentary_tenant as documentary_tenant

pytestmark = pytest.mark.rls_integration


def test_discrepant_reading_requires_review_and_only_cited_choice_becomes_manual(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet = priced_series(org, actor)
    sash = next(row for row in sheet["tabs"]["profiles"] if row["role"] == "SASH")
    values = {**sash["cut_rule"], "system_code": sheet["tabs"]["rules"]["code"], "sku": sash["sku"], "role": "SASH"}
    values = {key: str(value) for key, value in values.items()}
    evidence = {key: {"ref": "página 1", "quote": f"{key}: {value}", "literal": value, "confidence": "HIGH"}
        for key, value in values.items()}
    first = {"records": [{"sheet": "Roles y reglas de corte", "values": values, "evidence": evidence}]}
    second = deepcopy(first)
    second["records"][0]["values"]["welding_loss_per_end_mm"] = "4.00"
    second["records"][0]["evidence"]["welding_loss_per_end_mm"].update({"quote": "Soldadura alternativa: 4.00", "literal": "4.00"})
    tagged = [(". ".join(item["quote"] for item in evidence.values()) + ". Soldadura alternativa: 4.00", "página 1")]
    reads = [catalog_ai.parse_response(json.dumps(output), tagged=tagged, file_name="manual-sintetico.pdf") for output in (first, second)]
    candidates = compare_reads(*reads, file_name="manual-sintetico.pdf", audit_ids=[uuid4(), uuid4()])
    import_id, items = imported(org, actor, candidates)
    with as_user(actor):
        assert service.retrieve(service.ARTICLES, org, sash["id"])["cut_rule"]["welding_loss_per_end_mm"] == Decimal("3")
        diff = catalog_review.preview(org_id=org, import_id=import_id, items=items)
        assert diff["errors"]  # A discrepant required cell cannot publish.
        items[0]["values"]["welding_loss_per_end_mm"] = "4.00"
        reviewed = catalog_review.preview(org_id=org, import_id=import_id, items=items)
        assert not reviewed["errors"], reviewed["errors"]
        assert service.retrieve(service.ARTICLES, org, sash["id"])["cut_rule"]["welding_loss_per_end_mm"] == Decimal("3")
        published = catalog_review.publish(org_id=org, actor_id=actor, import_id=import_id, items=items, review_token=reviewed["review_token"])
        assert not published["errors"]
        row = one("SELECT origin,source_ref FROM public.catalog_value_history WHERE org_id=%s AND row_id=%s "
            "AND field_name='cut_rule.welding_loss_per_end_mm' ORDER BY version DESC LIMIT 1", [org, sash["id"]])
        assert row["origin"] == "MANUAL" and "página 1" in row["source_ref"]
        saved = one("SELECT candidates::text FROM public.catalog_import_publications WHERE import_id=%s", [import_id])
        assert json.loads(saved["candidates"])[0]["fields"]["welding_loss_per_end_mm"]["comparison"] == "HUMAN_RESOLVED"
