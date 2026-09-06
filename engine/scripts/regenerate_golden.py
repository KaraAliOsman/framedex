"""`make goldgen` is the sole writer. CI uses --check and never writes bytes."""

from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path

from dekopen_engine import EngineResult, ParametricNode, calculate_geometry
from dekopen_engine.snapshot import calculation_response
from engine.tests.catalog import demo_60_params

SNAPSHOT = Path(__file__).resolve().parents[1] / "tests" / "golden_example.json"


def golden_request() -> dict[str, object]:
    return {
        "system_id": "3067da09-3119-5ad0-a1d5-498cd2dfd753",
        "nominal_width_mm": "1500.00",
        "nominal_height_mm": "1400.00",
        "color": "WHITE",
        "parametric_tree": {
            "id": "root", "type": "SPLIT_V", "split_offset_mm": "750.00",
            "mullion_profile_sku": "POSTE-V",
            "children": [
                {"id": "bay_1", "type": "BAY", "opening_type": "FIXED",
                 "glass_thickness_mm": "24.00", "glass_spec": "4-16-4 Float Incoloro"},
                {"id": "bay_2", "type": "BAY", "opening_type": "TILT_TURN_RIGHT",
                 "glass_thickness_mm": "20.00", "glass_spec": "4-12-4 Float Incoloro"},
            ],
        },
    }


def golden_result() -> EngineResult:
    request = golden_request()
    root = ParametricNode.model_validate_json(json.dumps(request["parametric_tree"]))
    root = root.model_copy(update={
        "width_mm": Decimal(str(request["nominal_width_mm"])),
        "height_mm": Decimal(str(request["nominal_height_mm"])),
    })
    return calculate_geometry(root, demo_60_params())


def generated_bytes() -> bytes:
    request = golden_request()
    envelope = {"request": request, "response": calculation_response(request, golden_result())}
    return (json.dumps(envelope, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            + "\n").encode("utf-8")


def check_snapshot(path: Path | None = None) -> bool:
    target = SNAPSHOT if path is None else path
    return target.is_file() and target.read_bytes() == generated_bytes()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare bytes; never rewrite")
    args = parser.parse_args()
    if args.check:
        if not check_snapshot():
            raise SystemExit("Golden byte drift: run make goldgen explicitly and review the diff")
        print("Golden byte check: PASS (read-only)")
    else:
        SNAPSHOT.write_bytes(generated_bytes())
        print(f"Generated {SNAPSHOT.relative_to(SNAPSHOT.parents[2]).as_posix()}")


if __name__ == "__main__":
    main()
