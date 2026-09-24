"""Flow payment links: dispatch claims, verified settlement, recovery."""

from contextlib import contextmanager
from decimal import Decimal
from uuid import uuid4

import pytest
from rest_framework.exceptions import APIException

from billing.flow import FlowError
from projects import payment_links


@contextmanager
def _noop():
    yield


class _Client:
    def __init__(self, *, api_url="https://sandbox.flow.cl/api", behavior=None):
        self.api_url = api_url
        self.behavior = behavior or {}
        self.calls = []

    def create_payment(self, **kwargs):
        self.calls.append(("create", kwargs))
        if self.behavior.get("create_error"):
            raise FlowError("flow_unavailable", uncertain=True)
        return {"url": "https://sandbox.flow.cl/pay", "token": "tok-1", "flowOrder": 99}

    def redirect_url(self, response):
        return "https://sandbox.flow.cl/pay?token=tok-1"

    def payment_status(self, token):
        self.calls.append(("status", token))
        return self.behavior.get(
            "status",
            {"flowOrder": 99, "status": 2, "commerceOrder": "op-link-1",
             "amount": "250000", "currency": "CLP"},
        )

    def payment_by_order(self, order):
        self.calls.append(("by_order", order))
        return self.behavior.get(
            "by_order",
            {"flowOrder": 99, "status": 2, "commerceOrder": "op-link-1",
             "amount": "250000", "currency": "CLP"},
        )


def _integration(**over):
    return {
        "org_id": uuid4(),
        "provider": "FLOW",
        "api_url": "https://sandbox.flow.cl/api",
        "api_key": "AB12CD34EF56",
        "secret_key": "S3CR3T-KEY-0987",
        "payer_return_url": None,
        "enabled": True,
        "created_at": "2026-09-23T10:00:00+00:00",
        "updated_at": "2026-09-23T10:00:00+00:00",
        **over,
    }


def _link(**over):
    return {
        "id": uuid4(),
        "org_id": uuid4(),
        "project_id": uuid4(),
        "operation_key": "op-link-1",
        "kind": "ANTICIPO",
        "amount": Decimal("250000"),
        "payer_email": "cliente@correo.cl",
        "subject": "Ventanales — anticipo",
        "status": "PENDING",
        "environment": "sandbox",
        "flow_order": "99",
        "flow_token": "tok-1",
        "url": "https://sandbox.flow.cl/pay?token=tok-1",
        "project_payment_id": None,
        "flow_api_url": "https://sandbox.flow.cl/api",
        "flow_api_key": "AB12CD34EF56",
        "flow_secret_key": "S3CR3T-KEY-0987",
        "deal_total": Decimal("250000"),
        "deal_currency": "CLP",
        "created_by": uuid4(),
        "created_at": "2026-09-23T10:00:00+00:00",
        "updated_at": "2026-09-23T10:00:00+00:00",
        **over,
    }


def _payment_row(**over):
    return {
        "id": uuid4(),
        "kind": "ANTICIPO",
        "amount": Decimal("250000"),
        "method": "OTHER",
        "reference": "FLOW 99",
        "note": "Cobro en línea",
        "recorded_by": None,
        "recorded_at": "2026-09-23T10:00:00+00:00",
        "voided_at": None,
        "void_reason": None,
        "created_at": "2026-09-23T10:00:00+00:00",
        **over,
    }


def _patch_env(monkeypatch, rows_impl, client=None, deal=None):
    monkeypatch.setattr(payment_links, "documentary_backend", _noop)
    monkeypatch.setattr(payment_links.transaction, "atomic", _noop)
    monkeypatch.setattr(
        payment_links.wallet, "financial_transaction", lambda org: _noop()
    )
    monkeypatch.setattr(payment_links, "rows", rows_impl)
    monkeypatch.setattr(
        payment_links, "project_row", staticmethod(lambda *a, **k: {"name": "P-1"})
    )
    monkeypatch.setattr(
        payment_links,
        "_deal",
        staticmethod(
            lambda *a, **k: deal
            if deal is not None
            else {"total": Decimal("250000"), "currency": "CLP"}
        ),
    )
    receipts = []
    monkeypatch.setattr(
        payment_links,
        "issue_receipt",
        lambda **kwargs: receipts.append(kwargs) or {},
    )
    if client is not None:
        monkeypatch.setattr(payment_links, "_client", lambda integration: client)
        monkeypatch.setattr(payment_links, "_client_for_link", lambda link: client)
    return receipts


