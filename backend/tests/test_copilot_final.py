"""Dirección final 05–06: pure units of the copilot (attachments, receipts,
thread cursors) and the versioned quota policy. Database paths are covered
by the live gate and the REVIEW stack; these tests touch no database."""

from __future__ import annotations

import io
import zipfile
from datetime import datetime, timedelta, timezone

import pytest

from ai_gateway import attachments, postconditions, threads
from billing import capabilities, quota_policy

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _docx(body: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", f'<w:document xmlns:w="{W}"><w:body>{body}</w:body></w:document>')
    return buffer.getvalue()


def test_matrix_announces_only_real_adapters():
    kinds = {item["kind"] for item in attachments.matrix()["formats"]}
    assert kinds == {"PDF", "IMAGE", "XLSX", "CSV", "DOCX", "TEXT"}
    assert attachments.kind_of("Plano.PDF") == "PDF"
    assert attachments.kind_of("notas.md") == "TEXT"
    assert attachments.kind_of("foto.webp") == "IMAGE"
    assert attachments.kind_of("macro.xlsb") is None
    assert attachments.kind_of("setup.exe") is None


def test_docx_keeps_paragraph_and_table_origin():
    content = _docx(
        "<w:p><w:r><w:t>Listado revisión B</w:t></w:r></w:p>"
        "<w:tbl><w:tr><w:tc><w:p><w:r><w:t>V1</w:t></w:r></w:p></w:tc>"
        "<w:tc><w:p><w:r><w:t>1200 x 1000</w:t></w:r></w:p></w:tc></w:tr></w:tbl>"
    )
    assert attachments._sniff("DOCX", content)
    found = attachments.extract("DOCX", content)
    assert found["parts"] == [
        {"ref": "párrafo 1", "text": "Listado revisión B"},
        {"ref": "tabla 1 · fila 1", "text": "V1 | 1200 x 1000"},
    ]
    assert found["coverage"]["unprocessed_count"] == 0


def test_a_zip_without_document_is_not_docx():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("xl/workbook.xml", "<w/>")
    assert not attachments._sniff("DOCX", buffer.getvalue())


def test_text_and_csv_lines_keep_their_reference():
    text = attachments.extract("TEXT", "# Obra\n\n- V1 1200x1000\n".encode())
    assert [part["ref"] for part in text["parts"]] == ["línea 1", "línea 3"]
    csv = attachments.extract("CSV", "codigo;ancho\nV1;1200\n".encode())
    assert csv["parts"][1] == {"ref": "fila 2", "text": "V1;1200"}


def test_truncated_file_declares_what_was_not_processed(monkeypatch):
    monkeypatch.setattr(attachments, "MAX_TEXT_CHARS_PER_FILE", 12)
    found = attachments.extract("TEXT", "abcdefghij\nklmnopqrst\nuvw\n".encode())
    assert len(found["parts"]) == 1
    assert found["coverage"]["unprocessed"] == ["línea 2", "línea 3"]
    assert found["coverage"]["unprocessed_count"] == 2


def test_upload_refuses_unsupported_and_mismatched_files():
    with pytest.raises(attachments.AttachmentError) as unsupported:
        attachments.upload(org_id="o", user_id="u", file_name="a.exe", content=b"MZ")
    assert unsupported.value.code == "ai_attachment_unsupported"
    with pytest.raises(attachments.AttachmentError) as mismatch:
        attachments.upload(org_id="o", user_id="u", file_name="plano.pdf", content=b"not a pdf")
    assert mismatch.value.code == "ai_attachment_mismatch"
    with pytest.raises(attachments.AttachmentError) as unsafe:
        attachments.upload(org_id="o", user_id="u", file_name="../x.pdf", content=b"%PDF-1.4")
    assert unsafe.value.code == "ai_attachment_name_invalid"


def test_seal_limits_attachments_per_turn():
    with pytest.raises(attachments.AttachmentError) as limit:
        attachments.seal(org_id="o", user_id="u", ids=list(range(attachments.MAX_PER_TURN + 1)))
    assert limit.value.code == "ai_attachment_limit"


def _ops_step(**extra):
    return {"kind": "project_ops", "label": "Agregar 2 ventanas",
            "simulation": {"project_id": "11111111-1111-1111-1111-111111111111", "diff": []}, **extra}


def test_chat_or_propose_never_reports_applied():
    result = {"steps": [_ops_step()], "questions": [], "credits_debited": 8}
    for mode, policy in (("chat", "draft"), ("work", "propose")):
        receipt = postconditions.build_receipt(org_id="o", result=result, interaction_mode=mode,
                                               autonomy="propose" if mode == "chat" else policy)
        assert receipt["outcome"] == "proposal"
        assert all(item["status"] != "applied" for item in receipt["objects"])
        assert receipt["credits"] == 8


def test_approve_prepares_the_set_for_one_approval():
    receipt = postconditions.build_receipt(org_id="o", result={"steps": [_ops_step()], "questions": []},
                                           interaction_mode="work", autonomy="approve")
    assert receipt["outcome"] == "proposal"
    assert receipt["summary"].startswith("Conjunto preparado")


def test_draft_is_complete_only_when_saved_objects_verify(monkeypatch):
    step = _ops_step(applied={"operation_id": "op-1", "project_id": "11111111-1111-1111-1111-111111111111"})
    step["simulation"]["diff"] = [{"kind": "add", "before": None,
                                   "after": {"id": "p1", "position_index": 1, "quantity": 2}}]
    monkeypatch.setattr(postconditions, "_project_positions", lambda org, project: {"p1": {"quantity": 2}})
    receipt = postconditions.build_receipt(org_id="o", result={"steps": [step]}, interaction_mode="work",
                                           autonomy="draft")
    assert receipt["outcome"] == "complete"
    assert receipt["objects"][0]["operation_id"] == "op-1"

    monkeypatch.setattr(postconditions, "_project_positions", lambda org, project: {})
    missing = postconditions.build_receipt(org_id="o", result={"steps": [step]}, interaction_mode="work",
                                           autonomy="draft")
    assert missing["outcome"] == "blocked"
    assert "falta guardar" in missing["objects"][0]["cause"]


def test_partial_names_the_checkpoint_and_unread_parts():
    result = {"steps": [_ops_step(apply_error="La obra cambió")], "questions": ["¿Qué vidrio?"]}
    receipt = postconditions.build_receipt(
        org_id="o", result=result, interaction_mode="work", autonomy="draft",
        attachments=[{"id": "a", "file_name": "plano.pdf", "complete": False, "not_processed": ["página 9"]}],
    )
    assert receipt["outcome"] == "partial"
    assert receipt["checkpoint"]
    assert any("página 9" in check["detail"] for check in receipt["checks"])


def test_consequential_actions_stay_pending_for_the_human_click():
    result = {"steps": [{"kind": "prepare", "label": "Emitir cotización", "path": "/projects/x?section=quote"}]}
    receipt = postconditions.build_receipt(org_id="o", result=result, interaction_mode="work", autonomy="draft")
    assert receipt["objects"][0]["status"] == "pending"
    assert "clic" in receipt["objects"][0]["cause"]


def test_plain_answer_is_not_a_task():
    receipt = postconditions.build_receipt(org_id="o", result={"steps": [], "questions": []},
                                           interaction_mode="chat", autonomy="propose")
    assert receipt["outcome"] == "answer"


def test_thread_cursor_round_trips_and_rejects_garbage():
    moment = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)
    cursor = threads._encode_cursor(moment, "5eb24b61-970e-49ff-afb2-d2414bc69856")
    assert threads._decode_cursor(cursor) == (moment.isoformat(), "5eb24b61-970e-49ff-afb2-d2414bc69856")
    with pytest.raises(threads.ThreadError):
        threads._decode_cursor("not-a-cursor")


