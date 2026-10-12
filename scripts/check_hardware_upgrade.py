"""Populated D04 upgrade preserves prior BOMs, price history and sealed bytes."""
import json
from pathlib import Path
import sys

import local_gates

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dekopen_engine.models import BayOpeningType as B  # noqa: E402
from dekopen_engine.geometry import calculate_geometry  # noqa: E402
from dekopen_engine.snapshot import calculation_response  # noqa: E402
from engine.tests.catalog import demo_60_params  # noqa: E402
from engine.tests.test_gold_cases_catalog_families import node  # noqa: E402

FIRST_D04 = "20270101000000_hardware_classes.sql"
FIRST_DOCUMENTARY = "20260914000000_shot_09_documentary.sql"
ORG = "d0400000-0000-4000-8000-000000000001"
ACTOR = "d0400000-0000-4000-8000-000000000002"
SYSTEM = "3067da09-3119-5ad0-a1d5-498cd2dfd753"


def verify(container: str) -> None:
    database = "hardware_upgrade"
    docker = local_gates.executable("docker")
    def sql(source, *, db=database):
        return local_gates.run([docker, "exec", "-i", container, "psql", "-X", "-A", "-t",
            "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", db], input_text=source, capture=True)
    def literal(value):
        return "'" + json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("'", "''") + "'::jsonb"
    sql(f"CREATE DATABASE {database}", db="postgres")
    bootstrap = (ROOT / "supabase/compat/postgres16_bootstrap.sql").read_text(encoding="utf-8")
    sql(bootstrap[bootstrap.index("CREATE SCHEMA auth;"):])
    migrations = sorted((ROOT / "supabase/migrations").glob("*.sql"))
    sql("\n".join(p.read_text(encoding="utf-8") for p in migrations if p.name < FIRST_DOCUMENTARY))
    # A legitimate revision under its historical schema, before modern seals.
    sql(f"""INSERT INTO public.tenancy_organizations(id,name,tax_id) VALUES('{ORG}','D04 upgrade DEMO','D04-UP');
        INSERT INTO public.tenancy_memberships(org_id,user_id,role) VALUES('{ORG}','{ACTOR}','OWNER');
        INSERT INTO public.projects(id,org_id,code,name,client_name,created_by)
          VALUES('d0400000-0000-4000-8000-000000000003','{ORG}','UP-D04','Historical opening','Fixture','{ACTOR}');
        INSERT INTO public.project_versions(id,project_id,org_id,revision_code,snapshot_json,pdf_storage_path,emitted_by)
          VALUES('d0400000-0000-4000-8000-000000000004','d0400000-0000-4000-8000-000000000003',
          '{ORG}','R0','{{"opening_type":"TURN_LEFT","legacy_bom":{{"cut_mm":"812.25","hash":"original"}}}}',
          'legacy/opening-r0.pdf','{ACTOR}');""")
    sql("\n".join(p.read_text(encoding="utf-8") for p in migrations if FIRST_DOCUMENTARY <= p.name < FIRST_D04))
    sql((ROOT / "supabase/seed.sql").read_text(encoding="utf-8"))
    for index, kind in enumerate((k for k in B if k not in (B.DOOR_DOUBLE, B.SLIDING)), 1):
        old = node(kind, "1800" if kind.value.startswith("SLIDING") else "1000",
            "2200" if kind is B.DOOR_ENTRY else "900" if kind is B.AWNING else "1400")
        if kind is B.DOOR_ENTRY:
            old = old.model_copy(update={"panel_article_sku": "PANEL-SANDWICH-DEMO-24"})
        tree = old.model_dump(mode="json", exclude_none=True)
        width, height = tree.pop("width_mm"), tree.pop("height_mm")
        request = {"system_id": SYSTEM, "nominal_width_mm": width, "nominal_height_mm": height,
            "color": "WHITE", "parametric_tree": tree}
        bom = calculation_response(request, calculate_geometry(old, demo_60_params()))
        sql("INSERT INTO public.project_positions(id,project_id,org_id,position_index,typology,system_id,width_mm,height_mm,parametric_tree,bom_snapshot) "
            f"VALUES('d0400000-0000-4000-8001-{index:012d}','d0400000-0000-4000-8000-000000000003',"
            f"'{ORG}',{index},'{kind.value}','{SYSTEM}',{width},{height},{literal(tree)},{literal(bom)});")
    # Explicit already-applied commercial evidence; no recalculation at upgrade.
    sql("BEGIN; SELECT set_config('request.jwt.claims'," + literal({"sub": ACTOR, "aal": "aal2", "role": "authenticated"}) + "::text,true);"
        f"SELECT set_config('request.jwt.claim.sub','{ACTOR}',true);"
        "SELECT set_config('app.pricing_reason','Historical D04 synthetic price fixture',true); SET LOCAL ROLE pricing_backend;"
        "UPDATE public.projects SET total_cost_net=12345.6789,total_price_net=18993.3522 "
        "WHERE id='d0400000-0000-4000-8000-000000000003'; COMMIT;")
    tables = ["projects", "project_positions", "project_versions", "pricing_operations", "price_audit_logs",
        "document_artifacts", "profile_systems", "profile_articles", "hardware_kits", "catalog_demo_prices"]
    def snapshot():
        return {table: json.loads(sql(f"SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY id),'[]')::text FROM public.{table} t;"))
            for table in tables}
    before = snapshot()
    sql("\n".join(p.read_text(encoding="utf-8") for p in migrations if p.name >= FIRST_D04))
    after = snapshot()
    for table in tables:
        current = {row["id"]: row for row in after[table]}
        for row in before[table]:
            # Additive NULL columns may exist, but every old field stays exact.
            assert all(current[row["id"]][key] == value for key, value in row.items()), table
    assert len(before["project_positions"]) == 10
    print("  D04 populated PG16 upgrade: ten pre-class typologies, exact BOM/hash, applied money, issued snapshot and old catalog unchanged PASS", flush=True)
