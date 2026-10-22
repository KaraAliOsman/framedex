"""Populated v1-v7 catalog, money and sealed documents survive D08 exactly."""
from pathlib import Path
import json

from scripts import local_gates

ROOT = Path(__file__).resolve().parents[1]
FIRST = "20270126000000_advanced_opening_authority.sql"


def assert_historical_rows(before: dict, after: dict) -> None:
    # Explicit additions only: never ignore an unknown column or any old
    # price, actor, reason, timestamp, snapshot, record or document byte.
    added = {"projects": {"design_defaults": {}, "commercial_number": None},
             "document_artifacts": {"layout": "STANDARD"}}
    for table, previous in before.items():
        current = {row["id"]: row for row in after[table]}
        if table == "price_audit_logs":
            assert set(current) == {row["id"] for row in previous}, "Price audit rows changed during upgrade"
            ordinals = [row.get("event_order") for row in current.values()]
            assert all(type(value) is int and value > 0 for value in ordinals), "Invalid price audit ordinal"
            assert len(ordinals) == len(set(ordinals)), "Price audit ordinals must be distinct"
        for row in previous:
            defaults = {key: value for key, value in added.get(table, {}).items() if key not in row}
            found = dict(current[row["id"]])
            if table == "price_audit_logs" and "event_order" not in row:
                # Identity backfills stable ordinals, not recovered chronology.
                # Its type, uniqueness and immutability are independently gated.
                found.pop("event_order")
            assert found == {**row, **defaults}, f"D08 rewrote historical {table}"


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
    # Columns added by later migrations carry their declared empty default on
    # historical rows; every pre-existing field stays byte-identical.
    assert_historical_rows({table: json.loads(before[table]) for table in tables},
        {table: json.loads(after[table]) for table in tables})
    sql("""DO $$ BEGIN
      IF NOT EXISTS(SELECT 1 FROM pg_attribute WHERE attrelid='public.price_audit_logs'::regclass
        AND attname='event_order' AND attidentity='a' AND attnotnull AND atttypid='bigint'::regtype)
      THEN RAISE EXCEPTION 'Price audit ordinal must be a nonnull bigint always identity'; END IF;
      IF (SELECT count(*) FROM profile_systems WHERE version=8 AND is_demo)<>7
        OR EXISTS(SELECT 1 FROM profile_systems WHERE version<8 AND opening_capabilities::TEXT LIKE '%advanced_recipes%')
      THEN RAISE EXCEPTION 'Advanced capability inferred on historical catalog'; END IF;
    END $$;""")
    print("  D08 populated PG16 upgrade: v1-v7, BOMs, money and issued bytes unchanged PASS", flush=True)
