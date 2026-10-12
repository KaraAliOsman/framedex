"""Populated v1-v7 catalog, money and sealed documents survive D08 exactly."""
from pathlib import Path
import local_gates

ROOT = Path(__file__).resolve().parents[1]
FIRST = "20270126000000_advanced_opening_authority.sql"


def verify(container: str) -> None:
    docker = local_gates.executable("docker")
    database = "advanced_opening_upgrade"
    def sql(source, *, db=database):
        return local_gates.run([docker, "exec", "-i", container, "psql", "-X", "-A", "-t",
            "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", db], input_text=source, capture=True)
    # An independent populated schema includes previously issued documents and
    # immutable prices from the existing upgrade fixture, without replaying it.
    sql(f"CREATE DATABASE {database} TEMPLATE brand_mail_upgrade", db="postgres")
    for path in sorted((ROOT / "supabase/migrations").glob("*.sql")):
        if "20270125000000_field_work.sql" <= path.name < FIRST:
            sql(path.read_text(encoding="utf-8"))
    tables = ("projects", "project_positions", "project_versions", "pricing_operations", "price_audit_logs",
              "document_artifacts", "mail_outbox", "profile_systems", "profile_articles", "hardware_kits")
    def capture():
        return {table: sql(f"SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY id),'[]') FROM public.{table} t") for table in tables}
    before = capture()
    for path in sorted((ROOT / "supabase/migrations").glob("*.sql")):
        if path.name >= FIRST:
            sql(path.read_text(encoding="utf-8"))
    after = capture()
    import json
    for table in tables:
        current = {row["id"]: row for row in json.loads(after[table])}
        for row in json.loads(before[table]):
            assert current[row["id"]] == row, f"D08 rewrote historical {table}"
    sql("""DO $$ BEGIN
      IF (SELECT count(*) FROM profile_systems WHERE version=8 AND is_demo)<>7
        OR EXISTS(SELECT 1 FROM profile_systems WHERE version<8 AND opening_capabilities::TEXT LIKE '%advanced_recipes%')
      THEN RAISE EXCEPTION 'Advanced capability inferred on historical catalog'; END IF;
    END $$;""")
    print("  D08 populated PG16 upgrade: v1-v7, BOMs, money and issued bytes unchanged PASS", flush=True)
