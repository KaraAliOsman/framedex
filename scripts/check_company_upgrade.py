"""Extend the populated P25 database through P22, preserving legacy identities."""

from pathlib import Path

import local_gates
from check_brand_upgrade import ORG

ROOT = Path(__file__).resolve().parents[1]
FIRST = "20270124000000_client_dossiers.sql"


def verify(container: str) -> None:
    def sql(source):
        return local_gates.run(
            [
                local_gates.executable("docker"),
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
                "brand_mail_upgrade",
            ],
            input_text=source,
            capture=True,
        )

    paths = sorted((ROOT / "supabase/migrations").glob("*.sql"))
    for path in paths:
        if "20270108000000_brand_and_mail.sql" < path.name < FIRST:
            sql(path.read_text(encoding="utf-8"))
    sql(f"""
      INSERT INTO public.clients(org_id,name,rut,email,phone,notes,created_by)
      VALUES('{ORG}','Legacy A','76.543.210-1','legacy@example.test','123','Legacy note','19800000-0000-4000-8000-000000000003'),
            ('{ORG}','Legacy B','76543210-1',NULL,NULL,NULL,'19800000-0000-4000-8000-000000000003');
    """)
    tables = ("clients", "projects", "project_versions", "pricing_operations", "mail_outbox")
    currency = sql(f"SELECT currency FROM public.tenancy_organizations WHERE id='{ORG}'")
    before = {
        table: sql(
            f"SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY id),'[]') FROM public.{table} t WHERE org_id='{ORG}'"
        )
        for table in tables
    }
    for path in paths:
        if FIRST <= path.name < "20270125000000_field_work.sql":
            sql(path.read_text(encoding="utf-8"))
    after = {}
    for table in tables:
        added = (
            "-ARRAY['party_kind','merged_into_id']"
            if table == "clients"
            else "-'client_address_id'"
            if table == "projects"
            else ""
        )
        after[table] = sql(
            f"SELECT coalesce(jsonb_agg(to_jsonb(t){added} ORDER BY id),'[]') FROM public.{table} t WHERE org_id='{ORG}'"
        )
    assert before == after, "P22 changed historical client/project/document/price/mail evidence"
    assert currency == sql(f"SELECT currency FROM public.tenancy_organizations WHERE id='{ORG}'"), "P22 reinterpreted base-currency authority"
    sql(f"""DO $$ BEGIN
      IF (SELECT count(*) FROM public.clients WHERE org_id='{ORG}' AND party_kind='UNKNOWN' AND merged_into_id IS NULL)<>2
        OR (SELECT count(*) FROM public.client_contacts WHERE org_id='{ORG}' AND email='legacy@example.test' AND is_primary)<>1
        OR (SELECT count(*) FROM public.client_notes WHERE org_id='{ORG}' AND is_legacy AND body='Legacy note' AND author_label='Autor no registrado · nota histórica')<>1
      THEN RAISE EXCEPTION 'Legacy type, contact or authorship was inferred or lost'; END IF;
      IF (SELECT require_mfa FROM public.tenancy_organizations WHERE id='{ORG}') THEN RAISE EXCEPTION 'MFA silently enabled'; END IF;
      IF (SELECT quotation_currency IS NOT NULL FROM public.tenancy_organizations WHERE id='{ORG}') THEN RAISE EXCEPTION 'Quotation currency silently overridden'; END IF;
    END $$;""")
    print(
        "  P22 populated PG16 upgrade: colliding historical RUTs, unknown type, contacts/notes and sealed evidence preserved PASS",
        flush=True,
    )
