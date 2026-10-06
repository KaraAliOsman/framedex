"""Populated D02 upgrade preserves exact saved and historical sealed evidence."""
import json
from decimal import Decimal
from pathlib import Path
import sys

import local_gates

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dekopen_engine import BayOpeningType, NodeType, ParametricNode, calculate_geometry  # noqa: E402
from dekopen_engine.snapshot import calculation_response  # noqa: E402
from engine.tests.catalog import demo_60_params  # noqa: E402
FIRST_D02 = "20261230000000_glass_composition_and_rules.sql"
FIRST_DOCUMENTARY = "20260914000000_shot_09_documentary.sql"


def verify(container: str) -> None:
    database = "glass_upgrade"
    docker = local_gates.executable("docker")

    def sql(source, *, db=database):
        return local_gates.run([docker, "exec", "-i", container, "psql", "-X", "-A", "-t",
            "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", db], input_text=source, capture=True)

    sql(f"CREATE DATABASE {database}", db="postgres")
    bootstrap = (ROOT / "supabase/compat/postgres16_bootstrap.sql").read_text(encoding="utf-8")
    sql(bootstrap[bootstrap.index("CREATE SCHEMA auth;"):])
    migrations = sorted((ROOT / "supabase/migrations").glob("*.sql"))
    sql("\n".join(p.read_text(encoding="utf-8") for p in migrations if p.name < FIRST_DOCUMENTARY))
    # Legitimate issued authority under its original schema. Later gates keep it
    # historical instead of manufacturing modern authority or overwriting it.
    sql("""
        INSERT INTO public.tenancy_organizations(id,name,tax_id)
          VALUES('d0200000-0000-4000-8000-000000000001','D02 upgrade','UP-D02');
        INSERT INTO public.projects(id,org_id,code,name,client_name,created_by)
          VALUES('d0200000-0000-4000-8000-000000000002','d0200000-0000-4000-8000-000000000001',
          'UP-D02','Historical glass project','Fixture','d0200000-0000-4000-8000-000000000003');
        INSERT INTO public.project_versions(id,project_id,org_id,revision_code,snapshot_json,pdf_storage_path,emitted_by)
          VALUES('d0200000-0000-4000-8000-000000000004','d0200000-0000-4000-8000-000000000002',
          'd0200000-0000-4000-8000-000000000001','R0',
          '{"glass_spec":"3+3 especial","legacy_bom":{"cut_mm":"812.25","hash":"original"}}',
          'legacy/glass-r0.pdf','d0200000-0000-4000-8000-000000000003');
    """)
    sql("\n".join(p.read_text(encoding="utf-8") for p in migrations if FIRST_DOCUMENTARY <= p.name < FIRST_D02))
    sql((ROOT / "supabase/seed.sql").read_text(encoding="utf-8"))
    # Two real old mappings, one parseable and one requiring human review.
    sql("""
        INSERT INTO public.glass_purchase_mappings(id,system_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version,glass_spec,provenance)
          SELECT v.id::uuid,s.id,v.sku,v.sku,'Historical supplier','EA',1,v.spec,'{"source":"Historical supplier sheet"}'::jsonb
          FROM public.profile_systems s CROSS JOIN (VALUES
          ('d0200000-0000-4000-8000-000000000005','UP-D02-PARSED',' DVH 5-12-5 '),
          ('d0200000-0000-4000-8000-000000000006','UP-D02-UNKNOWN','especial sin ficha'),
          ('d0200000-0000-4000-8000-000000000007','UP-D02-PVB','3+3')) v(id,sku,spec)
          WHERE s.code='DEMO_60' AND s.version=1;
    """)
    tree = {"id": "B1", "type": "BAY", "opening_type": "FIXED", "glass_spec": "4-12-4 Float Incoloro", "glass_thickness_mm": "24.00"}
    request = {"system_id": "3067da09-3119-5ad0-a1d5-498cd2dfd753", "nominal_width_mm": "1000.00", "nominal_height_mm": "1400.00", "color": "WHITE", "parametric_tree": tree}
    node = ParametricNode(id="B1", type=NodeType.BAY, width_mm=Decimal("1000.00"), height_mm=Decimal("1400.00"),
        opening_type=BayOpeningType.FIXED, glass_spec=tree["glass_spec"], glass_thickness_mm=Decimal("24.00"))
    bom = calculation_response(request, calculate_geometry(node, demo_60_params()))
    def literal(value):
        return "'" + json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("'", "''") + "'::jsonb"
    sql(f"""
        INSERT INTO public.project_positions(id,project_id,org_id,position_index,typology,system_id,width_mm,height_mm,parametric_tree,bom_snapshot)
          SELECT 'd0200000-0000-4000-8000-000000000008','d0200000-0000-4000-8000-000000000002',
          'd0200000-0000-4000-8000-000000000001',1,'FIXED',s.id,1000,1400,
          {literal(tree)}, {literal(bom)}
          FROM public.profile_systems s WHERE s.code='DEMO_60' AND s.version=1;
    """)
    tables = ["projects", "project_positions", "project_versions", "glass_purchase_mappings",
              "pricing_operations", "document_artifacts"]
    def snapshot():
        return {table: sql(f"SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY id),'[]')::text FROM public.{table} t;").strip()
                for table in tables}
    before = snapshot()
    sql("\n".join(p.read_text(encoding="utf-8") for p in migrations if p.name >= FIRST_D02))
    after = snapshot()
    for table in tables:
        # D02 adds synthetic global glass SKUs; every prior row is byte-identical.
        prior = {row["id"]: row for row in json.loads(before[table])}
        current = {row["id"]: row for row in json.loads(after[table])}
        assert prior.keys() <= current.keys()
        assert all(current[key] == row for key, row in prior.items()), table
    recipes = json.loads(sql("SELECT jsonb_agg(jsonb_build_object('sku',g.technical_sku,'status',c.status,'product',c.product,'reason',c.review_reason)) "
        "FROM public.catalog_glass_compositions c JOIN public.glass_purchase_mappings g ON g.id=c.mapping_id "
        "WHERE g.technical_sku LIKE 'UP-D02-%';"))
    by_sku = {row["sku"]: row for row in recipes}
    assert by_sku["UP-D02-PARSED"]["status"] == "PARSED"
    assert by_sku["UP-D02-PARSED"]["product"]["composition"]["layers"][1]["width_mm"] == "12"
    assert by_sku["UP-D02-UNKNOWN"]["status"] == "UNKNOWN" and by_sku["UP-D02-UNKNOWN"]["product"] is None
    assert by_sku["UP-D02-UNKNOWN"]["reason"]
    assert by_sku["UP-D02-PVB"]["product"]["composition"]["layers"][0]["interlayers"] == [{}]
    print("  D02 populated upgrade: saved BOM/hash, historical revision, all old mappings and price/artifact history preserved; UNKNOWN/PVB honest PASS", flush=True)
