from __future__ import annotations

from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = ROOT / "supabase" / "migrations" / "20260901000000_initial_schema.sql"
SEED_PATH = ROOT / "supabase" / "seed.sql"

BUSINESS_TABLES = (
    "tenancy_organizations",
    "tenancy_memberships",
    "profile_systems",
    "profile_articles",
    "glazing_bead_matrix",
    "hardware_kits",
    "cost_lists",
    "cost_list_items",
    "pricing_rules",
    "price_audit_logs",
    "projects",
    "project_positions",
    "project_versions",
    "orders",
    "offcut_inventory",
    "ai_audit_logs",
    "payment_customers",
    "subscriptions",
    "payments",
    "payment_events",
    "credit_ledger",
)


@pytest.fixture(scope="module")
def migration_sql() -> str:
    return MIGRATION_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def normalized_migration(migration_sql: str) -> str:
    return " ".join(migration_sql.lower().split())


@pytest.fixture(scope="module")
def seed_sql() -> str:
    return SEED_PATH.read_text(encoding="utf-8")


def without_literals_or_comments(sql: str) -> str:
    without_literals = re.sub(r"'(?:''|[^'])*'", "''", sql, flags=re.DOTALL)
    return re.sub(r"--[^\n]*", "", without_literals)


def table_definition(sql: str, table: str) -> str:
    pattern = rf"CREATE TABLE public\.{re.escape(table)}\s*\((.*?)\n\);"
    match = re.search(pattern, sql, flags=re.DOTALL | re.IGNORECASE)
    assert match is not None, f"Missing table definition: {table}"
    return match.group(1)


def test_complete_schema_enables_rls_for_every_business_table(migration_sql: str) -> None:
    for table in BUSINESS_TABLES:
        assert f"CREATE TABLE public.{table}" in migration_sql
        assert f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;" in migration_sql


def test_business_schema_has_no_floating_point_types(migration_sql: str) -> None:
    executable_sql = without_literals_or_comments(migration_sql)
    forbidden = re.compile(r"\b(?:REAL|FLOAT\d*|DOUBLE\s+PRECISION)\b", re.IGNORECASE)
    assert forbidden.search(executable_sql) is None


def test_payment_events_contract(migration_sql: str, normalized_migration: str) -> None:
    definition = table_definition(migration_sql, "payment_events")
    assert re.search(r"org_id\s+UUID\s+REFERENCES", definition)
    assert "org_id UUID NOT NULL" not in definition
    assert "CONSTRAINT uk_provider_event UNIQUE (provider, event_id)" in definition
    assert "create policy payment_events_service_role" in normalized_migration
    assert "auth.jwt() ->> 'role' = 'service_role'" in normalized_migration
    assert "revoke all on public.payment_events from anon, authenticated" in normalized_migration


@pytest.mark.parametrize(
    "table",
    ("cost_lists", "cost_list_items", "pricing_rules", "price_audit_logs"),
)
def test_cost_policy_is_strict_for_reads_and_writes(
    table: str,
    normalized_migration: str,
) -> None:
    policy = re.search(
        rf"create policy \w+ on public\.{table} (.*?);",
        normalized_migration,
    )
    assert policy is not None
    policy_sql = policy.group(1)
    predicate = "org_id in (select public.current_user_org_ids())"
    assert "for all" in policy_sql
    assert f"using ({predicate})" in policy_sql
    assert f"with check ({predicate})" in policy_sql


@pytest.mark.parametrize("table", ("projects", "cost_lists"))
def test_tenant_data_contract_filters_by_current_memberships(
    table: str,
    normalized_migration: str,
) -> None:
    policy = re.search(
        rf"create policy \w+ on public\.{table} (.*?);",
        normalized_migration,
    )
    assert policy is not None
    assert "org_id in (select public.current_user_org_ids())" in policy.group(1)


def test_global_catalog_requires_an_authenticated_user(normalized_migration: str) -> None:
    policy = re.search(
        r"create policy profile_systems_select on public\.profile_systems (.*?);",
        normalized_migration,
    )
    assert policy is not None
    assert "auth.uid() is not null and is_global = true" in policy.group(1)


def test_superadmin_is_only_modeled_from_app_metadata(normalized_migration: str) -> None:
    assert "create or replace function public.is_platform_superadmin()" in normalized_migration
    assert "auth.jwt() -> 'app_metadata' ->> 'is_superadmin'" in normalized_migration
    assert not re.search(r"create policy .*superadmin", normalized_migration)


def test_demo_60_system_seed_is_exact(seed_sql: str) -> None:
    expected_values = (
        "'DEMO_60'",
        "'Sistema Demo 60mm PVC'",
        "60.00",
        "'PVC'",
        "8.00",
        "5.00",
        "35.00",
        "6.00",
        "TRUE",
    )
    for value in expected_values:
        assert value in seed_sql


@pytest.mark.parametrize(
    ("opening_type", "limits"),
    (
        ("TURN", ("400.00", "1200.00", "500.00", "2400.00", "80.00", "0", "0")),
        (
            "TILT_TURN",
            ("450.00", "1400.00", "600.00", "2400.00", "100.00", "0", "1"),
        ),
        (
            "SLIDING",
            ("400.00", "1500.00", "500.00", "2500.00", "120.00", "2", "0"),
        ),
    ),
)
def test_demo_60_hardware_seed_is_exact(
    opening_type: str,
    limits: tuple[str, ...],
    seed_sql: str,
) -> None:
    start = seed_sql.index(f"        '{opening_type}',")
    row_tail = seed_sql[start : seed_sql.index("    )", start)]
    cursor = 0
    for value in limits:
        cursor = row_tail.index(value, cursor) + len(value)


def test_demo_60_profile_roles_and_welding_are_exact(seed_sql: str) -> None:
    required_rows = (
        ("'MARCO'", "'FRAME'", "60.00", "6.00"),
        ("'HOJA'", "'SASH'", "60.00", "6.00"),
        ("'POSTE-V'", "'MULLION_V'", "60.00", "0.00"),
        ("'POSTE-H'", "'MULLION_H'", "60.00", "0.00"),
        ("'JQ-24'", "'GLAZING_BEAD'", "24.00", "0.00"),
        ("'JQ-14'", "'GLAZING_BEAD'", "14.00", "0.00"),
        ("'JQ-10'", "'GLAZING_BEAD'", "10.00", "0.00"),
    )
    for sku, role, width, welding_loss in required_rows:
        start = seed_sql.index(f"        {sku},")
        row_tail = seed_sql[start : seed_sql.index("    )", start)]
        assert role in row_tail
        assert width in row_tail
        assert row_tail.rstrip().endswith(welding_loss)


@pytest.mark.parametrize(
    ("thickness", "bead", "width", "gasket"),
    (
        ("4.00", "JQ-24", "24.00", "3.00"),
        ("5.00", "JQ-24", "24.00", "2.50"),
        ("6.00", "JQ-24", "24.00", "2.00"),
        ("20.00", "JQ-14", "14.00", "3.00"),
        ("24.00", "JQ-10", "10.00", "3.00"),
    ),
)
def test_demo_60_glazing_matrix_is_exact(
    thickness: str,
    bead: str,
    width: str,
    gasket: str,
    seed_sql: str,
) -> None:
    marker = f"/GLASS-{thickness.split('.')[0]}'"
    start = seed_sql.index(marker)
    row_tail = seed_sql[start : seed_sql.index("    )", start)]
    assert f"/{bead}'" in row_tail
    expected_tail = f"{width},\n        {gasket},\n        {gasket}"
    assert expected_tail in row_tail
