"""P22: actual tenant authority, preserved dossiers and verified invitations."""

from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal as D
from uuid import uuid4
from threading import Barrier

from io import BytesIO
from pypdf import PdfReader
import pytest
from django.db import DatabaseError, transaction, close_old_connections
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from authentication.rls import authenticated_rls_context
from authentication.tenancy import MembershipRepository
from authentication.types import VerifiedSupabaseToken, SupabaseUser
from backend.tests.integration.test_shot09_documentary import (
    documentary_tenant as documentary_tenant,
    as_user,
    _seed_project,
    _freeze,
    _tenant,
    documentary_committed_tenant as documentary_committed_tenant,
)
from documents.repository import documentary_backend, decoded
from pricing.repository import admin_write, commercial_backend, one, rows, write
from projects import clients, client_history, company, org_branding, service

pytestmark = pytest.mark.rls_integration
_live_branding_for_snapshot = org_branding.branding_for_snapshot


@pytest.fixture
def people(documentary_tenant, monkeypatch):
    # Unit emissions use a shared double; this integration consumes real settings.
    monkeypatch.setattr(org_branding, "branding_for_snapshot", _live_branding_for_snapshot)
    org, other, users, outsider = documentary_tenant
    users["OPERATOR"] = uuid4()
    write(
        "INSERT INTO public.tenancy_memberships(org_id,user_id,role) VALUES(%s,%s,'OPERATOR')",
        [org, users["OPERATOR"]],
    )
    for identity in [*users.values(), outsider]:
        write(
            "INSERT INTO auth.users(id,email,email_confirmed_at) VALUES(%s,%s,now())",
            [identity, f"p22-{identity}@example.test"],
        )
    return org, other, users, outsider


def customer(org, actor, **extra):
    with as_user(actor):
        return clients.create_client(
            org,
            actor,
            {
                "name": "Constructora Los Maitenes",
                "party_kind": "COMPANY",
                "contacts": [
                    {
                        "name": "Ana",
                        "contact_role": "Administración",
                        "email": "ana@example.test",
                        "is_primary": True,
                    },
                    {"name": "Pedro", "contact_role": "Obra", "phone": "+56912345678"},
                ],
                "addresses": [
                    {"label": "Norte", "address": "Av. Norte 220", "comuna": "Providencia"},
                    {"label": "Sur", "address": "Camino Sur 1550", "comuna": "Puente Alto"},
                ],
                **extra,
            },
        )


def test_rut_is_validated_and_canonical_duplicates_are_tenant_scoped(people):
    org, other, users, outsider = people
    record = customer(org, users["OWNER"], rut="76.543.210-3")
    with pytest.raises(Exception, match="RUT"), transaction.atomic():
        customer(org, users["OWNER"], rut="76.543.210-1")
    with pytest.raises(Exception, match="Ya existe"), transaction.atomic():
        customer(org, users["OWNER"], rut="76543210-3")
    with pytest.raises(DatabaseError), transaction.atomic(), as_user(users["OWNER"]):
        write(
            "INSERT INTO public.clients(org_id,name,rut,created_by) VALUES(%s,'Bypass','76.543.210-1',%s)",
            [org, users["OWNER"]],
        )
    second = customer(other, outsider, rut="76543210-3")
    assert record["id"] != second["id"]
    with as_user(outsider):
        assert not rows("SELECT id FROM public.client_addresses WHERE org_id=%s", [org])
        assert client_history.directory(other, {"q": "76.543.210-3"}, commercial=True)["total"] == 1


@pytest.mark.parametrize("mode", ["api_sparse", "api_same_selection", "direct_sql"])
def test_explicit_work_address_edit_detaches_selection_and_survives_reload(people, mode):
    org, _, users, _ = people
    client = customer(org, users["OWNER"])
    with as_user(users["OWNER"]):
        project = service.create_project(org, users["OWNER"], {
            "name": "Acceso posterior", "client_id": client["id"],
            "client_name": client["name"], "client_address_id": client["addresses"][1]["id"],
        })
        assert project["delivery_address"] == "Camino Sur 1550, Puente Alto"
        address = "Camino Sur 1550, acceso posterior, Puente Alto"
        if mode == "direct_sql":
            write("UPDATE public.projects SET delivery_address=%s WHERE org_id=%s AND id=%s",
                  [address, org, project["id"]])
        else:
            data = {"expected_updated_at": service.project_row(org, project["id"])["updated_at"], "delivery_address": address}
            if mode == "api_same_selection":
                data["client_address_id"] = project["client_address_id"]
            service.update_project(org, project["id"], data)
        saved = service.project_row(org, project["id"])
        assert saved["delivery_address"] == address
        assert saved["client_address_id"] is None
        # Selecting another master address deliberately replaces the override.
        selected = service.update_project(org, project["id"], {
            "expected_updated_at": saved["updated_at"],
            "client_address_id": client["addresses"][0]["id"],
        })
        assert selected["delivery_address"] == "Av. Norte 220, Providencia"


