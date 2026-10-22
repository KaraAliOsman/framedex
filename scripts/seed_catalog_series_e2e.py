"""Synthetic P02 browser data; requires a freshly owned local E2E tenant."""

import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit
from uuid import UUID

target = urlsplit(os.environ.get("DATABASE_URL", ""))
if target.hostname not in ("127.0.0.1", "localhost", "::1"):
    raise SystemExit("Catalog E2E seeding requires a local PostgreSQL instance")
root = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(root), str(root / "backend")]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django  # noqa: E402

django.setup()

from django.db import connection, transaction  # noqa: E402
from catalogs import series, service  # noqa: E402
from backend.tests.integration.test_catalog_series_sheet import create  # noqa: E402
from backend.tests.integration.test_catalog_use_levels import priced_series  # noqa: E402
from backend.tests.integration.test_shot09_documentary import as_user  # noqa: E402

org, actor = UUID(sys.argv[1]), UUID(sys.argv[2])
with transaction.atomic():
    with connection.cursor() as cursor:
        cursor.execute("SELECT o.name FROM public.tenancy_organizations o "
            "JOIN public.tenancy_memberships m ON m.org_id=o.id "
            "WHERE o.id=%s AND m.user_id=%s AND m.role='OWNER' AND m.is_active", [org, actor])
        tenant = cursor.fetchone()
        if not tenant or not tenant[0].startswith("DK2 E2E SYNTHETIC "):
            raise SystemExit("Refusing to seed a tenant not owned by this catalog test")
    with as_user(actor):
        sheet = priced_series(org, actor)
        current = service.retrieve(service.SYSTEMS, org, sheet["id"])
        service.update(service.SYSTEMS, org, sheet["id"], {"name": "PRO6004 · ensayo sintético"},
            expected_revision='"' + current["revision"] + '"', actor_id=actor)
        sheet = series.series_sheet(org, sheet["id"])
        if "--unpriced" in sys.argv[3:]:
            from pricing.repository import admin_write, rows

            for price_list in rows("SELECT id FROM public.cost_lists WHERE org_id=%s", [org]):
                admin_write("cost-lists", org, {"is_active": False},
                    "Synthetic setup starts without active purchase prices", price_list["id"])
        fields = ("sash_overlap_mm", "glass_clearance_white_mm", "glass_clearance_foil_mm",
            "rebate_depth_mm", "end_milling_overlap_mm")
        values = {item["field"]: item["value"] for item in sheet["cells"] if item["resource"] == "systems"}
        prepared = series.edit_cells(org, sheet["id"], actor, {"revision": sheet["revision"],
            "changes": [{"resource": "systems", "row_id": sheet["id"], "field": "rebate_depth_mm", "value": None}]})
        assert prepared["usage"]["level"] == "DRAWABLE"
        # Explicit synthetic stress values, never manufacturer claims.
        stress_profiles = [{
            "sku": f"DK2-STRESS-{index:03}",
            "name": (f"Perfil {index:03} de ensayo con nombre largo para comprobar la ficha de serie del taller " + "Ñ")[:80],
            "material": "PVC",
            "role": "FRAME" if index == 0 else "SASH" if index == 1 else "GLAZING_BEAD",
            "face_width_mm": "60.00",
            "commercial_length_mm": "6500.00", "weight_kg_m": "1.2345",
        } for index in range(0 if "--light" in sys.argv[3:] else 300)]
        stress = create(org, actor, name="300 perfiles · ensayo sintético",
            profiles=stress_profiles[:200], glazing=[], hardware=[]) if stress_profiles else sheet
        for profile in stress_profiles[200:]:
            validator = service.ARTICLES.serializer(data={**profile, "system_id": stress["id"]})
            assert validator.is_valid(), validator.errors
            service.create(service.ARTICLES, org, validator.validated_data, actor_id=actor)
        result = {"systemId": str(sheet["id"]), "stressId": str(stress["id"]),
            "pasteValues": [values[field] for field in fields]}
        if "--double-read" in sys.argv[3:]:
            from scripts.catalog_double_read_e2e import seed_manual

            result.update(seed_manual(org, actor, sheet))
print(json.dumps(result, ensure_ascii=False))
