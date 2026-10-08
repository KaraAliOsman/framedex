"""Export the engine's drawing grammar. --check rejects stale frontend tables."""
import argparse
import json
import re
from pathlib import Path

from dekopen_engine.models import HingeSide, LeafRole, Opening, OpeningDirection, OpeningMovement, SlidingTravel
from dekopen_engine.symbols import SYMBOL_TEMPLATES, symbol_names


def source() -> str:
    motions = {}
    for motion in OpeningMovement:
        for hinge in (HingeSide.LEFT, HingeSide.RIGHT, HingeSide.NONE):
            for travel in (None, SlidingTravel.LEFT, SlidingTravel.RIGHT):
                # Deliberately diagram-only: these are not catalogue capabilities.
                opening = Opening.model_construct(movement=motion, hinge_side=hinge,
                    direction=OpeningDirection.INWARD, leaf_role=LeafRole.SINGLE, fixed_in_sash=False)
                motions[f"{motion.value}/{hinge.value}/{travel.value if travel else ''}"] = symbol_names(opening, travel)
    return ("// Generated from dekopen_engine.symbols; do not edit.\n"
            + "export const symbolTemplates = " + json.dumps(SYMBOL_TEMPLATES, indent=2) + " as const;\n"
            + "export const symbolMotions: Record<string, readonly (keyof typeof symbolTemplates)[]> = "
            + json.dumps(motions, indent=2) + ";\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = Path(__file__).resolve().parents[1] / "frontend/src/ui/openingSymbols.generated.ts"
    result = source()
    if args.check:
        # Prettier's formatting is checked separately; compare the exported data.
        current = path.read_text(encoding="utf-8")
        def compact(value: str) -> str:
            value = re.sub(r'"([A-Za-z_]\w*)":', r'\1:', value)
            return "".join(value.split()).replace(",}", "}").replace(",]", "]")
        if compact(current) != compact(result):
            print("Opening grammar is stale. Run python scripts/generate_opening_symbols.py.")
            return 1
    else:
        path.write_text(result, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