def test_directory_paginates_thousand_matches_with_bounded_queries(people):
    org, _, users, _ = people
    with as_user(users["OWNER"]):
        write("INSERT INTO public.clients(org_id,created_by,name) "
              "SELECT %s,%s,'Escala '||lpad(n::text,4,'0') FROM generate_series(1,1000) n",
              [org, users["OWNER"]])
        with CaptureQueriesContext(connection) as captured:
            page = client_history.directory(org, {"q": "Escala", "limit": 50}, commercial=True)
        assert page["total"] == 1000 and page["next_offset"] == 50
        assert len(page["items"]) == 50 and page["items"][0]["name"] == "Escala 0001"
        assert not any(item["has_active_projects"] for item in page["items"])
        assert len(captured) <= 20, f"Directory made {len(captured)} queries for one page"
        last = client_history.directory(org, {"q": "Escala", "limit": 50, "offset": 990}, commercial=True)
        assert len(last["items"]) == 10 and last["next_offset"] is None
        empty = client_history.directory(org, {"q": "Escala", "offset": 1001}, commercial=True)
        assert empty["total"] == 1000 and not empty["items"]
        with CaptureQueriesContext(connection) as captured:
            balance = client_history.directory(org, {"q": "Escala", "with_balance": True}, commercial=True)
        assert balance["total"] == 0 and not balance["items"]
        assert len(captured) <= 35


def test_station_upsert_edits_same_identity_and_preserves_row_count(people):
    from production.service import create_work_center, list_work_centers

    org, _, users, _ = people
    with as_user(users["OWNER"]):
        original, created = create_work_center(org_id=org, code="CUT-01", name="Corte",
                                               kind="CUT", display_order=1)
        assert created
        updated, created = create_work_center(org_id=org, code="CUT-01", name="Corte norte",
                                              kind="CUT", display_order=4)
        assert not created and updated["id"] == original["id"]
        assert updated["name"] == "Corte norte" and updated["display_order"] == 4
        assert len(list_work_centers(org_id=org)["centers"]) == 1


