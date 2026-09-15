"""Populated pre-SHOT-09 project_versions upgrade on PostgreSQL 16.

Builds the pre-SHOT-09 schema, inserts a legitimate legacy project_version,
applies the SHOT-09 migrations, and proves the row survives unchanged as typed
PRE_SHOT09 evidence that cannot masquerade as a V1 revision, while new V1
revisions still require the complete strict authority contract.
"""

from pathlib import Path
import subprocess

import local_gates

ROOT = Path(__file__).resolve().parents[1]

FIRST_SHOT09 = "20260914000000_shot_09_documentary.sql"


def verify(container: str) -> None:
    docker = local_gates.executable("docker")

    def sql(database: str, source: str, expected_error: str | None = None) -> None:
        command = [docker, "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1",
                   "-U", "postgres", "-d", database]
        if expected_error is None:
            local_gates.run(command, input_text=source)
            return
        result = subprocess.run(command, input=source, capture_output=True,
                                text=True, encoding="utf-8", check=False)
        if result.returncode != 3 or expected_error not in result.stderr:
            raise RuntimeError("Expected rejection did not occur: "
                               + local_gates.redact(result.stdout + result.stderr))

    bootstrap = (ROOT / "supabase/compat/postgres16_bootstrap.sql").read_text(encoding="utf-8")
    bootstrap = bootstrap[bootstrap.index("CREATE SCHEMA auth;"):]
    migrations = sorted((ROOT / "supabase/migrations").glob("*.sql"))
    database = "shot09_upgrade"
    sql("postgres", f"CREATE DATABASE {database};")
    sql(database, bootstrap)
    for path in migrations:
        if path.name >= FIRST_SHOT09:
            break
        sql(database, path.read_text(encoding="utf-8"))
    sql(database, (ROOT / "supabase/seed.sql").read_text(encoding="utf-8"))

    # A legitimate pre-SHOT-09 revision: only the historical columns exist.
    sql(database, """
      INSERT INTO public.tenancy_organizations(id,name,tax_id)
        VALUES('88990000-0000-4000-8000-000000000001','Populated SHOT-09 upgrade','S09-UP');
      INSERT INTO public.projects(id,org_id,code,name,client_name,created_by)
        VALUES('88990000-0000-4000-8000-000000000002','88990000-0000-4000-8000-000000000001',
               'LEGACY-1','Historical project','Fixture','88990000-0000-4000-8000-000000000003');
      INSERT INTO public.project_versions(id,project_id,org_id,revision_code,snapshot_json,
               pdf_storage_path,emitted_by)
        VALUES('88990000-0000-4000-8000-000000000004','88990000-0000-4000-8000-000000000002',
               '88990000-0000-4000-8000-000000000001','R0',
               '{"historical":true,"total_price_gross":"119000"}',
               'org_88990000-0000-4000-8000-000000000001/legacy/r0.pdf',
               '88990000-0000-4000-8000-000000000003');
      CREATE TABLE project_versions_before AS
        SELECT * FROM public.project_versions
        WHERE id = '88990000-0000-4000-8000-000000000004';
    """)

    for path in migrations:
        if path.name < FIRST_SHOT09:
            continue
        sql(database, path.read_text(encoding="utf-8"))

    sql(database, """
      DO $$ DECLARE
        legacy public.project_versions%ROWTYPE;
      BEGIN
        SELECT * INTO legacy FROM public.project_versions
         WHERE id = '88990000-0000-4000-8000-000000000004';
        IF NOT FOUND THEN
          RAISE EXCEPTION 'Populated upgrade lost the legacy project_version';
        END IF;
        IF legacy.authority_version <> 'PRE_SHOT09' THEN
          RAISE EXCEPTION 'Legacy row was not typed PRE_SHOT09: %', legacy.authority_version;
        END IF;
        IF legacy.pricing_operation_id IS NOT NULL OR legacy.canonical_version IS NOT NULL
           OR legacy.bom_hash IS NOT NULL OR legacy.snapshot_sha256 IS NOT NULL
           OR legacy.production_allowed IS NOT NULL OR legacy.documentary_complete IS NOT NULL
        THEN
          RAISE EXCEPTION 'Legacy row gained fabricated V1 authority';
        END IF;
        IF (SELECT to_jsonb(v.*) FROM public.project_versions v
             WHERE v.id = legacy.id) - 'authority_version' - 'pricing_operation_id'
             - 'canonical_version' - 'bom_hash' - 'snapshot_sha256' - 'production_allowed'
             - 'documentary_complete'
           IS DISTINCT FROM
           (SELECT to_jsonb(b.*) FROM project_versions_before b)
        THEN
          RAISE EXCEPTION 'Legacy row historical semantics changed during upgrade';
        END IF;
      END $$;
    """)
    print("  Legacy row survives unchanged and stays typed PRE_SHOT09: PASS", flush=True)

    sql(database, """
      DO $$ BEGIN
        BEGIN
          UPDATE public.project_versions SET revision_code='RX'
           WHERE id='88990000-0000-4000-8000-000000000004';
          RAISE EXCEPTION 'Legacy row update unexpectedly succeeded';
        EXCEPTION WHEN insufficient_privilege THEN
          IF SQLERRM <> 'documentary_evidence_immutable' THEN RAISE; END IF;
        END;
        BEGIN
          INSERT INTO public.project_versions(project_id,org_id,revision_code,snapshot_json,
                   emitted_by,authority_version)
            VALUES('88990000-0000-4000-8000-000000000002','88990000-0000-4000-8000-000000000001',
                   'R9','{}','88990000-0000-4000-8000-000000000003','PRE_SHOT09');
          RAISE EXCEPTION 'PRE_SHOT09 insert unexpectedly succeeded';
        EXCEPTION WHEN check_violation THEN
          IF SQLERRM <> 'legacy_version_insert_forbidden' THEN RAISE; END IF;
        END;
        BEGIN
          INSERT INTO public.document_artifacts(id,org_id,project_id,project_version_id,
                   artifact_scope,artifact_scope_id,document_type,format,bom_hash,
                   revision_snapshot_sha256,storage_bucket,storage_object_key,file_sha256,
                   media_type,byte_size,created_by)
            VALUES('88990000-0000-4000-8000-000000000007','88990000-0000-4000-8000-000000000001',
                   '88990000-0000-4000-8000-000000000002',
                   '88990000-0000-4000-8000-000000000004','PROJECT_REVISION',
                   '88990000-0000-4000-8000-000000000004','DOC-05','PDF',
                   'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                   'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
                   'documents',
                   'org_88990000-0000-4000-8000-000000000001/projects/88990000-0000-4000-8000-000000000002/R0/doc05.pdf',
                   'abababababababababababababababababababababababababababababababab',
                   'application/pdf',1024,'88990000-0000-4000-8000-000000000003');
          RAISE EXCEPTION 'Artifact bound to a legacy version unexpectedly succeeded';
        EXCEPTION WHEN foreign_key_violation THEN NULL;
        END;
      END $$;
    """)
    print("  Legacy row cannot masquerade as V1 or bind artifacts: PASS", flush=True)

    sql(database, """
      INSERT INTO public.pricing_operations(id,org_id,project_id,requested_by,request,
               input_snapshot,result,source_revision,state,reason)
        VALUES('88990000-0000-4000-8000-000000000005','88990000-0000-4000-8000-000000000001',
               '88990000-0000-4000-8000-000000000002','88990000-0000-4000-8000-000000000003',
               '{}','{}','{}','REV-A','APPLIED','shot09 upgrade pricing authority');
      DO $$ BEGIN
        BEGIN
          INSERT INTO public.project_versions(project_id,org_id,revision_code,snapshot_json,
                   emitted_by,pricing_operation_id,canonical_version,snapshot_sha256,
                   production_allowed,documentary_complete)
            VALUES('88990000-0000-4000-8000-000000000002','88990000-0000-4000-8000-000000000001',
                   'REV-A','{}','88990000-0000-4000-8000-000000000003',
                   '88990000-0000-4000-8000-000000000005','DOCUMENTARY_CANONICAL_V1',
                   'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd',
                   TRUE,TRUE);
          RAISE EXCEPTION 'V1 revision without bom_hash unexpectedly succeeded';
        EXCEPTION WHEN check_violation THEN
          IF SQLERRM NOT LIKE '%project_versions_v1_authority%' THEN RAISE; END IF;
        END;
      END $$;
      INSERT INTO public.project_versions(id,project_id,org_id,revision_code,snapshot_json,
               emitted_by,authority_version,pricing_operation_id,canonical_version,bom_hash,
               snapshot_sha256,production_allowed,documentary_complete)
        VALUES('88990000-0000-4000-8000-000000000006','88990000-0000-4000-8000-000000000002',
               '88990000-0000-4000-8000-000000000001','REV-A','{}',
               '88990000-0000-4000-8000-000000000003','SHOT09_V1',
               '88990000-0000-4000-8000-000000000005','DOCUMENTARY_CANONICAL_V1',
               'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
               'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd',
               TRUE,TRUE);
      DO $$ BEGIN
        IF (SELECT count(*) FROM public.project_versions
             WHERE org_id='88990000-0000-4000-8000-000000000001') <> 2 THEN
          RAISE EXCEPTION 'Post-upgrade version count is wrong';
        END IF;
        IF (SELECT count(*) FROM public.project_versions
             WHERE authority_version='SHOT09_V1'
               AND bom_hash ~ '^[0-9a-f]{64}$') <> 1 THEN
          RAISE EXCEPTION 'Post-upgrade V1 authority is wrong';
        END IF;
      END $$;
    """)
    print("  New V1 revisions still require the complete strict contract: PASS", flush=True)
    print("  SHOT-09 populated pre-authority upgrade: PASS", flush=True)
