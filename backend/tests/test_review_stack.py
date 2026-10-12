"""Review startup never adopts foreign resources or writes dotenv values."""
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def review(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[2] / "scripts/review_stack.py"
    spec = importlib.util.spec_from_file_location("owned_review_stack", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "WORK", tmp_path / ".run/review")
    return module


def test_existing_data_without_owner_manifest_is_preserved(review, monkeypatch):
    calls = []
    monkeypatch.setattr(review, "resources", lambda: True)
    monkeypatch.setattr(review, "call", lambda *args, **kwargs: calls.append(args))
    with pytest.raises(RuntimeError, match="sin manifiesto"):
        review.require_owner()
    assert calls == [] and not review.WORK.exists()


def test_start_preserves_a_foreign_network_before_creating_containers(review, monkeypatch):
    calls = []
    monkeypatch.setattr(review.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(
        returncode=0, stdout=json.dumps([{"Labels": {review.LABEL: "foreign"}}])))
    monkeypatch.setattr(review, "call", lambda *args, **kwargs: calls.append(args))
    with pytest.raises(RuntimeError, match="red.*otro checkout"):
        review.container("framedex-review-api", "review-image", [], {})
    assert calls == []


def test_stop_checks_every_container_before_stopping_any(review, monkeypatch):
    review.WORK.mkdir(parents=True)
    (review.WORK / "owner.json").write_text(json.dumps({"owner": review.OWNER, "root": str(review.ROOT)}))
    calls = []
    monkeypatch.setattr(review, "inspect", lambda name: {"Config": {"Labels": {
        review.LABEL: "foreign" if name.endswith("api") else review.OWNER}}})
    monkeypatch.setattr(review, "call", lambda *args, **kwargs: calls.append(args))
    with pytest.raises(RuntimeError, match="no pertenece"):
        review.stop()
    assert calls == []


def test_dotenv_only_changes_the_returned_memory_environment(review, monkeypatch):
    monkeypatch.delenv("REVIEW_TEST_VALUE", raising=False)
    (review.ROOT / ".env").write_text('REVIEW_TEST_VALUE="local-fixture-value"\n# ignored\n')
    before = set(review.ROOT.rglob("*"))
    env = review.dotenv()
    assert env["REVIEW_TEST_VALUE"] == "local-fixture-value"
    assert "REVIEW_TEST_VALUE" not in os.environ
    assert set(review.ROOT.rglob("*")) == before
