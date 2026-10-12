"""Synthetic DEMO DOC-01: all geometry and money come from the engine."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django  # noqa: E402
django.setup()
from backend.tests.doc01_cases import proposal_case  # noqa: E402
from documents.renderers import render_pdf_document  # noqa: E402


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tmp" / "pdfs" / "doc01"
    target.mkdir(parents=True, exist_ok=True)
    cases = {str(count): proposal_case(count) for count in (1, 12, 24, 100)}
    cases["usd"] = proposal_case(12, "USD")
    cases["long-names"] = proposal_case(100, long_names=True)
    cases["a4"] = proposal_case(12, paper="A4")
    cases["oficio"] = proposal_case(12, paper="OFICIO")
    for name, snapshot in cases.items():
        content, _ = render_pdf_document("DOC-01", snapshot, pdf_identifier="fixture-" + name,
            portal_url="https://example.test/cotizacion/demo-revision-bound-token")
        (target / f"doc01-{name}.pdf").write_bytes(content)
        print(f"DOC-01 {name}: {len(snapshot['positions'])} posiciones DEMO; {len(content)} bytes")


if __name__ == "__main__":
    main()
