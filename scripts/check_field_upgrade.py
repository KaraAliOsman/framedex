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

    # Later migrations add projects.design_defaults/commercial_number; they are
    # compared apart below and must keep their declared empty value.
    row = "to_jsonb(t)-'field_authorization_id'-'design_defaults'-'commercial_number'"

    def capture():
        return {
            table: sql(
                f"SELECT coalesce(jsonb_agg({row} ORDER BY ({row})::text),'[]') FROM public.{table} t"
            )
            for table in tables
        }

    before = capture()
    for path in sorted((ROOT / "supabase/migrations").glob("*.sql")):
        if path.name >= FIRST:
            sql(path.read_text(encoding="utf-8"))
    assert capture() == before, "P23 changed historical source/POD/document/price bytes"
    sql("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM projects WHERE design_defaults<>'{}'::jsonb OR commercial_number IS NOT NULL)
      THEN RAISE EXCEPTION 'Historical projects received invented defaults'; END IF;
    END $$;""")
    sql("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM field_visits) OR EXISTS(SELECT 1 FROM field_incidents)
        OR EXISTS(SELECT 1 FROM field_assets) OR EXISTS(SELECT 1 FROM field_receipts)
      THEN RAISE EXCEPTION 'Historical field facts were inferred'; END IF;
    END $$;""")
    print(
        "  P23 populated PG16 upgrade: issued documents, source OTs, POD and historical prices preserved PASS",
        flush=True,
    )