def test_merge_preserves_snapshots_children_notes_and_unknown_money(people):
    org, _, users, _ = people
    source = customer(org, users["OWNER"], rut="76.543.210-3")
    target = customer(org, users["OWNER"], name="Maitenes consolidado", contacts=[], addresses=[])
    project, _, operation = _seed_project(org, users["OWNER"])
    address = source["addresses"][1]
    # Metadata changes precede the applied price; explicitly reprice it.
    with as_user(users["OWNER"]):
        from projects.service import reset_draft_pricing

        reset_draft_pricing(org, project, operation, "Elegir dirección de la obra")
        write(
            "UPDATE public.projects SET client_id=%s,client_address_id=%s WHERE id=%s AND org_id=%s",
            [source["id"], address["id"], project, org],
        )
    from pricing.service import preview, apply_operation
    from backend.tests.integration.test_shot09_documentary import _tenant
    from pricing.repository import commercial_backend

    with as_user(users["OWNER"]), commercial_backend():
        result = preview(
            org,
            _tenant(org, "OWNER"),
            {
                "project_id": project,
                "currency": "CLP",
                "pricing_mode": "COST_PLUS_MARGIN",
                "effective_date": timezone.localdate(),
                "context_code": "DEFAULT",
                "discount_pct": D("0"),
                "target_margin": D("0.35"),
                "segment": "RETAIL",
                "reason": "P22 dirección declarada",
                "_actor_id": users["OWNER"],
                "confirmed": False,
            },
        )
        apply_operation(org, users["OWNER"], "OWNER", result["id"], "P22 revisión", False)
    version = _freeze(org, users["OWNER"], project, result["id"])
    sealed = one(
        "SELECT snapshot_json,snapshot_sha256 FROM public.project_versions WHERE id=%s",
        [version["id"]],
    )
    assert (
        decoded(sealed["snapshot_json"])["project"]["delivery_address"]
        == "Camino Sur 1550, Puente Alto"
    )
    with as_user(users["ESTIMATOR"]):
        note = clients.add_note(
            org,
            source["id"],
            users["ESTIMATOR"],
            {"operation_key": uuid4(), "body": "Coordinar descarga en obra Sur"},
        )
        unknown = one(
            "INSERT INTO public.projects(org_id,code,name,client_name,client_id,created_by) VALUES(%s,%s,'Sin precio','Maitenes',%s,%s) RETURNING id",
            [org, f"P-{uuid4().hex[:8]}", source["id"], users["ESTIMATOR"]],
        )
        source = clients.client_public(org, source["id"])
        target = clients.client_public(org, target["id"])
        previewed = clients.merge_preview(org, source["id"], target["id"])
        assert not previewed["blockers"] and len(previewed["added_addresses"]) == 2
        merged = clients.merge_client(
            org,
            source["id"],
            {
                "target_id": target["id"],
                "expected_source_updated_at": source["updated_at"],
                "expected_target_updated_at": target["updated_at"],
                "reason": "Misma empresa, ficha sin RUT duplicada",
                "confirmed": True,
            },
        )
        dossier = client_history.dossier(org, merged["id"])
        assert {str(p["id"]) for p in dossier["projects"]} == {str(project), str(unknown["id"])}
        assert dossier["unknown_projects"] == 1 and len(dossier["balances"]) == 1
        assert str(dossier["notes"][0]["id"]) == str(note["id"])
        assert len(merged["addresses"]) == 2 and all(a["origin_id"] for a in merged["addresses"])
        assert merged["rut"] == source["rut"]
        directory = client_history.directory(org, {"q": "Maitenes", "with_active_projects": True,
                                                   "with_balance": True}, commercial=True)
        assert directory["total"] == 1 and directory["items"][0]["id"] == target["id"]
        assert directory["items"][0]["has_active_projects"]
        assert str(unknown["id"]) in {str(p["id"]) for p in dossier["projects"]}
    assert sealed == one(
        "SELECT snapshot_json,snapshot_sha256 FROM public.project_versions WHERE id=%s",
        [version["id"]],
    )
    assert (
        str(one("SELECT client_id FROM public.projects WHERE id=%s", [project])["client_id"])
        == source["id"]
    )
    with pytest.raises(DatabaseError), transaction.atomic(), as_user(users["OWNER"]):
        write("UPDATE public.client_notes SET body='Cambiar evidencia' WHERE id=%s", [note["id"]])
    with pytest.raises(Exception), transaction.atomic(), as_user(users["OWNER"]):
        clients.update_client(
            org, source["id"], {"expected_updated_at": timezone.now(), "name": "Otro"}
        )
    with as_user(users["OWNER"]):
        service.start_successor(org, project, "REV-A")
        current = service.project_row(org, project)
        revised = service.update_project(org, project, {
            "expected_updated_at": current["updated_at"],
            "delivery_address": "Camino Sur 1550, acceso posterior, Puente Alto",
        })
        assert revised["client_address_id"] is None
        assert "acceso posterior" in revised["delivery_address"]
    assert sealed == one("SELECT snapshot_json,snapshot_sha256 FROM public.project_versions WHERE id=%s",
                         [version["id"]])