def test_thread_title_is_bounded():
    assert threads.title_from("  Agrega   una corredera ") == "Agrega una corredera"
    assert len(threads.title_from("x" * 500)) == threads.MAX_TITLE
    assert threads.title_from("") == "Conversación"


def test_legacy_quota_is_the_active_policy():
    assert quota_policy.resolve("PRO").included_credits == 2000
    assert quota_policy.resolve("BUSINESS").included_credits == 6000
    assert quota_policy.resolve("BUSINESS_2X").included_credits == 12000
    assert quota_policy.resolve("STARTER").included_credits == 0
    trial = quota_policy.resolve("TRIAL")
    assert (trial.included_credits, trial.window) == (500, "trial_total")
    assert quota_policy.resolve("PRO").policy_version == "allowances-legacy-v1"


def test_proportional_policy_is_integer_and_not_inferred_from_price():
    quota = quota_policy.proportional(1500, 3, terms_version="draft")
    assert (quota.included_credits, quota.unit_credits, quota.multiplier) == (4500, 1500, 3)
    with pytest.raises(ValueError):
        quota_policy.proportional(1500, 1.5, terms_version="draft")  # type: ignore[arg-type]


def test_entitlement_is_one_rule_for_every_path():
    now = datetime.now(timezone.utc)
    assert not capabilities.entitled({"subscription_tier": "STARTER", "subscription_active": True}, now)
    assert capabilities.entitled({"subscription_tier": "PRO", "subscription_active": True}, now)
    assert not capabilities.entitled({"subscription_tier": "PRO", "subscription_active": False}, now)
    live_trial = {"subscription_tier": "TRIAL", "subscription_active": False, "trial_ends_at": now + timedelta(days=3)}
    over_trial = {**live_trial, "trial_ends_at": now - timedelta(days=1)}
    assert capabilities.entitled(live_trial, now)
    assert not capabilities.entitled(over_trial, now)


def test_a_created_work_without_windows_is_partial(monkeypatch):
    monkeypatch.setattr(postconditions, "_project_positions", lambda org, project: {})
    result = {"steps": [], "created_project": {"project_id": "p", "code": "P-1", "name": "Obra"}}
    receipt = postconditions.build_receipt(org_id="o", result=result, interaction_mode="work", autonomy="draft")
    assert receipt["outcome"] == "partial"
    assert "continúa" in receipt["checkpoint"]
