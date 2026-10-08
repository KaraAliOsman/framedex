"""P02 deterministic populated backfill preserves every historical source byte."""

from pathlib import Path

import local_gates

ROOT = Path(__file__).resolve().parents[1]
FIRST = "20270107000000_human_entity_codes.sql"
ORG = "19700000-0000-4000-8000-000000000001"
PROJECT = "19700000-0000-4000-8000-000000000002"


def verify(container: str) -> None:
    database = "human_codes_upgrade"
    docker = local_gates.executable("docker")

    def sql(source, db=database):
        return local_gates.run([docker, "exec", "-i", container, "psql", "-X", "-A", "-t",
            "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", db], input_text=source, capture=True)

    sql(f"CREATE DATABASE {database}", db="postgres")
    bootstrap = (ROOT / "supabase/compat/postgres16_bootstrap.sql").read_text(encoding="utf-8")
    sql(bootstrap[bootstrap.index("CREATE SCHEMA auth;"):])
    migrations = sorted((ROOT / "supabase/migrations").glob("*.sql"))
    for migration in migrations:
        if migration.name >= FIRST:
            break
        sql(migration.read_text(encoding="utf-8"))
    sql(f"""INSERT INTO public.tenancy_organizations(id,name,tax_id) VALUES('{ORG}','P02 upgrade','P02-197');
        INSERT INTO public.projects(id,org_id,code,name,client_name,created_by)
        VALUES('{PROJECT}','{ORG}','P-000123','P02 upgrade','Fixture','19700000-0000-4000-8000-000000000003');
        INSERT INTO public.pricing_operations(id,org_id,project_id,requested_by,request,input_snapshot,result,source_revision,state,reason)
        VALUES('19700000-0000-4000-8000-000000000004','{ORG}','{PROJECT}',
            '19700000-0000-4000-8000-000000000003','{{}}','{{}}','{{}}','REV-A','APPLIED','Synthetic populated P02 upgrade');
        INSERT INTO public.project_versions(id,project_id,org_id,revision_code,snapshot_json,emitted_by,
            authority_version,pricing_operation_id,canonical_version,bom_hash,snapshot_sha256,production_allowed,documentary_complete)
        VALUES('19700000-0000-4000-8000-000000000005','{PROJECT}','{ORG}','REV-A','{{}}',
            '19700000-0000-4000-8000-000000000003','SHOT09_V1','19700000-0000-4000-8000-000000000004',
            'DOCUMENTARY_CANONICAL_V1',repeat('a',64),repeat('b',64),true,true);
        DO $$ DECLARE i integer; kind public.order_type; batch uuid; eligibility uuid;
        BEGIN FOR i IN REVERSE 3..1 LOOP
            kind := (ARRAY['SUPPLIER_GLASS_PO','SUPPLIER_PROFILE_PO','SUPPLIER_HARDWARE_PO'])[i]::public.order_type;
            batch := ('19700000-0000-4000-8004-'||lpad(i::text,12,'0'))::uuid;
            eligibility := ('19700000-0000-4000-8005-'||lpad(i::text,12,'0'))::uuid;
            INSERT INTO public.supplier_eligibility_versions(id,project_id,project_version_id,org_id,bom_hash,snapshot_sha256,
                order_type,supplier_identity,supplier_name,supplier_details,eligible_requirement_keys,evidence,version,content_hash,created_by)
            VALUES(eligibility,'{PROJECT}','19700000-0000-4000-8000-000000000005','{ORG}',repeat('a',64),repeat('b',64),
                kind,'HISTORICAL-SUPPLIER','Synthetic supplier','{{}}','[]','{{}}',1,repeat(i::text,64),'19700000-0000-4000-8000-000000000003');
            INSERT INTO public.order_allocation_batches(id,project_id,project_version_id,org_id,bom_hash,snapshot_sha256,
                order_type,allocation_hash,confirmed_by)
            VALUES(batch,'{PROJECT}','19700000-0000-4000-8000-000000000005','{ORG}',repeat('a',64),repeat('b',64),
                kind,repeat(i::text,64),'19700000-0000-4000-8000-000000000003');
            INSERT INTO public.orders(id,org_id,project_id,project_version_id,order_type,order_code,payload_json,created_at,
                allocation_batch_id,supplier_eligibility_id,bom_hash,revision_snapshot_sha256,purchase_projection_hash,
                allocation_identity,order_snapshot_hash,supplier_identity,supplier_name,supplier_details,confirmed_by,confirmed_at)
            VALUES(('19700000-0000-4000-8001-'||lpad(i::text,12,'0'))::uuid,'{ORG}','{PROJECT}',
                '19700000-0000-4000-8000-000000000005',kind,'PO-HISTORIC-'||i,'{{"historical":"sealed"}}',
                CASE WHEN i=3 THEN '2025-01-02'::timestamptz ELSE '2025-01-01'::timestamptz END,
                batch,eligibility,repeat('a',64),repeat('b',64),repeat(i::text,64),repeat(i::text,64),
                encode(digest('{{"historical":"sealed"}}','sha256'),'hex'),
                'HISTORICAL-SUPPLIER','Synthetic supplier','{{}}','19700000-0000-4000-8000-000000000003',now());
        END LOOP; END $$;""")
    sql(f"""INSERT INTO public.inventory_remnants(id,org_id,kind,sheet_workshop_sku,width_mm,height_mm,created_at)
        SELECT ('19700000-0000-4000-8002-'||lpad(i::text,12,'0'))::uuid,'{ORG}','SHEET','P02-SHEET',100,200,'2025-01-01'
        FROM generate_series(3,1,-1) i;
        INSERT INTO public.order_receipts(id,org_id,order_id,receipt_key,created_at)
        SELECT ('19700000-0000-4000-8003-'||lpad(i::text,12,'0'))::uuid,'{ORG}',
            '19700000-0000-4000-8001-000000000001','historical-'||i,'2025-01-01'
        FROM generate_series(3,1,-1) i;""")
    tables = ("orders", "inventory_remnants", "order_receipts", "projects", "project_versions",
              "pricing_operations", "supplier_eligibility_versions", "order_allocation_batches")
    before = {table: sql(f"SELECT jsonb_agg(to_jsonb(t) ORDER BY id) FROM public.{table} t WHERE org_id='{ORG}'") for table in tables}
    sql("BEGIN;" + (ROOT / "supabase/migrations" / FIRST).read_text(encoding="utf-8") + "COMMIT;")
    assert before == {table: sql(f"SELECT jsonb_agg(to_jsonb(t) ORDER BY id) FROM public.{table} t WHERE org_id='{ORG}'") for table in tables}
    sql(f"""DO $$ BEGIN
        IF EXISTS(SELECT 1 FROM public.entity_codes WHERE org_id='{ORG}' AND sequence_no<>right(entity_id::text,12)::bigint)
            OR (SELECT count(*) FROM public.entity_codes WHERE org_id='{ORG}')<>9
        THEN RAISE EXCEPTION 'human code backfill not deterministic'; END IF;
        IF private.assign_entity_code('{ORG}','OC','19700000-0000-4000-8001-000000000004')<>'OC-000004'
        THEN RAISE EXCEPTION 'backfilled counter not continued'; END IF;
        END $$;""")
    print("  P02 populated PG16 upgrade: OC/RT/REC order by timestamp/id; every old row/hash/payload unchanged PASS", flush=True)
