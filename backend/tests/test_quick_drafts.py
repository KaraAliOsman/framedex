"""Quick drafts: any PDF from a name and one window, nothing stored."""

from __future__ import annotations

from contextlib import contextmanager

import pytest

from documents import quick_drafts, renderers, workshop_layouts
from documents.issuance_views import QuickDraftRequestSerializer
from documents.repository import DocumentaryError


def test_every_quick_document_maps_to_a_renderer_and_name():
    assert set(quick_drafts.QUICK_DOCUMENTS) == {"QUOTE", "CUT", "PLAN", "MATERIALS"}
    assert quick_drafts.QUICK_DOCUMENTS["PLAN"][:2] == ("DOC-03", "PLANO")
    assert all(name.endswith("-borrador") for _, _, name in quick_drafts.QUICK_DOCUMENTS.values())


def test_request_accepts_only_known_documents():
    assert QuickDraftRequestSerializer(data={"document": "CUT"}).is_valid()
    assert not QuickDraftRequestSerializer(data={"document": "DOC-07"}).is_valid()
    assert not QuickDraftRequestSerializer(data={"document": "CUT", "extra": 1}).is_valid()


@pytest.mark.parametrize("gate", [renderers._require_production, workshop_layouts._require_production])
def test_shop_documents_stay_blocked_unless_they_are_a_draft(gate):
    with pytest.raises(DocumentaryError, match="production_document_blocked"):
        gate({"production_allowed": False, "documentary_complete": False})
    with pytest.raises(DocumentaryError, match="manufacturing_document_incomplete"):
        gate({"production_allowed": True, "documentary_complete": False})
    gate({"production_allowed": False, "documentary_complete": False, "draft": True})


def test_suggestions_fill_only_what_a_person_did_not_declare():
    position = {
        "workshop_annotations": [{"bay_id": "b1", "leaf_id": None, "finish_class": "A",
                                  "has_coupler": None}],
        "workshop_suggestions": [
            {"bay_id": "b1", "leaf_id": None, "finish_class": "B", "has_coupler": False},
            {"bay_id": "b2", "leaf_id": "l1", "finish_class": "C"},
        ],
        "glass_polishing": [{"bay_id": "b1", "leaf_id": None, "edges": ["TOP"]}],
        "polishing_suggestions": [{"bay_id": "b1", "leaf_id": None, "edges": []},
                                  {"bay_id": "b2", "leaf_id": "l1", "edges": []}],
    }
    merged = quick_drafts._with_suggestions(position)
    first, second = merged["workshop_annotations"]
    assert first["finish_class"] == "A" and first["has_coupler"] is False
    assert second["bay_id"] == "b2"
    assert merged["glass_polishing"] == [{"bay_id": "b1", "leaf_id": None, "edges": ["TOP"]},
                                         {"bay_id": "b2", "leaf_id": "l1", "edges": []}]


def test_first_option_never_overrides_a_declared_policy():
    position = {"policy": "kept", "options": [{"id": "first"}]}
    assert quick_drafts._first_option(position, "policy", "options") == "kept"
    assert quick_drafts._first_option({"options": [{"id": "first"}]}, "policy", "options") == "first"
    assert quick_drafts._first_option({}, "policy", "options") is None


def test_render_always_rolls_back_what_the_draft_needed(monkeypatch):
    exits = []

    @contextmanager
    def atomic():
        try:
            yield
        except BaseException as error:
            exits.append(type(error).__name__)
            raise
        exits.append("commit")

    monkeypatch.setattr(quick_drafts.transaction, "atomic", atomic)
    monkeypatch.setattr(quick_drafts, "_compose", lambda **_: b"%PDF-1.7 draft")
    content, name = quick_drafts.render(object(), "project", "CUT")
    assert content == b"%PDF-1.7 draft"
    assert name == "hoja-de-corte-borrador"
    assert exits == ["_Discard"]


def test_a_failed_draft_raises_and_still_rolls_back(monkeypatch):
    exits = []

    @contextmanager
    def atomic():
        try:
            yield
        except BaseException as error:
            exits.append(type(error).__name__)
            raise

    def failing(**_):
        raise DocumentaryError("revision_not_available")

    monkeypatch.setattr(quick_drafts.transaction, "atomic", atomic)
    monkeypatch.setattr(quick_drafts, "_compose", failing)
    with pytest.raises(DocumentaryError):
        quick_drafts.render(object(), "project", "QUOTE")
    assert exits == ["DocumentaryError"]
