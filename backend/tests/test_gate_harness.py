"""Negative tests for the checker, not substitutes for real integration gates."""

from types import SimpleNamespace
from pathlib import Path

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
    assert "fixture-s3-secret" not in local_gates.redact("│ Secret Key │ fixture-s3-secret │")
    assert "fixture-s3-access" not in local_gates.redact("│ Access Key │ fixture-s3-access │")
    assert '"JWT_SECRET":"[redacted]"' in local_gates.redact('{"JWT_SECRET":"fixture-secret"}')
    assert "JWT_SECRET=[redacted]" in local_gates.redact("JWT_SECRET=fixture-secret")
    assert "fixture-password" not in local_gates.redact("postgresql://postgres:fixture-password@localhost/db")


def test_mailpit_health_failure_cannot_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(local_gates.httpx, "get", lambda *args, **kwargs: SimpleNamespace(status_code=503))
    with pytest.raises(RuntimeError, match="Mailpit /readyz failed"):
        local_gates.require_mailpit({"MAILPIT_URL": "http://127.0.0.1:54324"})


@pytest.mark.parametrize("existing", ("labelled-container", "volume", "legacy-container"))
def test_clean_gate_never_mutates_an_existing_stack(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, existing: str,
) -> None:
    (tmp_path / "supabase").mkdir()
    (tmp_path / "supabase/config.toml").write_text('project_id = "guard-fixture"\n', encoding="utf-8")
    monkeypatch.setattr(local_gates, "ROOT", tmp_path)
    monkeypatch.setattr(local_gates, "executable", lambda name: name)
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        if command == ["supabase", "--version"]:
            return local_gates.CLI_VERSION
        if command[:3] == ["docker", "ps", "-aq"]:
            if existing == "labelled-container" and command[-1].startswith("label="):
                return "existing-container\n"
            if existing == "legacy-container" and command[-1].startswith("name="):
                return "existing-unlabelled-container\n"
        if command[:3] == ["docker", "volume", "ls"] and existing == "volume":
            return "existing-data-volume\n"
        return ""

    monkeypatch.setattr(local_gates, "run", fake_run)
    with pytest.raises(RuntimeError, match="refuses existing Supabase"):
        local_gates.start_clean_stack()
    assert [command for command in commands if command[0] == "supabase"] == [["supabase", "--version"]]
    assert all("guard-fixture" in command[-1] for command in commands if "--filter" in command)


def test_clean_gate_preflight_accepts_only_absent_project_resources(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    (tmp_path / "supabase").mkdir()
    (tmp_path / "supabase/config.toml").write_text('project_id = "empty-fixture"\n', encoding="utf-8")
    monkeypatch.setattr(local_gates, "ROOT", tmp_path)
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        return ""

    monkeypatch.setattr(local_gates, "run", fake_run)
    local_gates.require_disposable_stack("docker")
    assert len(commands) == 3
    assert all(command[0] == "docker" and "empty-fixture" in command[-1] for command in commands)
