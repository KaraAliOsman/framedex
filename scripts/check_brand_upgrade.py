"""P25 populated upgrade: historical identities and issued authority stay exact."""

from pathlib import Path

import local_gates

ROOT = Path(__file__).resolve().parents[1]
FIRST = "20270108000000_brand_and_mail.sql"
ORG = "19800000-0000-4000-8000-000000000001"
PROJECT = "19800000-0000-4000-8000-000000000002"
ACTOR = "19800000-0000-4000-8000-000000000003"
PRICING = "19800000-0000-4000-8000-000000000004"


def verify(container: str) -> None:
    database = "brand_mail_upgrade"
    docker = local_gates.executable("docker")

    def sql(source, db=database):
        return local_gates.run(
            [
                docker,
                "exec",
                "-i",
                container,
                "psql",
                "-X",
                "-A",
                "-t",
                "-v",
                "ON_ERROR_STOP=1",
                "-U",
                "postgres",
                "-d",
                db,
            ],
            input_text=source,
            capture=True,
        )

    sql(f"CREATE DATABASE {database}", db="postgres")
    bootstrap = (ROOT / "supabase/compat/postgres16_bootstrap.sql").read_text(encoding="utf-8")
    sql(bootstrap[bootstrap.index("CREATE SCHEMA auth;") :])
    for migration in sorted((ROOT / "supabase/migrations").glob("*.sql")):
        if migration.name >= FIRST:
            break
        sql(migration.read_text(encoding="utf-8"))
    sql(f"""
        INSERT INTO public.tenancy_organizations(id,name,tax_id,commercial_name,brand_logo_key,brand_logo_sha256)
        VALUES('{ORG}','P25 historical','P25-upgrade','Original manufacturer','historical/logo.png',repeat('a',64));
        INSERT INTO public.projects(id,org_id,code,name,client_name,created_by)
        VALUES('{PROJECT}','{ORG}','P-000123','Historical quote','Fixture','{ACTOR}');
        INSERT INTO public.pricing_operations(id,org_id,project_id,requested_by,request,input_snapshot,result,source_revision,state,reason)
        VALUES('{PRICING}','{ORG}','{PROJECT}','{ACTOR}','{{}}','{{}}','{{}}','REV-A','APPLIED','Synthetic populated upgrade');
        INSERT INTO public.project_versions(id,project_id,org_id,revision_code,snapshot_json,emitted_by,
          authority_version,pricing_operation_id,canonical_version,bom_hash,snapshot_sha256,production_allowed,documentary_complete)
        VALUES('19800000-0000-4000-8000-000000000005','{PROJECT}','{ORG}','REV-A',
          '{{"organization":{{"commercial_name":"Original manufacturer","brand_logo_key":"historical/logo.png"}},"legacy":true}}',
          '{ACTOR}','SHOT09_V1','{PRICING}','DOCUMENTARY_CANONICAL_V1',repeat('b',64),repeat('c',64),true,true);
    """)
    tables = ("projects", "project_versions", "pricing_operations")
    before = {
        table: sql(f"SELECT to_jsonb(t) FROM public.{table} t WHERE org_id='{ORG}'")
        for table in tables
    }
    identity_before = sql(
        f"SELECT to_jsonb(t) FROM public.tenancy_organizations t WHERE id='{ORG}'"
    )
    sql("BEGIN;" + (ROOT / "supabase/migrations" / FIRST).read_text(encoding="utf-8") + "COMMIT;")
    after = {
        table: sql(f"SELECT to_jsonb(t) FROM public.{table} t WHERE org_id='{ORG}'")
        for table in tables
    }
    assert before == after, "brand migration changed issued or pricing authority"
    assert (
        identity_before
        == sql(f"""SELECT to_jsonb(t) - ARRAY['brand_primary_color','document_attribution',
        'portal_attribution','notification_email','internal_mail_enabled'] FROM public.tenancy_organizations t WHERE id='{ORG}'""")
    ), "historical issuer changed"
    sql(f"""DO $$ BEGIN
        IF NOT EXISTS(SELECT 1 FROM public.tenancy_organizations WHERE id='{ORG}' AND
          brand_primary_color='#075F5A' AND NOT document_attribution AND portal_attribution AND NOT internal_mail_enabled)
        THEN RAISE EXCEPTION 'brand preference defaults invalid'; END IF;
        IF EXISTS(SELECT 1 FROM public.project_versions WHERE org_id='{ORG}' AND snapshot_json->'organization' ? 'brand_schema')
        THEN RAISE EXCEPTION 'legacy authority silently upgraded'; END IF;
        END $$;""")
    print(
        "  P25 populated PG16 upgrade: original issuer, snapshots, hashes and pricing byte-identical; explicit defaults PASS",
        flush=True,
    )
