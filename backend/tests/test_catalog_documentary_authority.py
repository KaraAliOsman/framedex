"""A new catalog must produce identical saved, priced and documentary BOMs."""

from decimal import Decimal
from uuid import uuid4

import pytest

from documents.service import _position_calculations
from engine_api.adapter import calculate_from_api
from dekopen_engine.snapshot import result_payload
from engine.tests.catalog_families import family_params


@pytest.mark.parametrize("color", ["WHITE", "FOILED", "DARK"])
def test_family_documentary_recalculation_matches_transport_and_finish(color: str) -> None:
    params = family_params("DEMO_60").model_copy(update={"finishes": ("WHITE", "FOILED", "DARK")})
    tree = {
        "id": "leaf", "type": "BAY", "opening_type": "TURN_LEFT",
        "glass_thickness_mm": "24.00", "glass_spec": "4-16-4 Float Incoloro",
        "glass_article_sku": "DEMO_60-VIDRIO-4-16-4",
    }
    strict = calculate_from_api(
        parametric_tree=tree, nominal_width_mm=Decimal("900.00"),
        nominal_height_mm=Decimal("900.00"), color=color, params=params,
    )
    _, documentary = _position_calculations(
        tree=tree, width_mm=Decimal("900.00"), height_mm=Decimal("900.00"),
        color=color, params=params, system_id=uuid4(), org_id=uuid4(),
    )
    assert documentary.model_dump(mode="json") == strict.model_dump(mode="json")
    assert documentary.model_dump(mode="json") == result_payload(strict)
    assert bool(documentary.reinforcements) is (color != "WHITE")