def test_create_link_requires_integration(monkeypatch):
    _patch_env(monkeypatch, lambda sql, params=None: [])
    with pytest.raises(APIException) as failure:
        payment_links.create_link(
            org_id=uuid4(),
            project_id=uuid4(),
            actor_id=uuid4(),
            data={
                "operation_key": "op-link-1",
                "kind": "ANTICIPO",
                "amount": Decimal("250000"),
                "payer_email": "a@b.cl",
            },
        )
    assert failure.value.contract_code == "flow_not_configured"


def test_create_link_requires_a_deal(monkeypatch):
    _patch_env(
        monkeypatch,
        lambda sql, params=None: [_integration()]
        if "FROM public.org_payment_integrations" in sql
        else [],
        deal=None,
    )
    monkeypatch.setattr(
        payment_links, "_deal", staticmethod(lambda *a, **k: None)
    )
    with pytest.raises(APIException) as failure:
        payment_links.create_link(
            org_id=uuid4(),
            project_id=uuid4(),
            actor_id=uuid4(),
            data={
                "operation_key": "op-link-1",
                "kind": "ANTICIPO",
                "amount": Decimal("250000"),
                "payer_email": "a@b.cl",
            },
        )
    assert failure.value.contract_code == "payment_requires_deal"


def test_create_link_rejects_non_clp_deal(monkeypatch):
    _patch_env(
        monkeypatch,
        lambda sql, params=None: [_integration()]
        if "FROM public.org_payment_integrations" in sql
        else [],
        deal={"total": Decimal("1000"), "currency": "USD"},
    )
    with pytest.raises(APIException) as failure:
        payment_links.create_link(
            org_id=uuid4(),
            project_id=uuid4(),
            actor_id=uuid4(),
            data={
                "operation_key": "op-link-1",
                "kind": "ANTICIPO",
                "amount": Decimal("250000"),
                "payer_email": "a@b.cl",
            },
        )
    assert failure.value.contract_code == "payment_link_currency_unsupported"


def test_create_link_replay_returns_existing(monkeypatch):
    link = _link()
    calls = []

    def fake_rows(sql, params=None):
        calls.append(sql)
        if "FROM public.org_payment_integrations" in sql:
            return [_integration()]
        if "INSERT INTO public.project_payment_links" in sql:
            return []  # conflict: another dispatch won the key first
        if "FROM public.project_payment_links" in sql:
            return [link]
        return []

    _patch_env(monkeypatch, fake_rows, client=_Client())
    out = payment_links.create_link(
        org_id=link["org_id"],
        project_id=link["project_id"],
        actor_id=uuid4(),
        data={
            "operation_key": "op-link-1",
            "kind": "ANTICIPO",
            "amount": Decimal("250000"),
            "payer_email": "a@b.cl",
        },
    )
    assert out["link"]["id"] == str(link["id"])
    assert any("ON CONFLICT" in sql for sql in calls)


def test_create_link_replay_rejects_cross_project(monkeypatch):
    link = _link()

    def fake_rows(sql, params=None):
        if "FROM public.org_payment_integrations" in sql:
            return [_integration()]
        if "INSERT INTO public.project_payment_links" in sql:
            return []
        if "FROM public.project_payment_links" in sql:
            return [link]
        return []

    _patch_env(monkeypatch, fake_rows, client=_Client())
    with pytest.raises(APIException) as failure:
        payment_links.create_link(
            org_id=link["org_id"],
            project_id=uuid4(),  # another project claims the key
            actor_id=uuid4(),
            data={
                "operation_key": "op-link-1",
                "kind": "ANTICIPO",
                "amount": Decimal("250000"),
                "payer_email": "a@b.cl",
            },
        )
    assert failure.value.contract_code == "payment_operation_conflict"


