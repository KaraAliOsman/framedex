"""A series prepared from the library draws the owner's real PRO6004 windows."""

from decimal import Decimal

import pytest

from catalogs import series
from catalogs.reference_views import registry
from catalogs.series_serializers import SeriesCreateSerializer
from dekopen_engine import BayOpeningType, NodeType, ParametricNode, ProfileRole, calculate_geometry
from engine_api.repository import SystemParamsRepository

from .test_shot09_documentary import as_user, documentary_tenant as documentary_tenant

pytestmark = pytest.mark.rls_integration
D = Decimal


def prepare(org, actor):
    reference = next(item for item in registry()["series"] if item["id"] == "proline-pro6004")
    technical = reference["technical"]
    strip = lambda row: {key: value for key, value in row.items() if key not in ("source", "pages")}  # noqa: E731
    validator = SeriesCreateSerializer(data={
        "template_id": "pvc-casement-60-70", "template_version": 1,
        "name": reference["seed"]["name"], "code": reference["seed"]["code"],
        "manufacturer": reference["seed"]["manufacturer"],
        "rules": {"depth_mm": reference["seed"]["depth_mm"], "chamber_count": int(reference["seed"]["chamber_count"]),
                  **technical["rules"]},
        "profiles": [strip(row) for row in technical["profiles"]],
        "glazing": [strip(row) for row in technical["glazing"]],
        "hardware": [strip(row) for row in technical["hardware"]],
    })
    assert validator.is_valid(), validator.errors
    return series.create_from_template(org, actor, validator.validated_data)


def test_prepared_pro6004_draws_item_05_of_the_owners_work_order(documentary_tenant):
    org, _, users, _ = documentary_tenant
    with as_user(users["OWNER"]):
        sheet = prepare(org, users["OWNER"])
        params = SystemParamsRepository().load_visible(sheet["id"], org)
        glass = dict(type=NodeType.BAY, glass_thickness_mm=D("20.00"), glass_spec="4-12-4")
        node = ParametricNode(id="i05", type=NodeType.SPLIT_V, width_mm=D("1193"), height_mm=D("1358"),
            split_offset_mm=D("596.5"), mullion_profile_sku="PRO03", children=[
                ParametricNode(id="fix", opening_type=BayOpeningType.FIXED, **glass),
                ParametricNode(id="turn", opening_type=BayOpeningType.TURN_RIGHT, **glass)])
        result = calculate_geometry(node, params)
        def lengths(role, bay=None):
            return sorted(cut.length_mm for cut in result.profile_cuts
                          if cut.role is role and (bay is None or cut.bay_id == bay))
        # Every value is printed in the owner's work order N° 385, page 7.
        assert lengths(ProfileRole.FRAME) == [D("1199.00"), D("1364.00")]
        assert lengths(ProfileRole.MULLION_V) == [D("1358.00")]
        assert lengths(ProfileRole.SASH) == [D("554.50"), D("1292.00")]
        assert lengths(ProfileRole.GLAZING_BEAD, "fix") == [D("532.50"), D("1270.00")]
        assert {(g.bay_id, g.width_mm, g.height_mm) for g in result.glasses} == {
            ("fix", D("522.50"), D("1260.00")), ("turn", D("418.50"), D("1156.00"))}
        steel = {piece.role: [] for piece in result.reinforcements}
        for piece in result.reinforcements:
            steel[piece.role].append(piece.length_mm)
        assert sorted(steel[ProfileRole.FRAME]) == [D("1085.00"), D("1250.00")]
        assert steel[ProfileRole.MULLION_V] == [D("1338.00")]
