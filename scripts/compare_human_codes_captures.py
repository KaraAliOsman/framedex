"""Compare P02 findings with the preserved P00/P01 detector baseline.

Keep occurrence deltas visible: the exercised purchase adds real fixture rows,
so repeated legacy SKU tokens are not a new kind of presentation defect.
Never suppress a new signature or a numeric finding in the final surface.
"""
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/redesign/captures/identificadores-humanos"
NUMERIC = {"uuid", "hex", "decimal-precision", "percent-precision"}


def signature(issue):
    return issue["kind"], issue.get("match", "")


def main():
    records = []
    for route in ("panel", "proyectos", "proyecto-detalle", "compras", "produccion"):
        before = json.loads((ROOT / "antes" / route / "report.json").read_text(encoding="utf-8"))
        after = json.loads((ROOT / "despues" / route / "report.json").read_text(encoding="utf-8"))
        baseline = {(row["role"], row["theme"], row["viewport"]): row for row in before["records"]}
        for current in after["records"]:
            old = baseline[(current["role"], current["theme"], current["viewport"])]
            known = {signature(issue) for issue in old["findings"]}
            old_counts = Counter(signature(issue) for issue in old["findings"])
            new_counts = Counter(signature(issue) for issue in current["findings"])
            row = {
                "route": route, "role": current["role"], "theme": current["theme"], "viewport": current["viewport"],
                "numeric_findings": [issue for issue in current["findings"] if issue["kind"] in NUMERIC],
                "introduced_findings": [issue for issue in current["findings"] if signature(issue) not in known],
                "increased_legacy_occurrences": [{"kind": kind, "match": match, "delta": count - old_counts[(kind, match)]}
                    for (kind, match), count in new_counts.items() if count > old_counts[(kind, match)] and (kind, match) in known],
                "overflow_before": old["overflowX"], "overflow_after": current["overflowX"],
            }
            records.append(row)
    (ROOT / "comparacion.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    assert len(records) == 40
    assert not any(row["numeric_findings"] or row["introduced_findings"] for row in records)
    assert not any(row["overflow_after"] and not row["overflow_before"] for row in records)
    print("P02 40 comparisons: zero numeric findings, zero new signatures, zero new overflow. Legacy occurrence deltas retained.")


if __name__ == "__main__":
    main()