def test_create_link_dispatches_and_stores_redirect(monkeypatch):
    integration = _integration()
    client = _Client()
    inserts = []

    def fake_rows(sql, params=None):
        if "FROM public.org_payment_integrations" in sql:
            return [integration]
        if "INSERT INTO public.project_payment_links" in sql:
            return [_link(status="DISPATCHING")]
        if "INSERT INTO public.project_payment_link_credentials" in sql:
            inserts.append(params)
            return []
        if "UPDATE public.project_payment_links" in sql:
            return [_link()]
        return []

    _patch_env(monkeypatch, fake_rows, client=client)
    out = payment_links.create_link(
        org_id=integration["org_id"],
        project_id=uuid4(),
        actor_id=uuid4(),
        data={
            "operation_key": "op-link-1",
            "kind": "ANTICIPO",
            "amount": Decimal("250000"),
            "payer_email": "a@b.cl",
        },
    )
    assert client.calls[0][0] == "create"
    assert client.calls[0][1]["order"] == "op-link-1"
    assert client.calls[0][1]["amount"] == Decimal("250000")
    assert out["link"]["status"] == "PENDING"
    assert out["link"]["url"].startswith("https://sandbox.flow.cl")
    # The credential version that signed the dispatch lives on the
    # backend-only credentials row, keyed by the new link id.
    assert inserts[0][2:] == [
        integration["api_url"],
        integration["api_key"],
        integration["secret_key"],
    ]


def test_create_link_marks_uncertain_on_provider_failure(monkeypatch):
    integration = _integration()
    updates = []

    def fake_rows(sql, params=None):
        if "FROM public.org_payment_integrations" in sql:
            return [integration]
        if "INSERT INTO public.project_payment_links" in sql:
            return [_link(status="DISPATCHING")]
        if "UPDATE public.project_payment_links" in sql:
            updates.append(sql)
            return [_link(status="UNCERTAIN")]
        return []

    _patch_env(monkeypatch, fake_rows, client=_Client(behavior={"create_error": True}))
    with pytest.raises(APIException) as failure:
        payment_links.create_link(
            org_id=integration["org_id"],
            project_id=uuid4(),
            actor_id=uuid4(),
            data={
                "operation_key": "op-link-1",
                "kind": "ANTICIPO",
                "amount": Decimal("250000"),
                "payer_email": "a@b.cl",
            },
        )
    assert failure.value.contract_code == "payment_link_dispatch_failed"
    assert any("UNCERTAIN" in sql for sql in updates)


def test_confirm_settles_payment_into_ledger(monkeypatch):
    link = _link()
    inserts = []

    def fake_rows(sql, params=None):
        if "FROM public.project_payment_links" in sql and "id=%s" in sql:
            return [link]
        if "FOR UPDATE" in sql:
            return [link]
        if "INSERT INTO public.project_payments" in sql:
            inserts.append(sql)
            return [_payment_row()]
        if "UPDATE public.project_payment_links" in sql:
            return [_link(status="PAID", project_payment_id=uuid4())]
        return []

    client = _Client()
    receipts = _patch_env(monkeypatch, fake_rows, client=client)
    out = payment_links.confirm_link(link_id=link["id"], token="tok-1")
    assert out["link"]["status"] == "PAID"
    assert len(inserts) == 1
    assert "ON CONFLICT" in inserts[0]
    assert len(receipts) == 1
    assert receipts[0]["actor_id"] == link["created_by"]
    assert receipts[0]["deal"] == {"total": Decimal("250000"), "currency": "CLP"}


def test_confirm_seals_frozen_total_when_repriced(monkeypatch):
    """The comprobante reflects the total the link presented to the payer:
    repricing between mint and settle must not rewrite the frozen deal."""
    link = _link()
    integration = _integration(org_id=link["org_id"])

    def fake_rows(sql, params=None):
        if "FROM public.project_payment_links l" in sql:
            return [link]
        if "FROM public.org_payment_integrations" in sql:
            return [integration]
        if "FOR UPDATE" in sql:
            return [link]
        if "INSERT INTO public.project_payments" in sql:
            return [_payment_row()]
        if "UPDATE public.project_payment_links" in sql:
            return [_link(status="PAID", project_payment_id=uuid4())]
        return []

    client = _Client()
    receipts = _patch_env(monkeypatch, fake_rows, client=client)
    monkeypatch.setattr(
        payment_links,
        "_deal",
        lambda *a, **k: {"total": Decimal("400000"), "currency": "CLP"},
    )
    out = payment_links.confirm_link(link_id=link["id"], token="tok-1")
    assert out["link"]["status"] == "PAID"
    assert receipts[0]["deal"] == {"total": Decimal("250000"), "currency": "CLP"}


