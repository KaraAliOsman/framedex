"""Capabilities must recheck live revocation, including a previously cached 410."""

import pytest
from rest_framework.test import APIRequestFactory

from documents.repository import DocumentaryError
from portal.views import PortalQuoteDecisionView, PortalQuoteView


@pytest.mark.parametrize("code", [None, "quote_expired", "quote_revoked", "quote_not_found"])
@pytest.mark.parametrize("decision", [False, True])
def test_public_portal_never_caches_success_or_error(monkeypatch, code, decision):
    view = PortalQuoteDecisionView if decision else PortalQuoteView
    monkeypatch.setattr(view, "throttle_classes", [])

    def retrieve(*args, **kwargs):
        if code:
            raise DocumentaryError(code)
        return {"approval_status": "APPROVED"}

    monkeypatch.setattr("portal.service.portal_quote", retrieve)
    monkeypatch.setattr("portal.service.decide_quote", retrieve)
    factory = APIRequestFactory()
    request = (
        factory.post("/", {"decision": "APPROVED", "decided_by": "Cliente"}, format="json")
        if decision else factory.get("/")
    )
    response = view.as_view()(request, token="fixture-capability")
    assert response.status_code == (404 if code == "quote_not_found" else 410 if code else 200)
    assert "no-store" in response["Cache-Control"]
    assert "no-cache" in response["Cache-Control"]
    assert "private" in response["Cache-Control"]
    assert "Expires" in response