def test_child_edit_invalidates_merge_review_and_distinct_ruts_block(people):
    org, _, users, _ = people
    source = customer(org, users["OWNER"])
    target = customer(org, users["OWNER"], name="Destino", contacts=[], addresses=[])
    with as_user(users["OWNER"]):
        write(
            "UPDATE public.client_addresses SET address='Otra dirección' WHERE id=%s AND org_id=%s",
            [source["addresses"][0]["id"], org],
        )
        with pytest.raises(DatabaseError, match="client_merge_stale"), transaction.atomic():
            company.rows(
                "SELECT private.merge_clients(%s,%s,%s,%s,%s,'Revisión antigua')",
                [org, source["id"], target["id"], source["updated_at"], target["updated_at"]],
            )
        clients.update_client(
            org,
            target["id"],
            {
                "expected_updated_at": one(
                    "SELECT updated_at FROM public.clients WHERE id=%s", [target["id"]]
                )["updated_at"],
                "rut": "76.543.210-3",
            },
        )
    distinct = customer(org, users["OWNER"], rut="12.345.678-5")
    with as_user(users["OWNER"]):
        assert clients.merge_preview(org, distinct["id"], target["id"])["blockers"]


def test_company_role_gates_last_owner_mfa_bootstrap_and_legal_rut(people, monkeypatch):
    org, _, users, _ = people
    customer(org, users["OWNER"])
    with as_user(users["OPERATOR"]):
        assert not rows("SELECT id FROM public.clients WHERE org_id=%s", [org])
        assert not rows("SELECT id FROM public.client_contacts WHERE org_id=%s", [org])
    api = APIClient()
    for role, status in (("OWNER", 200), ("ESTIMATOR", 403), ("OPERATOR", 403)):
        user = users[role]
        token = VerifiedSupabaseToken(
            "test",
            {"sub": str(user), "role": "authenticated", "aal": "aal2"},
            user,
            f"p22-{user}@example.test",
            "aal2",
        )
        api.force_authenticate(SupabaseUser(user, token.email), token)
        with as_user(user):
            assert (
                api.get("/api/v1/organization/users/", HTTP_X_ORGANIZATION_ID=str(org)).status_code
                == status
            )
            assert (
                api.get(
                    "/api/v1/organization/numbering/", HTTP_X_ORGANIZATION_ID=str(org)
                ).status_code
                == 200
            )
    with as_user(users["OWNER"]):
        own = next(row for row in company.users(org)["items"] if row["role"] == "OWNER")
        with pytest.raises(DatabaseError, match="company_last_owner"), transaction.atomic():
            company.change_user(
                org,
                own["id"],
                {"role": "ESTIMATOR", "is_active": False, "expected_updated_at": own["updated_at"]},
            )
        before = company.get_company(org)
        with pytest.raises(DatabaseError, match="company_rut_invalid"), transaction.atomic():
            rows(
                "SELECT private.save_company(%s,'Nueva','12.345.678-4','CLP',false,%s)",
                [org, before["updated_at"]],
            )
        company.save_company(
            org,
            {
                "name": "Maitenes",
                "tax_id": "76.543.210-3",
                "currency": "USD",
                "require_mfa": True,
                "expected_updated_at": before["updated_at"],
            },
        )
    user = users["ESTIMATOR"]
    with authenticated_rls_context({"sub": str(user), "role": "authenticated", "aal": "aal1"}):
        rows("SELECT set_config('request.jwt.claim.sub',%s,true)", [str(user)])
        assert MembershipRepository().list_active_for_user(user)[0].require_mfa
        assert not rows("SELECT id FROM public.tenancy_organizations WHERE id=%s", [org])
        assert not rows("SELECT id FROM public.clients WHERE org_id=%s", [org])