def test_confirm_settles_on_frozen_deal_when_pricing_reset(monkeypatch):
    """A verified payment must never strand: if the live deal is gone, the
    receipt falls back to the snapshot frozen on the link at creation."""
    link = _link()
    integration = _integration(org_id=link["org_id"])

    def fake_rows(sql, params=None):
        if "FROM public.project_payment_links l" in sql:
            return [link]
        if "FROM public.org_payment_integrations" in sql:
            return [integration]
        if "FOR UPDATE" in sql:
            return [link]
        if "INSERT INTO public.project_payments" in sql:
            return [_payment_row()]
        if "UPDATE public.project_payment_links" in sql:
            return [_link(status="PAID", project_payment_id=uuid4())]
        return []

    client = _Client()
    receipts = _patch_env(monkeypatch, fake_rows, client=client)
    monkeypatch.setattr(payment_links, "_deal", lambda *a, **k: None)
    out = payment_links.confirm_link(link_id=link["id"], token="tok-1")
    assert out["link"]["status"] == "PAID"
    assert len(receipts) == 1
    assert receipts[0]["deal"] == {"total": Decimal("250000"), "currency": "CLP"}


def test_confirm_settles_on_live_deal_for_legacy_link(monkeypatch):
    """Links minted before the freeze carry no snapshot: the sealed revision's
    deal is used — read inside the billing scope, not via documentary claims."""
    link = _link(deal_total=None, deal_currency=None)
    integration = _integration(org_id=link["org_id"])

    def fake_rows(sql, params=None):
        if "FROM public.project_payment_links l" in sql:
            return [link]
        if "FROM public.org_payment_integrations" in sql:
            return [integration]
        if "FROM public.project_versions" in sql:
            return [
                {
                    "revision_code": "REV-A",
                    "snapshot_json": '{"project":{"total_price_gross":"250000","currency":"CLP"}}',
                }
            ]
        if "FOR UPDATE" in sql:
            return [link]
        if "INSERT INTO public.project_payments" in sql:
            return [_payment_row()]
        if "UPDATE public.project_payment_links" in sql:
            return [_link(status="PAID", project_payment_id=uuid4())]
        return []

    client = _Client()
    receipts = _patch_env(monkeypatch, fake_rows, client=client)
    monkeypatch.setattr(payment_links, "_deal", lambda *a, **k: None)
    out = payment_links.confirm_link(link_id=link["id"], token="tok-1")
    assert out["link"]["status"] == "PAID"
    assert receipts[0]["deal"] == {"total": Decimal("250000"), "currency": "CLP"}


def test_confirm_settles_without_any_deal(monkeypatch):
    """Links minted before the deal freeze carry no snapshot — the charge
    still settles and the comprobante renders an empty balance."""
    link = _link(deal_total=None, deal_currency=None)
    integration = _integration(org_id=link["org_id"])

    def fake_rows(sql, params=None):
        if "FROM public.project_payment_links l" in sql:
            return [link]
        if "FROM public.org_payment_integrations" in sql:
            return [integration]
        if "FOR UPDATE" in sql:
            return [link]
        if "INSERT INTO public.project_payments" in sql:
            return [_payment_row()]
        if "UPDATE public.project_payment_links" in sql:
            return [_link(status="PAID", project_payment_id=uuid4())]
        return []

    client = _Client()
    receipts = _patch_env(monkeypatch, fake_rows, client=client)
    monkeypatch.setattr(payment_links, "_deal", lambda *a, **k: None)
    out = payment_links.confirm_link(link_id=link["id"], token="tok-1")
    assert out["link"]["status"] == "PAID"
    assert receipts[0]["deal"] == {"total": None, "currency": "CLP"}


