"""Upgrade populated documents through P23 without inventing field authority."""

from pathlib import Path
import local_gates

ROOT = Path(__file__).resolve().parents[1]
FIRST = "20270125000000_field_work.sql"


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

    tables = (
        "orders",
        "deliveries",
        "dispatch_notes",
        "delivery_confirmations",
        "projects",
        "project_versions",
        "pricing_operations",
        "mail_outbox",
        "order_requirement_lines",
    )

    def capture():
        return {
            table: sql(
                f"SELECT coalesce(jsonb_agg(to_jsonb(t)-'field_authorization_id' ORDER BY (to_jsonb(t)-'field_authorization_id')::text),'[]') FROM public.{table} t"
            )
            for table in tables
        }

    before = capture()
    for path in sorted((ROOT / "supabase/migrations").glob("*.sql")):
        if path.name >= FIRST:
            sql(path.read_text(encoding="utf-8"))
    assert capture() == before, "P23 changed historical source/POD/document/price bytes"
    sql("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM field_visits) OR EXISTS(SELECT 1 FROM field_incidents)
        OR EXISTS(SELECT 1 FROM field_assets) OR EXISTS(SELECT 1 FROM field_receipts)
      THEN RAISE EXCEPTION 'Historical field facts were inferred'; END IF;
    END $$;""")
    print(
        "  P23 populated PG16 upgrade: issued documents, source OTs, POD and historical prices preserved PASS",
        flush=True,
    )
