"""Evidence is a current-value assertion; a human stamp is not certification."""
from datetime import datetime, timezone
from types import SimpleNamespace
from decimal import Decimal
import json

from catalogs import provenance


def test_decimal_evidence_is_exact_and_never_rounds_to_match():
    row = {"face_width_mm": Decimal("60.01")}
    assert provenance.evidence_matches(row, {"field_name": "face_width_mm", "canonical_value": '"60.010"'})
    assert not provenance.evidence_matches(row, {"field_name": "face_width_mm", "canonical_value": '"60"'})
    assert provenance.evidence_matches({"name": "Marco"}, {"field_name": "name", "canonical_value": "Marco"})


def test_correction_is_not_manufacturer_evidence_and_demo_stamp_never_verifies(monkeypatch):
    resource = SimpleNamespace(table="profile_systems", fields=["depth_mm"])
    now = datetime.now(timezone.utc)
    evidence = {"row_id": "a", "field_name": "depth_mm", "canonical_value": '"60"',
                "review_state": "REVIEWED", "source_ref": "Página 1", "extraction_method": "HUMAN_CORRECTION"}
    monkeypatch.setattr(provenance, "rows", lambda sql, args: [evidence] if "catalog_parameter_evidence" in sql else [{"label": "Técnico"}])
    row = {"id": "a", "data_provenance": "IMPORT", "depth_mm": Decimal(60),
           "technical_reviewed_at": now, "technical_reviewed_by": "t", "review_pending": False}
    provenance.decorate(resource, [row], "org")
    assert row["authority_provenance"]["state"] == "REVIEWED"
    evidence["extraction_method"] = "AI"
    provenance.decorate(resource, [row], "org")
    assert row["authority_provenance"]["state"] == "VERIFIED"
    row["is_demo"] = True
    provenance.decorate(resource, [row], "org")
    assert row["authority_provenance"]["state"] == "DEMO"
    row["is_demo"] = False
    row["depth_mm"] = Decimal("60.01")
    provenance.decorate(resource, [row], "org")
    assert row["authority_provenance"]["state"] == "REVIEWED"


def test_section_without_declared_interpretation_never_becomes_verified():
    section = {"source": "POLYGON", "depth_mm": "60", "polygon": [
        {"x_mm": "0", "y_mm": "0"}, {"x_mm": "40", "y_mm": "0"},
        {"x_mm": "40", "y_mm": "60"}, {"x_mm": "0", "y_mm": "60"}]}
    assert not provenance.section_facts({"section": section})["valid"]
    section.update(orientation="EXTERIOR_DOWN", local_origin="TOP_LEFT")
    assert provenance.section_facts({"section": section})["valid"]
    section["depth_mm"] = "60.01"
    assert not provenance.section_facts({"section": json.loads(json.dumps(section))})["valid"]


def test_kit_mass_evidence_does_not_verify_unsourced_component_quantities(monkeypatch):
    resource = SimpleNamespace(table="hardware_kits", fields=["total_kg", "contents"])
    row = {"id": "kit", "system_id": None, "data_provenance": "IMPORT",
           "total_kg": Decimal("0.50"), "contents": [{"sku": "HINGE", "qty": "3"}],
           "technical_reviewed_at": datetime.now(timezone.utc),
           "technical_reviewed_by": "reviewer", "review_pending": False}
    attestation = {"row_id": "kit", "field_name": "total_kg", "canonical_value": '"0.50"',
                   "review_state": "REVIEWED", "source_ref": "Página 1", "extraction_method": "AI"}
    evidence = [attestation]
    monkeypatch.setattr(provenance, "rows", lambda sql, args: evidence if "catalog_parameter_evidence" in sql
                        else [] if "SELECT is_demo" in sql else [{"label": "Revisor técnico"}])
    provenance.decorate(resource, [row], "org")
    assert row["authority_provenance"]["state"] == "REVIEWED"
    assert row["authority_provenance"]["missing_fields"] == ["contents"]
    evidence.append({**attestation, "field_name": "contents", "canonical_value": row["contents"]})
    provenance.decorate(resource, [row], "org")
    assert row["authority_provenance"]["state"] == "VERIFIED"


def test_many_profiles_share_parent_and_reviewer_queries_without_sharing_evidence(monkeypatch):
    resource = SimpleNamespace(table="profile_articles", fields=["face_width_mm"])
    now = datetime.now(timezone.utc)
    records = [{"id": str(index), "system_id": "real" if index else "demo",
        "face_width_mm": Decimal("60"), "data_provenance": "IMPORT",
        "technical_reviewed_at": now, "technical_reviewed_by": "reviewer", "review_pending": False}
        for index in range(300)]
    evidence = {"row_id": "1", "field_name": "face_width_mm", "canonical_value": '"60"',
        "review_state": "REVIEWED", "source_ref": "Página 1", "extraction_method": "AI"}
    calls = []
    def fetch(sql, args):
        calls.append(sql)
        if "catalog_parameter_evidence" in sql:
            return [evidence]
        if "profile_systems" in sql:
            assert set(args[0]) == {"real", "demo"}
            return [{"id": "real", "is_demo": False}, {"id": "demo", "is_demo": True}]
        assert args == ["reviewer", "org"]
        return [{"label": "Técnico del taller"}]
    monkeypatch.setattr(provenance, "rows", fetch)
    provenance.decorate(resource, records, "org")
    assert len(calls) == 3
    assert records[0]["authority_provenance"]["state"] == "DEMO"
    assert records[1]["authority_provenance"]["state"] == "VERIFIED"
    assert all(row["authority_provenance"]["state"] == "REVIEWED" for row in records[2:])
    assert all(row["authority_provenance"]["reviewer"] == "Técnico del taller" for row in records)