def test_confirm_uses_link_credentials_not_current_integration(monkeypatch):
    link = _link(flow_api_key="OLD-KEY-ROTATED")
    client = _Client()
    built = []

    def factory(**kwargs):
        built.append(kwargs)
        return client

    monkeypatch.setattr(payment_links, "FlowClient", factory)

    def fake_rows(sql, params=None):
        # org_payment_integrations is deliberately empty — rotation/disabling
        # must not strand an outstanding charge.
        if "FROM public.project_payment_links" in sql:
            return [link]
        if "FOR UPDATE" in sql:
            return [link]
        if "INSERT INTO public.project_payments" in sql:
            return [_payment_row()]
        if "UPDATE public.project_payment_links" in sql:
            return [_link(status="PAID", project_payment_id=uuid4())]
        return []

    _patch_env(monkeypatch, fake_rows)
    out = payment_links.confirm_link(link_id=link["id"], token="tok-1")
    assert out["link"]["status"] == "PAID"
    assert built[0]["api_key"] == "OLD-KEY-ROTATED"


def test_confirm_rejects_binding_mismatch(monkeypatch):
    link = _link()

    def fake_rows(sql, params=None):
        if "FROM public.project_payment_links" in sql:
            return [link]
        return []

    client = _Client(
        behavior={
            "status": {"flowOrder": 99, "status": 2, "commerceOrder": "OTHER-ORDER",
                       "amount": "250000", "currency": "CLP"}
        }
    )
    _patch_env(monkeypatch, fake_rows, client=client)
    with pytest.raises(FlowError, match="flow_payment_binding_mismatch"):
        payment_links.confirm_link(link_id=link["id"], token="tok-1")


def test_confirm_paid_link_is_idempotent(monkeypatch):
    link = _link(status="PAID", project_payment_id=uuid4())

    def fake_rows(sql, params=None):
        if "FROM public.project_payment_links" in sql:
            return [link]
        return []

    _patch_env(monkeypatch, fake_rows, client=_Client())
    out = payment_links.confirm_link(link_id=link["id"], token="tok-1")
    assert out["link"]["status"] == "PAID"


def test_confirm_failed_observation_marks_link_failed(monkeypatch):
    link = _link()

    def fake_rows(sql, params=None):
        if "FROM public.project_payment_links" in sql:
            return [link]
        if "UPDATE public.project_payment_links" in sql:
            return [_link(status="FAILED")]
        return []

    client = _Client(
        behavior={
            "status": {"flowOrder": 99, "status": 3, "commerceOrder": "op-link-1",
                       "amount": "250000", "currency": "CLP"}
        }
    )
    _patch_env(monkeypatch, fake_rows, client=client)
    out = payment_links.confirm_link(link_id=link["id"], token="tok-1")
    assert out["link"]["status"] == "FAILED"


def test_settle_rejects_hijacking_payment(monkeypatch):
    """A manual row holding the same key but different claim must not settle."""
    link = _link()
    hijacker = _payment_row(project_id=uuid4(), amount=Decimal("10000"))

    def fake_rows(sql, params=None):
        if "FROM public.project_payment_links" in sql:
            return [link]
        if "INSERT INTO public.project_payments" in sql:
            return []  # conflict — key already claimed
        if "FOR UPDATE" in sql and "project_payments" in sql:
            return [hijacker]
        if "FOR UPDATE" in sql:
            return [link]
        return []

    _patch_env(monkeypatch, fake_rows, client=_Client())
    with pytest.raises(APIException) as failure:
        payment_links.confirm_link(link_id=link["id"], token="tok-1")
    assert failure.value.contract_code == "payment_operation_conflict"


def test_settle_accepts_matching_manual_payment(monkeypatch):
    link = _link()
    manual = _payment_row(project_id=link["project_id"])

    def fake_rows(sql, params=None):
        if "FROM public.project_payment_links" in sql:
            return [link]
        if "INSERT INTO public.project_payments" in sql:
            return []
        if "FOR UPDATE" in sql and "project_payments" in sql:
            return [manual]
        if "FOR UPDATE" in sql:
            return [link]
        if "UPDATE public.project_payment_links" in sql:
            return [_link(status="PAID", project_payment_id=manual["id"])]
        return []

    _patch_env(monkeypatch, fake_rows, client=_Client())
    out = payment_links.confirm_link(link_id=link["id"], token="tok-1")
    assert out["link"]["status"] == "PAID"
    assert out["link"]["project_payment_id"] == str(manual["id"])


