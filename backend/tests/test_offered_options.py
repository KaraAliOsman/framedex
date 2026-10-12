"""Request-local reuse preserves full hash, tenant and literal offer checks."""
import copy
import json
from uuid import uuid4

import pytest

from dekopen_engine.documentary_canonical import snapshot_sha256_v1
from documents import agreements, artifacts
from documents.repository import DocumentaryError


@pytest.fixture
def sealed(monkeypatch):
    org, project = uuid4(), uuid4()
    snapshots = {revision: {"revision": revision, "project": {"name": "DEMO"},
                            "positions": [], "pricing": {}} for revision in ["REV-A", "REV-B", "REV-C"]}
    snapshots["REV-B"]["alternatives"] = [copy.deepcopy(snapshots["REV-A"])]
    versions = {revision: {"id": uuid4(), "project_id": project, "org_id": org,
                           "revision_code": revision, "authority_version": "SHOT10_V1",
                           "snapshot_json": json.dumps(snapshot),
                           "snapshot_sha256": snapshot_sha256_v1(snapshot)}
                for revision, snapshot in snapshots.items()}
    calls = []

    def version_query(sql, params, *error):
        calls.append(params[0])
        assert params[1] == org
        return next(row.copy() for row in versions.values() if row["id"] == params[0])

    def selection_query(sql, params, *error):
        assert params[:2] == [org, project]
        return versions[params[2]].copy()

    monkeypatch.setattr(artifacts, "one", version_query)
    monkeypatch.setattr(agreements, "one", selection_query)
    return org, versions, calls


def test_one_request_verifies_each_complete_authority_once(sealed):
    org, versions, calls = sealed
    request = agreements.OfferedOptions(org, versions["REV-B"])
    assert request.resolve("REV-B")[0]["id"] == versions["REV-B"]["id"]
    assert request.resolve("REV-A")[0]["id"] == versions["REV-A"]["id"]
    assert request.resolve("REV-A")[0]["id"] == versions["REV-A"]["id"]
    assert calls == [versions["REV-B"]["id"], versions["REV-A"]["id"]]


def test_new_request_revalidates_hash_instead_of_reusing_old_authority(sealed):
    org, versions, calls = sealed
    agreements.OfferedOptions(org, versions["REV-B"]).resolve("REV-A")
    versions["REV-A"]["snapshot_json"] = json.dumps({"revision": "REV-A", "changed": True})
    with pytest.raises(DocumentaryError, match="frozen_revision_hash_mismatch"):
        agreements.OfferedOptions(org, versions["REV-B"]).resolve("REV-A")
    assert len(calls) == 4


def test_valid_but_unoffered_revision_still_fails_literal_inclusion(sealed):
    org, versions, _ = sealed
    with pytest.raises(DocumentaryError, match="quote_option_not_offered"):
        agreements.OfferedOptions(org, versions["REV-B"]).resolve("REV-C")


def test_offering_still_checks_project_binding(sealed):
    org, versions, _ = sealed
    with pytest.raises(DocumentaryError, match="quote_option_not_offered"):
        agreements.OfferedOptions(org, {**versions["REV-B"], "project_id": uuid4()})
