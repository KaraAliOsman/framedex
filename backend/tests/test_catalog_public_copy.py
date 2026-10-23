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


def test_process_picker_preserves_custom_names_and_the_stored_catalog(monkeypatch):
    from catalogs import service

    stored = [
        {"id": "global", "org_id": None, "code": "GENERIC_LEGACY", "label": "Nombre histórico", "version": 1},
        {"id": "own", "org_id": "org", "code": "GENERIC_LEGACY", "label": "Ruta propia del taller", "version": 2},
        {"id": "pvc", "org_id": None, "code": "PVC_WELDED", "label": "PVC", "version": 1},
    ]
    monkeypatch.setattr(service, "_rows_dicts", lambda query, params: stored)
    options = service.process_profile_options("org")
    assert options[0] == {**stored[0], "label": "Genérico · proceso por completar"}
    assert options[1:] == stored[1:]
    assert stored[0]["label"] == "Nombre histórico"