def test_recover_promotes_uncertain_to_pending(monkeypatch):
    link = _link(status="UNCERTAIN", flow_order=None)
    updates = []

    def fake_rows(sql, params=None):
        if "FROM public.project_payment_links" in sql:
            return [link]
        if "UPDATE public.project_payment_links" in sql:
            updates.append((sql, params))
            return [_link(status="PENDING", flow_order="99")]
        return []

    client = _Client(
        behavior={
            "by_order": {"flowOrder": 99, "status": 1, "commerceOrder": "op-link-1",
                         "amount": "250000", "currency": "CLP"}
        }
    )
    _patch_env(monkeypatch, fake_rows, client=client)
    out = payment_links.recover_link(
        org_id=link["org_id"], project_id=link["project_id"], link_id=link["id"]
    )
    assert out["link"]["status"] == "PENDING"
    assert updates and "UNCERTAIN" in updates[0][0]


def test_recover_scopes_to_project(monkeypatch):
    seen = []

    def fake_rows(sql, params=None):
        seen.append((sql, params))
        if "FROM public.project_payment_links" in sql:
            return []
        return []

    _patch_env(monkeypatch, fake_rows, client=_Client())
    link = _link()
    with pytest.raises(APIException):
        payment_links.recover_link(
            org_id=link["org_id"], project_id=link["project_id"], link_id=link["id"]
        )
    lookup = [p for s, p in seen if "FROM public.project_payment_links" in s][0]
    assert str(link["project_id"]) in lookup


def test_recover_link_uses_order_lookup(monkeypatch):
    link = _link(status="UNCERTAIN", flow_order=None)

    def fake_rows(sql, params=None):
        if "FROM public.project_payment_links" in sql:
            return [link]
        if "FOR UPDATE" in sql:
            return [link]
        if "INSERT INTO public.project_payments" in sql:
            return [_payment_row()]
        if "UPDATE public.project_payment_links" in sql:
            return [_link(status="PAID")]
        return []

    client = _Client()
    _patch_env(monkeypatch, fake_rows, client=client)
    out = payment_links.recover_link(
        org_id=link["org_id"], project_id=link["project_id"], link_id=link["id"]
    )
    assert client.calls[0] == ("by_order", "op-link-1")
    assert out["link"]["status"] == "PAID"


def test_integration_status_never_leaks_secret(monkeypatch):
    def fake_rows(sql, params=None):
        if "FROM public.org_payment_integrations" in sql:
            return [_integration()]
        return []

    _patch_env(monkeypatch, fake_rows)
    status = payment_links.get_integration(org_id=uuid4())
    assert status["configured"] is True
    assert status["api_key_preview"] == "AB12…56"
    assert "secret" not in repr(status)


def test_save_integration_keeps_stored_secret_on_update(monkeypatch):
    captured = []

    def fake_rows(sql, params=None):
        captured.append((sql, params))
        if "SELECT api_key, secret_key FROM public.org_payment_integrations" in sql:
            return [{"api_key": "AB12CD34EF56", "secret_key": "S3CR3T-KEY-0987"}]
        if "INSERT INTO public.org_payment_integrations" in sql:
            return [{"org_id": params[0]}]
        if "FROM public.org_payment_integrations" in sql:
            return [_integration()]
        return []

    monkeypatch.setattr(payment_links, "documentary_backend", _noop)
    monkeypatch.setattr(payment_links.transaction, "atomic", _noop)
    monkeypatch.setattr(payment_links, "rows", fake_rows)
    payment_links.save_integration(
        org_id=uuid4(),
        data={
            "api_url": "https://www.flow.cl/api",
            "api_key": "NEWKEY123456",
            "payer_return_url": "",
            "enabled": True,
        },
    )
    insert = [p for s, p in captured if "INSERT INTO public.org_payment_integrations" in s]
    assert insert[0][3] == "S3CR3T-KEY-0987"  # stored secret survives the update