def test_invitation_verified_email_acceptance_replay_revocation_and_mfa(people):
    import hashlib

    org, other, users, outsider = people
    user = uuid4()
    write(
        "INSERT INTO auth.users(id,email,email_confirmed_at) VALUES(%s,'new@example.test',now())",
        [user],
    )
    token = "test-invitation-capability-only-" + uuid4().hex
    digest = hashlib.sha256(token.encode()).hexdigest()
    with as_user(users["OWNER"]):
        invitation = one(
            "SELECT private.create_company_invitation(%s,%s,'new@example.test','OWNER',%s) AS id",
            [org, uuid4(), digest],
        )["id"]
    with as_user(outsider):
        assert not rows("SELECT * FROM private.inspect_company_invitation(%s)", [digest])
    with authenticated_rls_context({"sub": str(user), "role": "authenticated", "aal": "aal1"}):
        rows("SELECT set_config('request.jwt.claim.sub',%s,true)", [str(user)])
        assert company.invitation(token)["organization_name"] == "Documentary A"
        with (
            pytest.raises(DatabaseError, match="company_invitation_mfa_required"),
            transaction.atomic(),
        ):
            company.accept_invitation(token)
    with as_user(user):
        assert company.accept_invitation(token)["organization_id"] == org
        assert company.accept_invitation(token)["organization_id"] == org
        assert (
            len(
                rows(
                    "SELECT id FROM public.tenancy_memberships WHERE org_id=%s AND user_id=%s",
                    [org, user],
                )
            )
            == 1
        )
    write(
        "UPDATE public.organization_invitations SET expires_at=now()-interval '1 day' WHERE id=%s",
        [invitation],
    )
    with as_user(user):
        assert company.invitation(token)["accepted"]
    with as_user(users["OWNER"]):
        # Same-tenant duplicate active access cannot create a new invitation.
        with (
            pytest.raises(DatabaseError, match="company_user_already_active"),
            transaction.atomic(),
        ):
            rows(
                "SELECT private.create_company_invitation(%s,%s,'new@example.test','ESTIMATOR',%s)",
                [org, uuid4(), hashlib.sha256((token + "x").encode()).hexdigest()],
            )
    pending_token = token + "y"
    with as_user(outsider):
        pending = one(
            "SELECT private.create_company_invitation(%s,%s,'new@example.test','ESTIMATOR',%s) AS id",
            [other, uuid4(), hashlib.sha256(pending_token.encode()).hexdigest()],
        )["id"]
        company.revoke_invitation(other, pending)
    with as_user(user), pytest.raises(Exception, match="disponible"):
        company.accept_invitation(pending_token)


def test_invitation_replay_requires_live_verified_identity_and_owner(people):
    import hashlib

    org, _, users, _ = people
    invited = uuid4()
    write("INSERT INTO auth.users(id,email) VALUES(%s,'pending-p22@example.test')", [invited])
    token = "invitation-test-" + uuid4().hex
    digest = hashlib.sha256(token.encode()).hexdigest()
    key = uuid4()
    with as_user(users["OWNER"]):
        identity = rows(
            "SELECT private.create_company_invitation(%s,%s,'pending-p22@example.test','ESTIMATOR',%s) AS id",
            [org, key, digest],
        )[0]["id"]
        assert (
            rows(
                "SELECT private.create_company_invitation(%s,%s,'pending-p22@example.test','ESTIMATOR',%s) AS id",
                [org, key, "a" * 64],
            )[0]["id"]
            == identity
        )
        from projects.company_views import company_errors

        with (
            pytest.raises(Exception, match="otra invitación"),
            company_errors(),
            transaction.atomic(),
        ):
            rows(
                "SELECT private.create_company_invitation(%s,%s,'other-p22@example.test','ESTIMATOR',%s)",
                [org, key, "b" * 64],
            )
    with as_user(invited), pytest.raises(Exception, match="disponible"):
        company.accept_invitation(token)
    write("UPDATE auth.users SET email_confirmed_at=now() WHERE id=%s", [invited])
    write(
        "UPDATE public.tenancy_memberships SET role='OWNER' WHERE org_id=%s AND user_id=%s",
        [org, users["ESTIMATOR"]],
    )
    with as_user(users["ESTIMATOR"]):
        creator = next(
            u
            for u in company.users(org)["items"]
            if u["email"] == f"p22-{users['OWNER']}@example.test"
        )
        company.change_user(
            org,
            creator["id"],
            {"role": "OWNER", "is_active": False, "expected_updated_at": creator["updated_at"]},
        )
    with as_user(invited), pytest.raises(Exception, match="disponible"):
        company.accept_invitation(token)
    assert not rows(
        "SELECT id FROM public.tenancy_memberships WHERE org_id=%s AND user_id=%s", [org, invited]
    )


