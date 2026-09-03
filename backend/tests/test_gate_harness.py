"""Negative tests for the checker, not substitutes for real integration gates."""

from types import SimpleNamespace

import pytest

from scripts import check_generated_api, local_gates


def test_generated_api_drift_rejects_an_altered_artifact(monkeypatch: pytest.MonkeyPatch) -> None:
    versions = iter(({"client.ts": b"old"}, {"client.ts": b"changed"}))
    monkeypatch.setattr(check_generated_api, "snapshot", lambda: next(versions))
    monkeypatch.setattr(check_generated_api, "run", lambda *args: None)
    monkeypatch.setattr(check_generated_api.shutil, "which", lambda name: name)
    with pytest.raises(SystemExit, match="Generated API drift detected: client.ts"):
        check_generated_api.main()


def test_missing_tool_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(local_gates.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="Required executable is missing"):
        local_gates.executable("supabase")


def test_failed_command_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        local_gates.subprocess, "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout="real failure", stderr=""),
    )
    with pytest.raises(RuntimeError, match="exited with code 1"):
        local_gates.run(["a-gate"])


def test_gate_logs_redact_secret_values_in_json_and_text() -> None:
    assert '"JWT_SECRET":"[redacted]"' in local_gates.redact('{"JWT_SECRET":"fixture-secret"}')
    assert "JWT_SECRET=[redacted]" in local_gates.redact("JWT_SECRET=fixture-secret")
    assert "fixture-password" not in local_gates.redact("postgresql://postgres:fixture-password@localhost/db")


def test_mailpit_health_failure_cannot_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(local_gates.httpx, "get", lambda *args, **kwargs: SimpleNamespace(status_code=503))
    with pytest.raises(RuntimeError, match="Mailpit /readyz failed"):
        local_gates.require_mailpit({"MAILPIT_URL": "http://127.0.0.1:54324"})
