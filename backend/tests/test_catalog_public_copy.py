"""Public catalog schema keeps workshop language and versioned file compatibility."""

import re

from ingest.catalog_template import SCHEMAS, candidate, public_schema


def test_public_labels_and_required_errors_use_workshop_language():
    forbidden = re.compile(r"\b(?:autoridad(?:es)?|sellad[oa]s?|fuentes?|procedencias?|sin datos?)\b", re.I)
    for sheet in public_schema()["sheets"]:
        for column in sheet["columns"]:
            assert not forbidden.search(column["label"]), column
    row = candidate("Sistemas", {}, key="missing", row=1, method="MANUAL")
    assert row["errors"]
    for error in row["errors"]:
        assert not forbidden.search(error["message"]), error
    # The canonical input workbook retains its headers and therefore its parser.
    assert next(column for column in SCHEMAS["Sistemas"] if column.key == "source").label == "Fuente"
