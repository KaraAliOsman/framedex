#!/usr/bin/env python3
"""Create a minimal implementation-plan scaffold for a Dekopen shot."""

from __future__ import annotations

import os
import re
import sys


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/new_shot.py SHOT-XX")
        raise SystemExit(1)

    shot_id = sys.argv[1].upper()
    if not re.fullmatch(r"SHOT-\d{2}", shot_id):
        print(f"Error: invalid shot format {shot_id!r}; expected SHOT-01 to SHOT-24.")
        raise SystemExit(1)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    plan_file = os.path.join(base_dir, "docs", "plans", "PLAN_{}.md".format(shot_id))
    shots_table_file = os.path.join(base_dir, "docs", "PRD", "PLAN_SHOTS.md")

    source_prd = "docs/PRD/PRD-XX.md"
    gate_desc = "Describe the observable acceptance gate from PLAN_SHOTS.md."
    shot_name = "Implementation of {}".format(shot_id)

    if os.path.exists(shots_table_file):
        with open(shots_table_file, encoding="utf-8") as shots_file:
            for line in shots_file:
                if "**{}**".format(shot_id) not in line:
                    continue
                parts = [part.strip() for part in line.split("|")]
                if len(parts) >= 6:
                    source_prd = parts[3]
                    shot_name = parts[4].replace("**", "")
                    gate_desc = parts[5].replace("**", "")
                break

    template = """# Plan — {shot_id}: {shot_name}

## Scope and authority

- **Shot:** '{shot_id}'
- **Source PRD:** '{source_prd}'
- **Acceptance gate:** {gate_desc}
- **Goal:** [Describe the observable result and authorized scope.]

## Contracts and affected surfaces

- **Upstream contracts:** [List the existing interfaces or decisions consumed.]
- **Downstream contracts:** [List future consumers that must remain compatible.]
- **Files/surfaces:** [List files, APIs, UI, database or engine surfaces.]
- **Out of scope:** [List explicitly excluded capabilities.]

## Verification

Select checks from the changed proof surface:
- Focused tests/checkers: [commands and expected evidence]
- Broader module or integration checks: [only where justified]
- Canonical closure: 'python scripts/check_dod.py all' is required for the final material
  implementation head of a SHOT.

## Decisions and evidence

- Material contradiction or gap: [None, or '[PENDIENTE-DECISIÓN]' with the exact question.]
- SHA-bound evidence: [Record the commit, gate, result and covered surface.]
""".format(
        shot_id=shot_id,
        shot_name=shot_name,
        source_prd=source_prd,
        gate_desc=gate_desc,
    )

    os.makedirs(os.path.dirname(plan_file), exist_ok=True)
    if os.path.exists(plan_file):
        print("[INFO] Plan already exists: {}".format(plan_file))
        return

    with open(plan_file, "w", encoding="utf-8", newline="\n") as plan_handle:
        plan_handle.write(template)
    print("[OK] Created plan scaffold: {}".format(plan_file))


if __name__ == "__main__":
    main()