def test_save_integration_keeps_stored_api_key_on_update(monkeypatch):
    captured = []

    def fake_rows(sql, params=None):
        captured.append((sql, params))
        if "SELECT api_key, secret_key FROM public.org_payment_integrations" in sql:
            return [{"api_key": "AB12CD34EF56", "secret_key": "S3CR3T-KEY-0987"}]
        if "INSERT INTO public.org_payment_integrations" in sql:
            return [{"org_id": params[0]}]
        if "FROM public.org_payment_integrations" in sql:
            return [_integration()]
        return []

    monkeypatch.setattr(payment_links, "documentary_backend", _noop)
    monkeypatch.setattr(payment_links.transaction, "atomic", _noop)
    monkeypatch.setattr(payment_links, "rows", fake_rows)
    payment_links.save_integration(
        org_id=uuid4(),
        data={
            "api_url": "https://www.flow.cl/api",
            "enabled": False,  # toggling without re-typing the key
        },
    )
    insert = [p for s, p in captured if "INSERT INTO public.org_payment_integrations" in s]
    assert insert[0][2] == "AB12CD34EF56"


def test_save_integration_requires_secret_for_new_org(monkeypatch):
    monkeypatch.setattr(payment_links, "documentary_backend", _noop)
    monkeypatch.setattr(payment_links.transaction, "atomic", _noop)
    monkeypatch.setattr(payment_links, "rows", lambda *_a, **_k: [])
    with pytest.raises(APIException) as failure:
        payment_links.save_integration(
            org_id=uuid4(),
            data={
                "api_url": "https://sandbox.flow.cl/api",
                "api_key": "NEWKEY123456",
            },
        )
    assert failure.value.contract_code == "flow_secret_required"


def test_save_integration_requires_api_key_for_new_org(monkeypatch):
    monkeypatch.setattr(payment_links, "documentary_backend", _noop)
    monkeypatch.setattr(payment_links.transaction, "atomic", _noop)
    monkeypatch.setattr(payment_links, "rows", lambda *_a, **_k: [])
    with pytest.raises(APIException) as failure:
        payment_links.save_integration(
            org_id=uuid4(),
            data={
                "api_url": "https://sandbox.flow.cl/api",
                "secret_key": "S3CR3T-KEY-0987",
            },
        )
    assert failure.value.contract_code == "flow_api_key_required"


def test_settle_drops_credentials_once_paid(monkeypatch):
    """A settled link must not keep the dispatch credential snapshot around."""
    link = _link()
    deletes = []

    def fake_rows(sql, params=None):
        if "FROM public.project_payment_links" in sql:
            return [link]
        if "FOR UPDATE" in sql:
            return [link]
        if "INSERT INTO public.project_payments" in sql:
            return [_payment_row()]
        if "UPDATE public.project_payment_links" in sql:
            return [_link(status="PAID", project_payment_id=uuid4())]
        if "DELETE FROM public.project_payment_link_credentials" in sql:
            deletes.append(params)
            return []
        return []

    _patch_env(monkeypatch, fake_rows, client=_Client())
    out = payment_links.confirm_link(link_id=link["id"], token="tok-1")
    assert out["link"]["status"] == "PAID"
    assert deletes == [[str(link["id"])]]


def test_terminal_link_falls_back_to_current_integration(monkeypatch):
    """Once the snapshot is gone, recovery uses the org's live integration."""
    link = _link(
        status="FAILED",
        flow_api_url=None,
        flow_api_key=None,
        flow_secret_key=None,
    )
    client = _Client()
    built = []
    monkeypatch.setattr(
        payment_links, "FlowClient", lambda **kw: built.append(kw) or client
    )
    integration = _integration(api_key="CURRENT-KEY")

    def fake_rows(sql, params=None):
        if "FROM public.project_payment_links" in sql:
            return [link]
        if "FROM public.org_payment_integrations" in sql:
            return [integration]
        if "INSERT INTO public.project_payments" in sql:
            return [_payment_row()]
        if "UPDATE public.project_payment_links" in sql:
            return [_link(status="PAID", project_payment_id=uuid4())]
        if "DELETE FROM public.project_payment_link_credentials" in sql:
            return []
        return []

    _patch_env(monkeypatch, fake_rows)
    out = payment_links.recover_link(
        org_id=link["org_id"], project_id=link["project_id"], link_id=link["id"]
    )
    assert out["link"]["status"] == "PAID"
    assert built[0]["api_key"] == "CURRENT-KEY"


