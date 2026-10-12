"""Reproducible, additive D03 catalog versions. Never rewrites the v2 seed."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.catalogs.demo_openings import opening_manifest  # noqa: E402
from backend.catalogs.demo_glass import demo_glass_product, demo_glass_rates, SOURCE  # noqa: E402
from scripts.generate_demo_catalog import generated_sql, insert, uid, shared_demo_price  # noqa: E402

MIGRATION = ROOT / "supabase/migrations/20261231000100_demo_opening_catalog.sql"


def opening_sql() -> str:
    records = opening_manifest()
    sql = generated_sql(records, version=3).removesuffix("COMMIT;\n")
    sql = sql.replace("scripts/generate_demo_catalog.py", "scripts/generate_demo_openings.py")
    additions = []
    for record in records:
        code = record["code"]
        system_id = uid(code, version=3)
        for kind in ("SAFE", "LOWE"):
            sku = f"{code}-GLASS-{kind}"
            mapping_id = uid(code, sku, version=3)
            product = demo_glass_product(code, kind)
            additions.append(insert("glass_purchase_mappings", {"id": mapping_id,
                "org_id": None, "system_id": system_id, "technical_sku": sku,
                "purchasing_sku": sku, "manufacturer_name": "Vidriero sintético · DEMO",
                "purchase_unit": "EA", "version": 1,
                "glass_spec": "3+3 PVB 0,38 / 13,62 aire aluminio / 4 templado" if kind == "SAFE"
                    else "4 / 16 Ar borde cálido / 4 Low-E (c3)", "provenance": {"source": SOURCE}}))
            additions.append(insert("catalog_glass_compositions", {
                "id": uid(code, "composition/" + sku, version=3), "org_id": None,
                "system_id": system_id, "mapping_id": mapping_id, "status": "PARSED",
                "product": product.model_dump(mode="json")}))
        for sku, unit, rate in demo_glass_rates(code):
            additions.append(shared_demo_price({"id": uid(code, "price/" + sku, version=3),
                "org_id": None, "system_id": system_id, "sku": sku, "unit": unit,
                "unit_cost": rate, "seed": 20261230, "source": SOURCE, "is_demo": True,
                "currency": "CLP"}))
    return sql + "\n" + "\n".join(additions) + "\nCOMMIT;\n"


if __name__ == "__main__":
    MIGRATION.write_text(opening_sql(), encoding="utf-8", newline="\n")
    print("D03 additive demo versions reproduced; all authorities are synthetic.")
