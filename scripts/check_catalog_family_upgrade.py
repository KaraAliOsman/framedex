"""Populated D01 upgrade: preserve manufacturing and sealed authorities on PG16."""
from decimal import Decimal as D
import json
from pathlib import Path
import sys
from uuid import UUID, uuid5

import local_gates

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dekopen_engine import BayOpeningType, NodeType, ParametricNode, SystemFamily, calculate_geometry  # noqa: E402
from dekopen_engine.snapshot import calculation_hash, calculation_response  # noqa: E402
from engine.tests.catalog import demo_60_params  # noqa: E402

FIRST_D01 = "20261229000000_catalog_profile_roles.sql"
SYSTEM = "3067da09-3119-5ad0-a1d5-498cd2dfd753"
ORG = "dc010000-0000-4000-8000-000000000001"
ACTOR = "dc010000-0000-4000-8000-000000000002"
NAMESPACE = UUID("df168df1-7f3e-4e41-a244-a77dfe5ff101")


def verify(container: str) -> None:
    database = "catalog_family_upgrade"
    docker = local_gates.executable("docker")

    def sql(source: str, *, db=database, capture=False):
        return local_gates.run([docker, "exec", "-i", container, "psql", "-X", "-A", "-t",
            "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", db], input_text=source, capture=capture)

    def literal(value):
        return "'" + json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("'", "''") + "'::jsonb"

    sql(f"CREATE DATABASE {database}", db="postgres")
    bootstrap = (ROOT / "supabase/compat/postgres16_bootstrap.sql").read_text(encoding="utf-8")
    sql(bootstrap[bootstrap.index("CREATE SCHEMA auth;"):])
    migrations = sorted((ROOT / "supabase/migrations").glob("*.sql"))
    sql("\n".join(path.read_text(encoding="utf-8") for path in migrations if path.name < FIRST_D01))
    sql((ROOT / "supabase/seed.sql").read_text(encoding="utf-8"))
    sql(f"INSERT INTO public.tenancy_organizations(id,name,tax_id) VALUES('{ORG}','Upgrade D01','D01-UP');"
        f"INSERT INTO public.tenancy_memberships(org_id,user_id,role) VALUES('{ORG}','{ACTOR}','OWNER');")
    cases = [("fixed", "FIXED", "CASEMENT"), ("turn", "TURN_LEFT", "CASEMENT"),
        ("sliding", "SLIDING_2L", "SLIDING"), ("door", "DOOR_ENTRY", "DOOR"),
        ("mixed", "FIXED", None), ("commercial", "SLIDING_2L", None), ("issued", "SLIDING_2L", None)]
    saved = {}
    for index, (key, opening, family) in enumerate(cases, start=1):
        width, height = "1000.00", "2200.00" if key == "door" else "1400.00"
        project = f"dc010000-0000-4000-8001-{index:012d}"
        position = f"dc010000-0000-4000-8002-{index:012d}"
        tree = {"id": "B1", "type": "BAY", "opening_type": opening,
            "glass_spec": "4-12-4 Float Incoloro", "glass_thickness_mm": "24.00"}
        if key == "door":
            tree["panel_article_sku"] = "PANEL-SANDWICH-DEMO-24"
        params = demo_60_params()
        node = ParametricNode(id="B1", type=NodeType.BAY, width_mm=D(width), height_mm=D(height),
            opening_type=BayOpeningType(opening), glass_spec=tree["glass_spec"], glass_thickness_mm=D("24.00"),
            panel_article_sku=tree.get("panel_article_sku"))
        request = {"system_id": SYSTEM, "nominal_width_mm": width, "nominal_height_mm": height,
            "color": "WHITE", "parametric_tree": tree}
        response = calculation_response(request, calculate_geometry(node, params))
        if key == "mixed":
            tree = {"id": "MIXED", "type": "SPLIT_V", "split_offset_mm": "700.00", "children": [
                {**tree, "id": "S1", "opening_type": "SLIDING_2L"}, {**tree, "id": "T1", "opening_type": "TURN_LEFT"}]}
        sql(f"INSERT INTO public.projects(id,org_id,code,name,client_name,created_by) "
            f"VALUES('{project}','{ORG}','{key}','Upgrade {key}','Fixture','{ACTOR}');"
            "INSERT INTO public.project_positions(id,project_id,org_id,position_index,typology,system_id,width_mm,height_mm,parametric_tree,bom_snapshot) "
            f"VALUES('{position}','{project}','{ORG}',1,'{opening}','{SYSTEM}',{width},{height},{literal(tree)},{literal(response)});")
        if family:
            sql("INSERT INTO public.position_documentary_inputs(position_id,project_id,org_id,"
                "manufacturing_placement_policy_id,handle_requirement_policy_id,reinforcement_cut_policy_id,"
                "workshop_annotations,structural_inputs,glass_polishing,handle_intents,accessory_schedule,created_by,calculation_hash) "
                f"SELECT '{position}','{project}','{ORG}',p.id,h.id,r.id,'[]','[]','[]','[]','{{}}','{ACTOR}','{response['calculation_hash']}' "
                "FROM public.manufacturing_placement_policies p,public.handle_requirement_policies h,public.reinforcement_cut_policies r "
                f"WHERE p.system_id='{SYSTEM}' AND h.system_id='{SYSTEM}' AND r.system_id='{SYSTEM}' "
                "ORDER BY p.version DESC,h.version DESC,r.version DESC LIMIT 1;")
        if key in ("commercial", "issued"):
            sql("BEGIN; SELECT set_config('request.jwt.claims',"
                f"'{json.dumps({'sub': ACTOR, 'aal': 'aal2', 'role': 'authenticated'})}',true);"
                f"SELECT set_config('request.jwt.claim.sub','{ACTOR}',true);"
                "SELECT set_config('app.pricing_reason','Populated D01 authority',true);"
                "SET LOCAL ROLE pricing_backend;"
                f"UPDATE public.projects SET {'total_cost_net=100.00' if key=='commercial' else "status='QUOTED'"} WHERE id='{project}'; COMMIT;")
        saved[position] = (request, response, family, node, key)
    sql("CREATE TABLE d01_before AS SELECT id,to_jsonb(p) AS value FROM public.project_positions p;"
        "CREATE TABLE d01_catalog_before AS SELECT to_jsonb(s) AS value FROM public.profile_systems s "
        f"WHERE s.id='{SYSTEM}';"
        "CREATE TABLE d01_inputs_before AS SELECT * FROM public.position_documentary_inputs;")
    sql("\n".join(path.read_text(encoding="utf-8") for path in migrations if path.name >= FIRST_D01))
    after = json.loads(sql("SELECT json_agg(json_build_object('id',p.id,'system_id',p.system_id,'bom',p.bom_snapshot,"
        "'family',s.system_family,'legacy',s.legacy_authority,'outcome',m.outcome)) "
        "FROM public.project_positions p JOIN public.profile_systems s ON s.id=p.system_id "
        "JOIN public.catalog_family_migrations m ON m.position_id=p.id;", capture=True))
    assert len(after) == len(cases)
    for position in after:
        request, response, family, node, key = saved[position["id"]]
        if family:
            target = str(uuid5(NAMESPACE, SYSTEM + ":" + family))
            assert position["system_id"] == target and position["family"] == family and position["legacy"]
            assert position["outcome"] == "MIGRATED"
            assert {k: v for k, v in position["bom"].items() if k != "calculation_hash"} == {
                k: v for k, v in response.items() if k != "calculation_hash"}
            assert position["bom"]["calculation_hash"] == calculation_hash({**request, "system_id": target}, response)
            typed = demo_60_params().model_copy(update={"system_family": SystemFamily(family), "legacy_authority": True})
            assert calculate_geometry(node, typed) == calculate_geometry(node, demo_60_params())
        else:
            assert position["system_id"] == SYSTEM and position["bom"] == response, (key, position)
            assert position["outcome"] == {"mixed": "MIXED_FAMILIES", "commercial": "PRESERVED_COMMERCIAL", "issued": "PRESERVED_ISSUED"}[key]
    sql("DO $$ BEGIN IF EXISTS(SELECT 1 FROM d01_before b JOIN public.project_positions p ON p.id=b.id "
        "WHERE b.value - ARRAY['system_id','bom_snapshot'] IS DISTINCT FROM to_jsonb(p) - ARRAY['system_id','bom_snapshot']) "
        "THEN RAISE EXCEPTION 'D01 changed unrelated position fields'; END IF; "
        "IF EXISTS(SELECT 1 FROM d01_inputs_before b JOIN public.position_documentary_inputs p ON p.id=b.id "
        "WHERE b.calculation_hash=p.calculation_hash) THEN RAISE EXCEPTION 'D01 left stale documentary identity'; END IF; END $$;")
    print("  D01 populated upgrade: seven saved positions, exact manufacturing/hash and preserved commercial/issued authorities PASS", flush=True)