def test_reset_pricing_blocked_by_outstanding_link(monkeypatch):
    """reset_draft_pricing refuses while a collectible link exists."""
    from projects import service as projects_service

    project = {
        "id": uuid4(),
        "org_id": uuid4(),
        "name": "P-1",
        "status": "DRAFT",
        "current_revision": "REV-A",
    }
    op_id = uuid4()
    monkeypatch.setattr(projects_service, "project_row", lambda *a, **k: project)
    monkeypatch.setattr(
        projects_service, "_pricing_authority", lambda *a, **k: {"id": op_id}
    )
    monkeypatch.setattr(projects_service, "audit_reason", lambda reason: None)
    monkeypatch.setattr(projects_service, "commercial_backend", _noop)
    monkeypatch.setattr(
        projects_service, "project_public", lambda *a, **k: {"id": project["id"]}
    )

    def fake_rows(sql, params=None):
        if "FROM public.project_versions" in sql:
            return []  # revision not yet emitted
        if "FROM public.project_payment_links" in sql:
            return [{"id": uuid4()}]  # an outstanding collectible link
        return []

    monkeypatch.setattr(projects_service, "rows", fake_rows)
    with pytest.raises(APIException) as failure:
        projects_service.reset_draft_pricing(
            project["org_id"], project["id"], op_id, "reprice"
        )
    assert failure.value.contract_code == "payment_links_outstanding"


def test_confirm_paid_link_requires_own_token(monkeypatch):
    """A retried callback acknowledges only when it carries the link's own
    opaque Flow token — a bare link id must not forge settlement evidence."""
    link = _link(status="PAID", project_payment_id=uuid4())

    def fake_rows(sql, params=None):
        if "FROM public.project_payment_links" in sql:
            return [link]
        return []

    _patch_env(monkeypatch, fake_rows, client=_Client())
    with pytest.raises(FlowError, match="flow_payment_binding_mismatch"):
        payment_links.confirm_link(link_id=link["id"], token="tok-other")


def test_cancel_link_tombstones_open_claim(monkeypatch):
    link = _link()
    writes = []

    def fake_rows(sql, params=None):
        if "SET status='CANCELLED'" in sql:
            writes.append(sql)
            return [_link(status="CANCELLED")]
        if "DELETE FROM public.project_payment_link_credentials" in sql:
            writes.append(sql)
            return []
        return []

    _patch_env(monkeypatch, fake_rows)
    out = payment_links.cancel_link(
        org_id=link["org_id"], project_id=link["project_id"], link_id=link["id"]
    )
    assert out["link"]["status"] == "CANCELLED"
    assert len(writes) == 2


def test_cancel_link_rejects_terminal_status(monkeypatch):
    link = _link(status="PAID")

    def fake_rows(sql, params=None):
        return []  # the status guard filters terminal rows out

    _patch_env(monkeypatch, fake_rows)
    with pytest.raises(APIException) as failure:
        payment_links.cancel_link(
            org_id=link["org_id"], project_id=link["project_id"], link_id=link["id"]
        )
    assert failure.value.contract_code == "payment_link_not_cancellable"


def test_create_link_rechecks_currency_under_lock(monkeypatch):
    """A pricing reset landing between the pre-check and the project lock can
    swap the deal's currency — the locked re-check must still refuse the
    charge."""
    calls = {"n": 0}

    def flip_deal(*args, **kwargs):
        calls["n"] += 1
        currency = "CLP" if calls["n"] == 1 else "USD"
        return {"total": Decimal("250000"), "currency": currency}

    _patch_env(
        monkeypatch,
        lambda sql, params=None: [_integration()]
        if "FROM public.org_payment_integrations" in sql
        else [],
        deal={"total": Decimal("250000"), "currency": "CLP"},
    )
    monkeypatch.setattr(payment_links, "_deal", staticmethod(flip_deal))
    with pytest.raises(APIException) as failure:
        payment_links.create_link(
            org_id=uuid4(),
            project_id=uuid4(),
            actor_id=uuid4(),
            data={
                "operation_key": "op-link-1",
                "kind": "ANTICIPO",
                "amount": Decimal("250000"),
                "payer_email": "a@b.cl",
            },
        )
    assert failure.value.contract_code == "payment_link_currency_unsupported"
    assert calls["n"] == 2  # pre-check passed; locked re-check caught the swap
