"""`make goldgen` is the sole writer. CI uses --check and never writes bytes."""

from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path

from dekopen_engine import EngineResult, ParametricNode, calculate_geometry
from dekopen_engine.snapshot import calculation_response
from engine.tests.catalog import demo_60_params
from engine.tests.catalog_families import family_cases
from engine.tests.glass_cases import glass_cases
from engine.tests.opening_cases import opening_cases
from engine.tests.hardware_cases import hardware_cases
from engine.tests.finish_cases import finish_cases
from engine.tests.extra_cases import extra_cases
from engine.tests.mounting_cases import mounting_cases
from engine.tests.operation_cases import operation_cases
from engine.tests.ai_cost_cases import ai_cost_cases
from engine.tests.quotation_cases import quotation_cases
from engine.tests.workspace_cases import workspace_cases
from engine.tests.assembly_cases import assembly_cases

SNAPSHOT = Path(__file__).resolve().parents[1] / "tests" / "golden_example.json"
FAMILY_SNAPSHOT = SNAPSHOT.with_name("golden_catalog_families.json")
GLASS_SNAPSHOT = SNAPSHOT.with_name("golden_glass_products.json")
OPENING_SNAPSHOT = SNAPSHOT.with_name("golden_openings.json")
HARDWARE_SNAPSHOT = SNAPSHOT.with_name("golden_hardware_classes.json")
FINISH_SNAPSHOT = SNAPSHOT.with_name("golden_finishes.json")
EXTRA_SNAPSHOT = SNAPSHOT.with_name("golden_extras.json")
MOUNTING_SNAPSHOT = SNAPSHOT.with_name("golden_mounting.json")
OPERATION_SNAPSHOT = SNAPSHOT.with_name("golden_design_operations.json")
AI_COST_SNAPSHOT = SNAPSHOT.with_name("golden_ai_cost.json")
QUOTATION_SNAPSHOT = SNAPSHOT.with_name("golden_quotation.json")
WORKSPACE_SNAPSHOT = SNAPSHOT.with_name("golden_price_workspace.json")
ASSEMBLY_SNAPSHOT = SNAPSHOT.with_name("golden_assemblies.json")


def generated_assembly_bytes() -> bytes:
    return (json.dumps(assembly_cases(),ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n").encode('utf-8')


def generated_workspace_bytes() -> bytes:
    return (json.dumps(workspace_cases(),ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n").encode('utf-8')


def generated_quotation_bytes() -> bytes:
    return (json.dumps(quotation_cases(), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def generated_ai_cost_bytes() -> bytes:
    return (json.dumps(ai_cost_cases(), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def generated_operation_bytes() -> bytes:
    return (json.dumps(operation_cases(), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def generated_mounting_bytes() -> bytes:
    return (json.dumps(mounting_cases(), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+"\n").encode("utf-8")


def generated_extra_bytes() -> bytes:
    return (json.dumps(extra_cases(),ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n").encode("utf-8")


def generated_finish_bytes() -> bytes:
    return (json.dumps(finish_cases(), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            + "\n").encode("utf-8")


def generated_hardware_bytes() -> bytes:
    return (json.dumps(hardware_cases(), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            + "\n").encode("utf-8")


def generated_opening_bytes() -> bytes:
    return (json.dumps(opening_cases(), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            + "\n").encode("utf-8")


def generated_glass_bytes() -> bytes:
    return (json.dumps(glass_cases(), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            + "\n").encode("utf-8")


def generated_family_bytes() -> bytes:
    return (json.dumps(family_cases(), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            + "\n").encode("utf-8")


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
        if not ASSEMBLY_SNAPSHOT.is_file() or ASSEMBLY_SNAPSHOT.read_bytes()!=generated_assembly_bytes():
            raise SystemExit('Assembly golden byte drift: run make goldgen and review the diff')
        if not WORKSPACE_SNAPSHOT.is_file() or WORKSPACE_SNAPSHOT.read_bytes() != generated_workspace_bytes():
            raise SystemExit('Price workspace golden byte drift: run make goldgen and review the diff')
        if (not check_snapshot() or not FAMILY_SNAPSHOT.is_file()
                or FAMILY_SNAPSHOT.read_bytes() != generated_family_bytes()):
            raise SystemExit("Golden byte drift: run make goldgen explicitly and review the diff")
        if not GLASS_SNAPSHOT.is_file() or GLASS_SNAPSHOT.read_bytes() != generated_glass_bytes():
            raise SystemExit("Glass golden byte drift: run make goldgen and review the diff")
        if not OPENING_SNAPSHOT.is_file() or OPENING_SNAPSHOT.read_bytes() != generated_opening_bytes():
            raise SystemExit("Opening golden byte drift: run make goldgen and review the diff")
        if not HARDWARE_SNAPSHOT.is_file() or HARDWARE_SNAPSHOT.read_bytes() != generated_hardware_bytes():
            raise SystemExit("Hardware golden byte drift: run make goldgen and review the diff")
        print("Golden byte check: PASS (read-only)")
        if not FINISH_SNAPSHOT.is_file() or FINISH_SNAPSHOT.read_bytes() != generated_finish_bytes():
            raise SystemExit("Finish golden byte drift: run make goldgen and review the diff")
        if not EXTRA_SNAPSHOT.is_file() or EXTRA_SNAPSHOT.read_bytes() != generated_extra_bytes():
            raise SystemExit("Accessory golden byte drift: run make goldgen and review the diff")
        if not MOUNTING_SNAPSHOT.is_file() or MOUNTING_SNAPSHOT.read_bytes() != generated_mounting_bytes():
            raise SystemExit("Mounting golden byte drift: run make goldgen and review the diff")
        if not OPERATION_SNAPSHOT.is_file() or OPERATION_SNAPSHOT.read_bytes() != generated_operation_bytes():
            raise SystemExit("Editing golden byte drift: run make goldgen and review the diff")
        if not AI_COST_SNAPSHOT.is_file() or AI_COST_SNAPSHOT.read_bytes() != generated_ai_cost_bytes():
            raise SystemExit("AI cost golden byte drift: run make goldgen and review the diff")
        if not QUOTATION_SNAPSHOT.is_file() or QUOTATION_SNAPSHOT.read_bytes() != generated_quotation_bytes():
            raise SystemExit("Quotation golden byte drift: run make goldgen and review the diff")
    else:
        ASSEMBLY_SNAPSHOT.write_bytes(generated_assembly_bytes())
        WORKSPACE_SNAPSHOT.write_bytes(generated_workspace_bytes())
        SNAPSHOT.write_bytes(generated_bytes())
        FAMILY_SNAPSHOT.write_bytes(generated_family_bytes())
        GLASS_SNAPSHOT.write_bytes(generated_glass_bytes())
        OPENING_SNAPSHOT.write_bytes(generated_opening_bytes())
        HARDWARE_SNAPSHOT.write_bytes(generated_hardware_bytes())
        FINISH_SNAPSHOT.write_bytes(generated_finish_bytes())
        EXTRA_SNAPSHOT.write_bytes(generated_extra_bytes())
        MOUNTING_SNAPSHOT.write_bytes(generated_mounting_bytes())
        OPERATION_SNAPSHOT.write_bytes(generated_operation_bytes())
        AI_COST_SNAPSHOT.write_bytes(generated_ai_cost_bytes())
        QUOTATION_SNAPSHOT.write_bytes(generated_quotation_bytes())
        print(f"Generated {SNAPSHOT.relative_to(SNAPSHOT.parents[2]).as_posix()}")


if __name__ == "__main__":
    main()