def test_section_patch_is_consumed_and_preview_keeps_sealed_numbers(people):
    org, _, users, _ = people
    project, _, operation = _seed_project(org, users["OWNER"])
    version = _freeze(org, users["OWNER"], project, operation)
    before = one(
        "SELECT snapshot_json,snapshot_sha256 FROM public.project_versions WHERE id=%s",
        [version["id"]],
    )
    with as_user(users["ESTIMATOR"]):
        branding = org_branding.get_branding(org_id=org)
        org_branding.save_branding(
            org_id=org,
            data={
                "expected_updated_at": branding["updated_at"],
                "document_preferences": {
                    "quotation_valid_days": 23,
                    "paper": "A4",
                    "legal_footer": "Pie vigente de Maitenes",
                },
            },
        )
        prefs = org_branding.get_branding(org_id=org)["document_preferences"]
        assert prefs["paper"] == "A4"
        assert prefs["quotation_valid_days"] == 23
        assert prefs["legal_footer"] == "Pie vigente de Maitenes"
        with pytest.raises(Exception, match="Recarga"), transaction.atomic():
            org_branding.save_branding(
                org_id=org,
                data={
                    "expected_updated_at": branding["updated_at"],
                    "document_preferences": {"paper": "A4"},
                },
            )
        from documents.service import _prepared_valid_until

        with documentary_backend():
            assert _prepared_valid_until({}, org) == timezone.localdate() + timedelta(days=23)
        content = company.preview(
            org,
            {
                "version_id": version["id"],
                "branding": {
                    "commercial_name": "Marca Maitenes",
                    "document_preferences": {"quotation_valid_days": 23},
                },
            },
        )
    text = "\n".join(page.extract_text() for page in PdfReader(BytesIO(content)).pages)
    assert "Marca Maitenes" in text
    assert "Pie vigente de Maitenes" in text
    assert D(str(PdfReader(BytesIO(content)).pages[0].mediabox.width)).quantize(D("0.01")) == D(
        "595.28"
    )
    assert (timezone.localdate() + timedelta(days=23)).strftime("%d-%m-%Y") in text
    assert before == one(
        "SELECT snapshot_json,snapshot_sha256 FROM public.project_versions WHERE id=%s",
        [version["id"]],
    )


def test_company_currency_proposes_new_prices_without_reinterpreting_sealed_money(people):
    org, _, users, _ = people
    project, _, operation = _seed_project(org, users["OWNER"])
    version = _freeze(org, users["OWNER"], project, operation)
    sealed = one("SELECT snapshot_sha256 FROM public.project_versions WHERE id=%s", [version["id"]])
    with as_user(users["OWNER"]):
        before = company.get_company(org)
        company.save_company(
            org,
            {
                **{key: before[key] for key in ("name", "tax_id", "require_mfa")},
                "currency": "USD",
                "expected_updated_at": before["updated_at"],
            },
        )
        assert company.get_company(org)["currency"] == "USD"
        assert company.get_company(org)["base_currency"] == "CLP"
        assert one("SELECT currency FROM public.tenancy_organizations WHERE id=%s", [org])["currency"] == "CLP"
        assert service.project_public(org, service.project_row(org, project))["currency"] == "CLP"
        token = VerifiedSupabaseToken(
            "test",
            {"sub": str(users["OWNER"]), "role": "authenticated", "aal": "aal2"},
            users["OWNER"],
            f"p22-{users['OWNER']}@example.test",
            "aal2",
        )
        api = APIClient()
        api.force_authenticate(SupabaseUser(token.user_id, token.email), token)
        result = api.get("/api/v1/pricing/options/", HTTP_X_ORGANIZATION_ID=str(org))
        assert result.status_code == 200
        assert result.json()["default_currency"] == "USD"
    assert sealed == one(
        "SELECT snapshot_sha256 FROM public.project_versions WHERE id=%s", [version["id"]]
    )


