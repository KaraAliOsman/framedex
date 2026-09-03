from __future__ import annotations

from contextlib import nullcontext
import json

import pytest

import authentication.rls
from authentication.rls import authenticated_rls_context


class RecordingCursor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def __enter__(self) -> RecordingCursor:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, sql: str, params: object = None) -> None:
        self.calls.append((sql, params))


class RecordingConnection:
    def __init__(self, cursor: RecordingCursor) -> None:
        self.recording_cursor = cursor

    def cursor(self) -> RecordingCursor:
        return self.recording_cursor


def test_verified_claims_and_authenticated_role_are_transaction_local(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cursor = RecordingCursor()
    monkeypatch.setattr(authentication.rls, "connection", RecordingConnection(cursor))
    monkeypatch.setattr(authentication.rls.transaction, "atomic", nullcontext)
    claims = {"sub": "10000000-0000-0000-0000-000000000001", "role": "authenticated"}

    with authenticated_rls_context(claims):
        pass

    assert cursor.calls[0][0] == "SELECT set_config('request.jwt.claims', %s, true)"
    assert json.loads(cursor.calls[0][1][0]) == claims
    assert cursor.calls[1] == ("SET LOCAL ROLE authenticated", None)
