"""Two simulated model reads for the owned catalog browser fixture.

The browser still uses real review/publication APIs, PostgreSQL and storage.
This fixture makes no claim about manufacturer data or real-provider quality.
"""

from copy import deepcopy
import json
from uuid import uuid4

from documents.storage import SupabaseDocumentStorage
from documents.repository import documentary_backend
from ingest import catalog_ai
from ingest.catalog_double_read import compare_reads
from pricing.repository import one, json_text


def seed_manual(org, actor, sheet):
    filename = "manual-doble-lectura-sintetico.txt"
    records, text = [], []
    profiles = [row for row in sheet["tabs"]["profiles"] if row["role"] in ("FRAME", "SASH")]
    for profile in profiles:
        values = {**profile["cut_rule"], "system_code": sheet["tabs"]["rules"]["code"],
                  "sku": profile["sku"], "role": profile["role"]}
        values = {key: str(value) for key, value in values.items()}
        evidence = {key: {"ref": "página 1", "quote": f"{profile['sku']} {key}: {value}",
                          "literal": value, "confidence": "HIGH"} for key, value in values.items()}
        text.extend(item["quote"] for item in evidence.values())
        records.append({"sheet": "Roles y reglas de corte", "values": values, "evidence": evidence})
    first = {"records": records}
    second = deepcopy(first)
    second["records"][0]["values"]["welding_loss_per_end_mm"] = "4.00"
    quote = f"{profiles[0]['sku']} soldadura alternativa: 4.00"
    second["records"][0]["evidence"]["welding_loss_per_end_mm"].update({"quote": quote, "literal": "4.00"})
    text.append(quote)
    source = "Ensayo sintético: dos lecturas simuladas.\n" + "\n".join(text)
    reads = [catalog_ai.parse_response(json.dumps(reading), tagged=[(source, "página 1")], file_name=filename)
             for reading in (first, second)]
    candidates = compare_reads(*reads, file_name=filename, audit_ids=[uuid4(), uuid4()])
    assert len(candidates) == 2
    assert candidates[0]["double_read"]["review_fields"] == ["welding_loss_per_end_mm"]
    assert not candidates[1]["double_read"]["review_fields"]
    import_id = uuid4()
    path = f"catalog-imports/{org}/{import_id}/{filename}"
    SupabaseDocumentStorage().upload_immutable(path, source.encode(), "text/plain")
    with documentary_backend():
        one("INSERT INTO public.catalog_imports(id,org_id,file_name,kind,storage_path,created_by,status,candidates,contains_costs) "
            "VALUES(%s,%s,%s,'TEXT',%s,%s,'REVIEW_READY',%s::jsonb,TRUE) RETURNING id",
            [import_id, org, filename, path, actor, json_text(candidates)])
    return {"manualImportId": str(import_id), "manualArticleId": str(profiles[0]["id"]), "manualSku": profiles[0]["sku"]}
