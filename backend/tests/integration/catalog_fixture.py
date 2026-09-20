"""Independent unreferenced technical catalog for destructive negative fixtures."""

from uuid import uuid4
from pricing.repository import one, rows, json_text


def copy_fixed_catalog(org):
    source = one("SELECT * FROM public.profile_systems WHERE code='DEMO_60' AND is_global")
    target = uuid4()

    def insert(table, row):
        one(f"INSERT INTO public.{table} SELECT (jsonb_populate_record(NULL::public.{table},"
            "%s::jsonb)).* RETURNING id", [json_text(row)])

    insert("profile_systems", {**source, "id": target, "org_id": org,
        "code": f"TEST-{target.hex}", "is_global": False, "is_demo": False, "technical_locked": False})
    identities = {}
    for article in rows("SELECT * FROM public.profile_articles WHERE system_id=%s AND org_id IS NULL", [source["id"]]):
        identities[article["id"]] = uuid4()
        insert("profile_articles", {**article, "id": identities[article["id"]], "system_id": target, "org_id": org})
    for table in ("glazing_bead_matrix", "reinforcement_articles"):
        for row in rows(f"SELECT * FROM public.{table} WHERE system_id=%s AND org_id IS NULL", [source["id"]]):
            value = {**row, "id": uuid4(), "system_id": target, "org_id": org}
            for key in ("bead_article_id", "parent_profile_article_id"):
                if key in value:
                    value[key] = identities[value[key]]
            insert(table, value)
    for old, new in identities.items():
        for row in rows("SELECT * FROM public.profile_purchase_mappings WHERE profile_article_id=%s AND org_id IS NULL", [old]):
            insert("profile_purchase_mappings", {**row, "id": uuid4(), "profile_article_id": new, "org_id": org})
    return target
