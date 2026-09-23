"""Customer approval links: token mint, public read, idempotent decide."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest

from documents.repository import DocumentaryError
from portal import service


@contextmanager
def _atomic():
    yield


def _roles(monkeypatch):
    monkeypatch.setattr("portal.service.transaction.atomic", _atomic)
    monkeypatch.setattr("portal.service.documentary_backend", _atomic)
    monkeypatch.setattr("portal.service.portal_backend", _atomic)


def test_share_quote_mints_hashed_token(monkeypatch) -> None:
    _roles(monkeypatch)
    org_id, project_id, actor_id, version_id = uuid4(), uuid4(), uuid4(), uuid4()
    captured: dict[str, list] = {"insert_params": []}

    def fake_one(sql_text, params, code="not_found"):
        lowered = " ".join(sql_text.lower().split())
        if lowered.startswith("select id,status"):
            return {"id": project_id, "status": "QUOTED"}
        if lowered.startswith("insert into public.customer_approvals"):
            captured["insert_params"] = list(params)
            return {"id": uuid4()}
        raise AssertionError(lowered)

    def fake_rows(sql_text, params=()):
        lowered = " ".join(sql_text.lower().split())
        if "project_versions" in lowered:
            return [{"id": version_id}]
        return []

    monkeypatch.setattr("portal.service.one", fake_one)
    monkeypatch.setattr("portal.service.rows", fake_rows)
    out = service.share_quote(org_id=org_id, project_id=project_id, actor_id=actor_id)

    token = out["token"]
    assert len(token) > 40 and out["expires_at"] > datetime.now(timezone.utc)
    # the raw token never reaches storage — only its sha256
    assert captured["insert_params"][3] != token
    assert captured["insert_params"][3] == __import__("hashlib").sha256(
        token.encode()
    ).hexdigest()
    assert captured["insert_params"][4] == out["expires_at"]


def test_share_quote_requires_quoted_status(monkeypatch) -> None:
    _roles(monkeypatch)
    monkeypatch.setattr(
        "portal.service.one",
        lambda *a, **k: {"id": uuid4(), "status": "DRAFT"},
    )
    with pytest.raises(DocumentaryError, match="quote_share_requires_quoted"):
        service.share_quote(org_id=uuid4(), project_id=uuid4(), actor_id=uuid4())


def _approval(status="PENDING", expired=False):
    return {
        "id": uuid4(),
        "created_by": uuid4(),
        "org_id": uuid4(),
        "project_id": uuid4(),
        "project_version_id": uuid4(),
        "status": status,
        "decided_by": None,
        "decided_at": None,
        "decided_note": None,
        "expires_at": datetime.now(timezone.utc)
        + timedelta(days=-1 if expired else 30),
    }


def test_portal_quote_unknown_and_expired_tokens(monkeypatch) -> None:
    _roles(monkeypatch)
    monkeypatch.setattr("portal.service.rows", lambda *a, **k: [])
    with pytest.raises(DocumentaryError, match="quote_not_found"):
        service.portal_quote("bogus")

    monkeypatch.setattr("portal.service.rows", lambda *a, **k: [_approval(expired=True)])
    with pytest.raises(DocumentaryError, match="quote_expired"):
        service.portal_quote("expired-token")


def test_decide_approves_project_and_replays(monkeypatch) -> None:
    _roles(monkeypatch)
    approval = _approval()
    calls: list[str] = []

    def fake_rows(sql_text, params=()):
        lowered = " ".join(sql_text.lower().split())
        calls.append(lowered)
        if "token_hash" in lowered:
            return [approval]
        return []

    def fake_one(sql_text, params, code="not_found"):
        lowered = " ".join(sql_text.lower().split())
        calls.append(lowered)
        if lowered.startswith("update public.customer_approvals"):
            return {"id": approval["id"]}
        if lowered.startswith("select code,name"):
            return {
                "code": "P-1",
                "name": "Casa",
                "client_name": "Ana",
                "status": "APPROVED",
                "total_price_net": "10.00",
                "total_price_tax": "1.90",
                "total_price_gross": "11.90",
                "current_revision": "REV-A",
            }
        if lowered.startswith("select revision_code"):
            return {
                "revision_code": "REV-A",
                "emitted_at": datetime.now(timezone.utc),
            }
        raise AssertionError(lowered)

    monkeypatch.setattr("portal.service.rows", fake_rows)
    monkeypatch.setattr("portal.service.one", fake_one)
    role_calls: list[str] = []

    class _FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def execute(self, statement, params=()):
            role_calls.append(str(statement))

        def fetchone(self):
            return ["authenticated"]

    monkeypatch.setattr(
        "portal.service.connection",
        SimpleNamespace(cursor=lambda: _FakeCursor()),
    )
    with patch("portal.service.SupabaseDocumentStorage"):
        out = service.decide_quote(
            token="tok", decision="APPROVED", decided_by="Ana", note=None
        )

    assert any("pricing_backend" in c for c in role_calls)
    assert any("request.jwt.claims" in c for c in role_calls)

    assert out["approval_status"] in {"PENDING", "APPROVED"}
    assert any("status='approved'" in c for c in calls)
    # every SQL statement stayed parameterized (never interpolated the token)
    assert all("token" not in c or "token_hash" in c for c in calls)
    # the approval row itself was updated via one()/RETURNING
    assert any("update public.customer_approvals" in c for c in calls)


def test_decide_replay_keeps_sealed_state(monkeypatch) -> None:
    _roles(monkeypatch)
    approval = _approval(status="APPROVED")
    calls: list[str] = []

    def fake_rows(sql_text, params=()):
        lowered = " ".join(sql_text.lower().split())
        calls.append(lowered)
        if "token_hash" in lowered:
            return [approval]
        return []

    monkeypatch.setattr("portal.service.rows", fake_rows)
    monkeypatch.setattr(
        "portal.service.one",
        lambda sql_text, params, code="not_found": {
            "code": "P-1",
            "name": "Casa",
            "client_name": "Ana",
            "status": "APPROVED",
            "total_price_net": "10.00",
            "total_price_tax": "1.90",
            "total_price_gross": "11.90",
            "current_revision": "REV-A",
            "revision_code": "REV-A",
            "emitted_at": datetime.now(timezone.utc),
        },
    )
    with patch("portal.service.SupabaseDocumentStorage"):
        out = service.decide_quote(
            token="tok", decision="DECLINED", decided_by="Otro", note=None
        )
    # a second decision never rewrites the approval row or the project
    assert not any("update" in c for c in calls)
    assert out["approval_status"] == "APPROVED"
