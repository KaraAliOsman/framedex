"""Customer approval links: token mint, public read, idempotent decide."""

import json
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


def _version(snapshot: dict | None = None, revision="REV-A"):
    return {
        "revision_code": revision,
        "emitted_at": datetime.now(timezone.utc),
        "snapshot_json": json.dumps(
            snapshot
            or {
                "project": {
                    "code": "P-1",
                    "name": "Casa",
                    "client_name": "Ana",
                    "total_price_net": "10.00",
                    "total_price_tax": "1.90",
                    "total_price_gross": "11.90",
                    "quotation_valid_until": "2999-01-01",
                }
            }
        ),
    }


def _live(status="QUOTED", revision="REV-A"):
    return {"status": status, "current_revision": revision}


def _install_fakes(monkeypatch, approval, version=None, live=None, calls=None):
    calls = calls if calls is not None else []

    def fake_rows(sql_text, params=()):
        lowered = " ".join(sql_text.lower().split())
        calls.append(lowered)
        if "token_hash" in lowered:
            return [approval]
        if lowered.startswith("update public.customer_approvals"):
            return [{"id": approval["id"]}]
        if lowered.startswith("update public.projects"):
            return [{"id": approval["project_id"]}]
        return []

    def fake_one(sql_text, params, code="not_found"):
        lowered = " ".join(sql_text.lower().split())
        calls.append(lowered)
        if "project_versions" in lowered:
            return version or _version()
        if "public.projects" in lowered:
            return live or _live()
        raise AssertionError(lowered)

    monkeypatch.setattr("portal.service.rows", fake_rows)
    monkeypatch.setattr("portal.service.one", fake_one)
    return calls


def test_portal_quote_unknown_and_expired_tokens(monkeypatch) -> None:
    _roles(monkeypatch)
    monkeypatch.setattr("portal.service.rows", lambda *a, **k: [])
    with pytest.raises(DocumentaryError, match="quote_not_found"):
        service.portal_quote("bogus")

    monkeypatch.setattr("portal.service.rows", lambda *a, **k: [_approval(expired=True)])
    with pytest.raises(DocumentaryError, match="quote_expired"):
        service.portal_quote("expired-token")


def test_portal_quote_reads_sealed_snapshot_not_live_totals(monkeypatch) -> None:
    """After a successor resets live totals, the link still shows REV-A's."""
    _roles(monkeypatch)
    approval = _approval()
    sealed = {
        "project": {
            "code": "P-1",
            "name": "Casa",
            "client_name": "Ana",
            "total_price_net": "1190000.00",
            "total_price_tax": "226100.00",
            "total_price_gross": "1416100.00",
            "quotation_valid_until": "2999-01-01",
        }
    }
    # the live project moved on to a draft REV-B with zeroed totals
    _install_fakes(
        monkeypatch,
        approval,
        version=_version(snapshot=sealed),
        live=_live(status="DRAFT", revision="REV-B"),
    )
    with patch("portal.service.SupabaseDocumentStorage"):
        out = service.portal_quote("tok")

    assert out["total_price_gross"] == "1416100.00"
    assert out["project_name"] == "Casa"
    assert out["revision_code"] == "REV-A"
    assert out["superseded"] is True
    assert out["valid_until"] == "2999-01-01"


def test_decide_approves_project_and_replays(monkeypatch) -> None:
    _roles(monkeypatch)
    approval = _approval()
    calls = _install_fakes(monkeypatch, approval)

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
    # the portal role bound itself to the approval's tenant first
    assert any("app.portal_org_id" in c for c in calls)
    assert out["approval_status"] in {"PENDING", "APPROVED"}
    assert any("status='approved'" in c for c in calls)
    # every SQL statement stayed parameterized (never interpolated the token)
    assert all("token" not in c or "token_hash" in c for c in calls)
    assert any("update public.customer_approvals" in c for c in calls)
    assert any("update public.projects" in c for c in calls)


def test_decide_rejects_stale_link(monkeypatch) -> None:
    """A successor draft resets the project — the old link cannot approve it."""
    _roles(monkeypatch)
    approval = _approval()
    calls = _install_fakes(
        monkeypatch, approval, live=_live(status="DRAFT", revision="REV-B")
    )
    with patch("portal.service.SupabaseDocumentStorage"):
        with pytest.raises(DocumentaryError, match="quote_link_stale"):
            service.decide_quote(
                token="tok", decision="APPROVED", decided_by="Ana", note=None
            )
    # nothing was written — no stale approval seal, no project transition
    assert not any(c.startswith("update") for c in calls)


def test_decide_confirm_on_already_approved_project(monkeypatch) -> None:
    """A second link on the same sealed revision still seals its approval."""
    _roles(monkeypatch)
    approval = _approval()
    calls = _install_fakes(monkeypatch, approval, live=_live(status="APPROVED"))
    with patch("portal.service.SupabaseDocumentStorage"):
        out = service.decide_quote(
            token="tok", decision="APPROVED", decided_by="Ana", note=None
        )
    # the approval seals, but the project is not transitioned again
    assert any("update public.customer_approvals" in c for c in calls)
    assert not any("update public.projects" in c for c in calls)
    assert out["approval_status"] in {"PENDING", "APPROVED"}


def test_decide_rejects_expired_quote_validity(monkeypatch) -> None:
    _roles(monkeypatch)
    approval = _approval()
    stale_validity = {
        "project": {"quotation_valid_until": "2000-01-01"}
    }
    calls = _install_fakes(
        monkeypatch, approval, version=_version(snapshot=stale_validity)
    )
    with patch("portal.service.SupabaseDocumentStorage"):
        with pytest.raises(DocumentaryError, match="quote_validity_expired"):
            service.decide_quote(
                token="tok", decision="APPROVED", decided_by="Ana", note=None
            )
    assert not any(c.startswith("update") for c in calls)


def test_decide_replay_keeps_sealed_state(monkeypatch) -> None:
    _roles(monkeypatch)
    approval = _approval(status="APPROVED")
    calls = _install_fakes(monkeypatch, approval, live=_live(status="APPROVED"))
    with patch("portal.service.SupabaseDocumentStorage"):
        out = service.decide_quote(
            token="tok", decision="DECLINED", decided_by="Otro", note=None
        )
    # a second decision never rewrites the approval row or the project
    assert not any(c.startswith("update") for c in calls)
    assert out["approval_status"] == "APPROVED"