@pytest.mark.parametrize(("base", "preferred", "labor", "installation"), [
    ("USD", "CLP", "8505", "17010"), ("CLP", "USD", "0.01", "0.02"),
])
def test_preferred_currency_consumes_base_labor_with_declared_fx(people, base, preferred, labor, installation):
    from pricing.service import preview

    org, _, users, _ = people
    project, _, _ = _seed_project(org, users["OWNER"], apply_pricing=False)
    # This new fixture declares its process rates; the CLP material list retains
    # its own currency. A preference must never reinterpret either authority.
    write("UPDATE public.tenancy_organizations SET currency=%s WHERE id=%s", [base, org])
    with as_user(users["OWNER"]):
        admin_write("rules", org, {"labor_rate_per_m2": D("9"), "installation_rate_per_m2": D("18")},
                    "P22 explicitly declared synthetic process rates",
                    one("SELECT id FROM public.pricing_rules WHERE org_id=%s", [org])["id"])
        before = company.get_company(org)
        company.save_company(
            org,
            {
                **{key: before[key] for key in ("name", "tax_id", "require_mfa")},
                "currency": preferred,
                "expected_updated_at": before["updated_at"],
            },
        )
        assert company.get_company(org)["base_currency"] == base
        fx = admin_write(
            "fx", org,
            {"base_currency": "USD", "quote_currency": "CLP",
             "observed_rate": D("900"), "observed_date": date(2026, 9, 10),
             "effective_date": date(2026, 9, 10), "source": "P22 synthetic FX fixture"},
            "P22 declared rate for process costs",
        )
        request = {
            "project_id": project, "pricing_mode": "COST_PLUS_MARGIN",
            "currency": company.get_company(org)["currency"],
            "effective_date": date(2026, 9, 10), "context_code": "DEFAULT",
            "discount_pct": D("0"), "target_margin": D("0.35"),
            "segment": "RETAIL", "confirmed": False,
            "reason": "P22 new calculation with preferred currency", "_actor_id": users["OWNER"],
        }
        from dekopen_engine.commercial import PricingError

        with pytest.raises(PricingError, match="missing_fx_authority"), commercial_backend():
            preview(org, _tenant(org, "OWNER"), request)
        with commercial_backend():
            result = preview(org, _tenant(org, "OWNER"), {**request, "fx_snapshot_id": fx["id"]})
        assert result["currency"] == preferred
        assert D(result["positions_breakdown"][0]["labor_rate_per_m2"]) == D(labor)
        assert D(result["positions_breakdown"][0]["installation_rate_per_m2"]) == D(installation)
        assert D(result["rules"]["labor_rate_per_m2"]) == D("9")
        assert any(item.get("organization_currency") == base for item in result["authorities"])
        assert any(item.get("fx", {}).get("id") == fx["id"] for item in result["authorities"])
        from pricing.workspace import replay_state, _reprice

        stored = decoded(one("SELECT input_snapshot FROM public.pricing_operations WHERE id=%s", [result["id"]])["input_snapshot"])
        state = replay_state(stored["replay"])
        frozen_result = _reprice(org, state, state, state)
        assert frozen_result["net"] == D(str(result["project_net"]))
        assert frozen_result["total"] == D(str(result["project_gross"]))


def test_direct_child_edit_and_merge_serialize_without_lost_changes(documentary_committed_tenant):
    org, _, users, _ = documentary_committed_tenant
    owner = users["OWNER"]
    write(
        "INSERT INTO auth.users(id,email,email_confirmed_at) VALUES(%s,%s,now())",
        [owner, f"p22-{owner}@example.test"],
    )
    source = customer(org, owner)
    target = customer(org, owner, contacts=[], addresses=[])
    start = Barrier(2)

    def attempt(merge):
        close_old_connections()
        try:
            start.wait(timeout=15)
            with transaction.atomic(), as_user(owner):
                rows("SELECT set_config('lock_timeout','15s',true)")
                if merge:
                    clients.merge_client(
                        org,
                        source["id"],
                        {
                            "target_id": target["id"],
                            "expected_source_updated_at": source["updated_at"],
                            "expected_target_updated_at": target["updated_at"],
                            "confirmed": True,
                            "reason": "Fusión concurrente revisada",
                        },
                    )
                else:
                    write(
                        "UPDATE public.client_addresses SET address='Cambio concurrente' WHERE org_id=%s AND id=%s",
                        [org, source["addresses"][0]["id"]],
                    )
            return "merge" if merge else "edit"
        except DatabaseError as error:
            code = getattr(error.__cause__, "sqlstate", None)
            assert code not in ("40P01", "55P03"), "Lock order must not deadlock or time out"
            return "rejected"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt, [True, False]))
    assert outcomes.count("rejected") == 1
    with as_user(owner):
        live = clients.client_public(org, source["id"])
        consolidated = clients.client_public(org, target["id"])
        if "merge" in outcomes:
            assert live["merged_into_id"] == target["id"]
            assert consolidated["addresses"][0]["address"] == source["addresses"][0]["address"]
        else:
            assert live["merged_into_id"] is None
            assert live["addresses"][0]["address"] == "Cambio concurrente"
