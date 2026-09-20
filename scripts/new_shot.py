#!/usr/bin/env python3
"""Create a minimal implementation-plan scaffold for a Dekopen shot."""

from __future__ import annotations

import os
import re
import sys


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if len(sys.argv) != 2:
        print("Usage: python scripts/new_shot.py SHOT-XX")
        raise SystemExit(1)

    shot_id = sys.argv[1].upper()
    if not re.fullmatch(r"SHOT-(0[1-9]|1[0-9]|2[0-4])", shot_id):
        print(f"Error: invalid shot format {shot_id!r}; expected SHOT-01 to SHOT-24.")
        raise SystemExit(1)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    plan_file = os.path.join(base_dir, "docs", "plans", "PLAN_{}.md".format(shot_id))
    shots_table_file = os.path.join(base_dir, "docs", "PRD", "PLAN_SHOTS.md")

    if os.path.exists(plan_file):
        print(f"[INFO] Plan already exists: {plan_file}")
        return

    source_prd = gate_desc = shot_name = ""

    if os.path.exists(shots_table_file):
        with open(shots_table_file, encoding="utf-8") as shots_file:
            for line in shots_file:
                parts = [part.strip() for part in line.split("|")]
                if len(parts) == 7 and parts[1] == f"**{shot_id}**":
                    source_prd = parts[3]
                    shot_name = parts[4].replace("**", "")
                    gate_desc = parts[5].replace("**", "")
                    break

    if not all((source_prd, shot_name, gate_desc)):
        print(f"Error: no complete roadmap row for {shot_id} in {shots_table_file}.")
        raise SystemExit(1)

    template = """# Plan — {shot_id}: {shot_name}

## Scope and authority

- **Shot:** `{shot_id}`
- **Source PRD:** {source_prd}
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
- Closure and evidence reuse: [Constitution Rule 19](../CONSTITUTION.md).

## Decisions and evidence

- Material contradiction or gap: [None, or `[PENDIENTE-DECISIÓN]` with the exact question.]
- SHA-bound evidence: [Record the commit, gate, result and covered surface.]
""".format(
        shot_id=shot_id,
        shot_name=shot_name,
        source_prd=source_prd,
        gate_desc=gate_desc,
    )

    os.makedirs(os.path.dirname(plan_file), exist_ok=True)
    try:
        with open(plan_file, "x", encoding="utf-8", newline="\n") as plan_handle:
            plan_handle.write(template)
    except FileExistsError:
        print(f"[INFO] Plan already exists: {plan_file}")
        return
    print("[OK] Created plan scaffold: {}".format(plan_file))


if __name__ == "__main__":
    main()
