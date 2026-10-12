"""Generate only additive P06 authority and v7 catalog/seed migrations."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "engine/src")]
from dekopen_engine.models import CouplerRule  # noqa: E402
from backend.catalogs.demo_couplings import coupling_manifest  # noqa: E402
from scripts.generate_demo_extras import extra_sql, extra_seed_sql  # noqa: E402


def schema_sql():
    schema = json.dumps(CouplerRule.model_json_schema(), sort_keys=True).replace("'", "''")
    return (ROOT / "scripts/coupling_schema.sql").read_text().replace("__SCHEMA__", schema)


def catalog_sql():
    return extra_sql(coupling_manifest(), version=7)


def seed_sql():
    return extra_seed_sql().replace("-- D06 generated documentary seed; see scripts/generate_demo_extras.py.",
        "-- P06 generated documentary seed; see scripts/generate_demo_couplings.py.").replace(
        "d06_seed", "p06_seed").replace("catalog/v6/", "catalog/v7/").replace("s.version=6", "s.version=7").replace("_DEMO_V6", "_DEMO_V7")


if __name__ == "__main__":
    (ROOT / "supabase/migrations/20270113000000_coupling_authority.sql").write_text(schema_sql(), encoding="utf-8", newline="\n")
    (ROOT / "supabase/migrations/20270113000100_demo_coupling_catalog.sql").write_text(catalog_sql(), encoding="utf-8", newline="\n")
    marker = "-- P06 generated documentary seed; see scripts/generate_demo_couplings.py."
    seed = ROOT / "supabase/seed.sql"
    content = seed.read_text(encoding="utf-8").split(marker, 1)[0].rstrip()
    seed.write_text(content+"\n\n"+seed_sql(), encoding="utf-8", newline="\n")
    print("P06 exact joint authority and additive v7 catalogs generated.")
