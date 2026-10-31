"""Public consent, chosen authority and payer return on real tenant/RLS data."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal as D
from threading import Barrier
from urllib.parse import parse_qs, urlsplit
from uuid import UUID, uuid4

from django.db import DatabaseError, connection, connections, transaction
import pytest

from analytics.today import quotation_rows, commercial_actions
from backend.tests.integration.test_shot09_documentary import (
    as_user, documentary_tenant as documentary_tenant,
    documentary_committed_tenant as documentary_committed_tenant,
    _seed_project, _freeze, FakeStorage,
)
from backend.tests.integration.test_shot10_revision_lifecycle import price_current
from documents.repository import DocumentaryError, documentary_backend, decoded, one, rows, write
from documents.service import prepare_documentary_inputs, save_documentary_inputs, revision_snapshot
from portal import service as portal
from portal import payments as payer
from portal.document_links import document_portal_url
from projects import service as projects, payments, simulated_flow, receipts, invoices
from purchasing.service import confirm_order_type_batch
from production import service as production
from projects.serializers import PositionWriteSerializer

pytestmark = pytest.mark.rls_integration


def issue(org, owner, *, expired=False):
    project, position, operation = _seed_project(org, owner)
    if expired:
        with as_user(owner), documentary_backend():
            write("UPDATE project_documentary_inputs SET quotation_valid_until='2020-01-01' WHERE project_id=%s", [project])
    version = _freeze(org, owner, project, operation)
    with as_user(owner):
        link = portal.share_quote(org_id=org, project_id=project, actor_id=owner, role='OWNER')
    return project, position, UUID(version['id']), link['token']


def response(token, *, decision='APPROVED', selected=None, **extra):
    quote = portal.portal_quote(token, track=False)
    option = next(item for item in quote['options'] if item['revision_code'] == (selected or quote['revision_code']))
    return dict(token=token, decision=decision, decided_by='Ana Pérez', decided_rut='12.345.678-5',
        selected_revision=option['revision_code'], expected_offering_sha256=quote['offering_sha256'],
        expected_selected_sha256=option['snapshot_sha256'], confirmed=decision=='APPROVED',
        consent_text=option['consent_text'], ip_address='203.0.113.7', user_agent='Cliente móvil', **extra)


def another_token(org, owner, version_id):
    # Sharing replaces earlier SHARE links by P25's contract. A printed
    # document capability coexists and exercises a second valid token.
    with as_user(owner), documentary_backend():
        version,_=revision_snapshot(version_id,org)
        return document_portal_url(org_id=org,version=version,actor_id=owner).rsplit('/',1)[-1]


def test_consent_is_complete_immutable_private_and_shared_between_tokens(documentary_tenant):
    org, _, users, outsider = documentary_tenant
    owner = users['OWNER']
    project, _, version, token = issue(org, owner)
    second = another_token(org,owner,version)
    wrong = response(token)
    wrong['consent_text'] += ' cambiado'
    with pytest.raises(DocumentaryError, match='quote_consent_stale'):
        portal.decide_quote(**wrong)
    accepted = portal.decide_quote(**response(token))
    assert accepted['approval_status']=='APPROVED' and accepted['decided_by'] is None
    assert '203.0.113.7' not in str(accepted) and '12.345.678-5' not in str(accepted)
    replay = response(second, decision='DECLINED', note='No debe reemplazar el primer consentimiento')
    assert portal.decide_quote(**replay)['approval_status']=='APPROVED'
    with as_user(owner), documentary_backend():
        decision = one('SELECT * FROM quote_decisions WHERE org_id=%s', [org])
        evidence = decoded(decision['evidence'])
        assert evidence['name']=='Ana Pérez' and evidence['rut']=='12.345.678-5'
        assert evidence['ip_address']=='203.0.113.7' and evidence['user_agent']=='Cliente móvil'
        assert evidence['confirmed'] is True and evidence['consent']==accepted['consent_text']
        assert evidence['offering_revision']==evidence['selected_revision']=='REV-A'
        assert evidence['offering_sha256']==evidence['selected_sha256']==accepted['offering_sha256']
        assert decision['decided_at'] and decision['selected_version_id']==version
        assert len(rows('SELECT id FROM quote_decisions WHERE org_id=%s',[org]))==1
        for sql in ("UPDATE quote_decisions SET evidence='{}' WHERE org_id=%s", 'DELETE FROM quote_decisions WHERE org_id=%s'):
            with pytest.raises(DatabaseError), transaction.atomic():
                write(sql, [org])
        ledger = portal.list_approvals(org_id=org,project_id=project)
        assert all(item['status']=='APPROVED' and item['evidence']==evidence for item in ledger)
    for user in (users['WORKSHOP_MANAGER'], users['INSTALLER'], outsider):
        with as_user(user), documentary_backend():
            assert rows('SELECT evidence FROM quote_decisions WHERE org_id=%s',[org])==[]
    with transaction.atomic(), portal.portal_backend():
        portal._approval_for_token(token)
        with pytest.raises(DatabaseError, match='permission denied'), transaction.atomic():
            rows('SELECT evidence FROM quote_decisions WHERE org_id=%s',[org])


@pytest.mark.parametrize('decision',['CHANGES_REQUESTED','DECLINED'])
def test_changes_mark_exact_sealed_position_and_rejection_is_distinct(documentary_tenant,decision):
    org, _, users, _ = documentary_tenant
    project, position, _, token = issue(org, users['OWNER'])
    wrong = response(token, decision=decision, note='Cambiar vidrio', position_id=uuid4())
    with pytest.raises(DocumentaryError, match='quote_position_not_offered'):
        portal.decide_quote(**wrong)
    quote=portal.decide_quote(**response(token,decision=decision,note='Cambiar vidrio',position_id=position))
    assert quote['approval_status']==decision and quote['payment_provider'] is None
    with as_user(users['OWNER']):
        row=quotation_rows(org)[0]
        assert row['decision_kind']==decision and row['decided_note']=='Cambiar vidrio'
        actions,_=commercial_actions(org,date(2026,10,11),'OWNER')
        assert any(item['kind']=='quote_response' and item['title']==('Revisa los cambios solicitados' if decision=='CHANGES_REQUESTED' else 'Revisa el rechazo del cliente') for item in actions)
        with documentary_backend():
            item=one('SELECT position_id FROM quote_decisions WHERE org_id=%s',[org])
        assert item['position_id']==position and projects.project_row(org,project)['status']=='QUOTED'
        with pytest.raises(DocumentaryError,match='quote_already_decided'):
            portal.approve_internal(org_id=org,project_id=project,actor_id=users['OWNER'],actor_label='Dueño',note='No reemplazar respuesta')


def offered_alternative(org, owner, *, replace_position=False):
    project, position, version_a, _ = issue(org,owner)
    with as_user(owner):
        projects.start_successor(org,project)
        source=projects.position_public(projects.position_row(org,position))
        serializer=PositionWriteSerializer(data={'location_tag':'Oferta nueva','quantity':3,'design':source['design']})
        assert serializer.is_valid(),serializer.errors
        data=serializer.validated_data
        if not replace_position:
            data['expected_updated_at']=source['updated_at']
        saved=projects.save_position(org,project,data,position_id=None if replace_position else position)
        if replace_position:
            current=projects.position_row(org,position)
            projects.delete_position(org,position,current['updated_at'])
        from backend.tests.integration.mounting_fixture import confirm_fixture_measurements
        confirm_fixture_measurements(org,UUID(str(saved['id'])))
        with documentary_backend():
            prepared=prepare_documentary_inputs(org_id=org,project_id=project)
        fields=('position_id','calculation_hash','location_tag','manufacturing_placement_policy_id',
            'handle_requirement_policy_id','reinforcement_cut_policy_id','workshop_annotations','structural_inputs',
            'glass_polishing','handle_intents','accessory_schedule','legacy_handle_migration_confirmed')
        position_inputs=[{key:item[key] for key in fields} for item in prepared['positions']]
        for item,ready in zip(position_inputs,prepared['positions'],strict=True):
            for key,options in [('manufacturing_placement_policy_id','placement_options'),('handle_requirement_policy_id','handle_options'),('reinforcement_cut_policy_id','reinforcement_options')]:
                item[key]=item[key] or ready[options][0]['id']
            item['workshop_annotations']=item['workshop_annotations'] or ready['workshop_suggestions']
            item['glass_polishing']=item['glass_polishing'] or ready['polishing_suggestions']
            item['accessory_schedule']=item['accessory_schedule'] or {'schema_version':1,'coverage':'NONE_REQUIRED','items':[]}
        save_documentary_inputs(org_id=org,actor_id=owner,project_id=project,data={
            'payment_terms':prepared['payment_terms'],'quotation_valid_until':prepared['quotation_valid_until'],
            'commercial_terms':prepared['commercial_terms'],'alternative_version_ids':[version_a],
            'positions':position_inputs})
        operation=price_current(org,owner,'OWNER',project)
        version_b=UUID(_freeze(org,owner,project,operation)['id'])
        token=portal.share_quote(org_id=org,project_id=project,actor_id=owner,role='OWNER')['token']
    return project, position, version_a, version_b, token


@pytest.mark.parametrize('replace_position',[False,True])
def test_alternative_is_authority_for_project_collections_today_workshop_and_new_draft(documentary_tenant,replace_position,monkeypatch):
    org, _, users, _=documentary_tenant
    owner=users['OWNER']
    project,position,version_a,version_b,token=offered_alternative(org,owner,replace_position=replace_position)
    with as_user(owner), documentary_backend():
        before=rows('SELECT id,snapshot_json::text,snapshot_sha256 FROM project_versions WHERE project_id=%s ORDER BY id',[project])
        _,snapshot_a=revision_snapshot(version_a,org)
    accepted=portal.decide_quote(**response(token,selected='REV-A'))
    assert accepted['selected_revision']=='REV-A' and accepted['revision_code']=='REV-B'
    with as_user(owner):
        view=projects.project_public(org,projects.project_row(org,project),detail=True)
        assert view['accepted_version_id']==str(version_a) and view['positions'][0]['quantity']==2
        assert view['total_price_gross']==accepted['total_price_gross']
        deal=payments.list_payments(org_id=org,project_id=project)
        assert D(deal['quote_total_gross'])==D(accepted['total_price_gross'])
        assert D(quotation_rows(org)[0]['total'])==D(accepted['total_price_gross'])
        monkeypatch.setattr(invoices,'SupabaseDocumentStorage',FakeStorage)
        invoice=invoices.issue_invoice(org_id=org,project=projects.project_row(org,project),actor_id=owner,document_kind='BOLETA')
        with documentary_backend():
            sealed_invoice=one('SELECT project_version_id,payload_json FROM project_invoices WHERE id=%s',[invoice['id']])
        assert sealed_invoice['project_version_id']==version_a
        assert decoded(sealed_invoice['payload_json'])['revision_code']=='REV-A'
        copied=projects.clone_project(org,owner,project,{'expected_updated_at':projects.project_row(org,project)['updated_at'],'name':'Copia de la opción aceptada'})
        assert copied['positions'][0]['quantity']==2 and not copied['pricing_current']
    with as_user(users['WORKSHOP_MANAGER']):
        with pytest.raises(DocumentaryError,match='quote_solution_not_selected'):
            confirm_order_type_batch(org_id=org,actor_id=users['WORKSHOP_MANAGER'],version_id=version_b,
                                     order_type='SUPPLIER_GLASS_PO',confirmed=True)
        assert any(item['version_id']==str(version_a) for item in production.production_prep(org_id=org)['versions'])
        with pytest.raises(DocumentaryError,match='version_superseded'):
            production.release_production(org_id=org,version_id=version_b,actor_id=users['WORKSHOP_MANAGER'])
        # Exercise real release, then roll back only this test's trial release.
        with transaction.atomic():
            released=production.release_production(org_id=org,version_id=version_a,actor_id=users['WORKSHOP_MANAGER'])
            assert released['orders']
            transaction.set_rollback(True)
    with as_user(owner):
        next_draft=projects.start_successor(org,project)
        assert next_draft['current_revision']=='REV-C' and not next_draft['pricing_current']
        assert str(next_draft['positions'][0]['id'])==str(position) and next_draft['positions'][0]['quantity']==2
        assert next_draft['positions'][0]['measurements']['state']!='CONFIRMED'
        with documentary_backend():
            after=rows('SELECT id,snapshot_json::text,snapshot_sha256 FROM project_versions WHERE project_id=%s ORDER BY id',[project])
        assert after==before and snapshot_a['positions'][0]['quantity']==2
    assert portal.portal_quote(token,track=False)['payment_provider'] is None


def test_public_payment_is_bounded_idempotent_encrypted_and_returns_to_proposal(documentary_tenant,monkeypatch,settings):
    org, _, users, _=documentary_tenant
    project,_,_,token=issue(org,users['OWNER'])
    settings.BILLING_FRONTEND_ORIGIN='http://127.0.0.1:5173'
    settings.BILLING_CALLBACK_ORIGIN='https://callback.example.test'
    monkeypatch.setattr(receipts,'SupabaseDocumentStorage',FakeStorage)
    data=dict(token=token,amount=D('1'),payer_email='ana@example.test',operation_key=uuid4())
    with pytest.raises(Exception) as denied:
        payer.create(**data)
    assert denied.value.contract_code=='portal_payment_unavailable'
    approved=portal.decide_quote(**response(token))
    with as_user(users['OWNER']),documentary_backend(),connection.cursor() as cursor:
        cursor.execute('INSERT INTO collection_preferences(org_id,simulation_enabled,updated_by) VALUES(%s,false,%s) '
                       'ON CONFLICT(org_id) DO UPDATE SET simulation_enabled=false,updated_by=EXCLUDED.updated_by',[org,users['OWNER']])
    assert portal.portal_quote(token,track=False)['payment_provider'] is None
    with pytest.raises(Exception) as disabled:
        payer.create(**data)
    assert disabled.value.contract_code=='portal_payment_unavailable'
    with as_user(users['OWNER']),documentary_backend(),connection.cursor() as cursor:
        cursor.execute('UPDATE collection_preferences SET simulation_enabled=true WHERE org_id=%s',[org])
    data['amount']=D(approved['payment']['balance'])
    with pytest.raises(Exception) as denied:
        payer.create(**{**data,'amount':data['amount']+1})
    assert denied.value.contract_code=='payment_exceeds_balance'
    created=payer.create(**data)
    assert payer.create(**data)==created and created['simulated'] is True
    assert portal.portal_quote(token,track=False)['payment_url']==created['url']
    with as_user(users['OWNER']),documentary_backend():
        offered=one('SELECT id FROM project_versions WHERE org_id=%s AND project_id=%s',[org,project])
    unrelated=another_token(org,users['OWNER'],offered['id'])
    assert portal.portal_quote(unrelated,track=False)['payment_url'] is None
    link_id=UUID(urlsplit(created['url']).path.rsplit('/',1)[-1])
    capability=parse_qs(urlsplit(created['url']).query)['token'][0]
    with as_user(users['OWNER']),documentary_backend():
        ctx=one('SELECT * FROM portal_payment_contexts WHERE org_id=%s',[org])
        assert token not in ctx['token_ciphertext']
        assert len(rows('SELECT id FROM project_payment_links WHERE org_id=%s',[org]))==1
    pending=simulated_flow.payer_status(link_id=link_id,token=capability)
    access=parse_qs(urlsplit(pending['portal_path']).query)['access'][0]
    assert pending['portal_path'].startswith('/cotizacion/'+token+'?pago=')
    assert payer.result(context_id=ctx['id'],access=access)['status']=='PENDING'
    with pytest.raises(Exception) as denied:
        payer.result(context_id=ctx['id'],access='wrong')
    assert denied.value.contract_code=='portal_payment_return_not_found'
    paid=simulated_flow.confirm(link_id=link_id,token=capability,outcome='PAID')
    assert paid['status']=='PAID' and simulated_flow.confirm(link_id=link_id,token=capability,outcome='FAILED')['status']=='PAID'
    assert payer.result(context_id=ctx['id'],access=access)['status']=='PAID'
    final=portal.portal_quote(token,track=False)
    assert final['payment_provider'] is None and final['payment_url'] is None and D(final['payment']['balance'])==0
    with as_user(users['OWNER']):
        ledger=payments.list_payments(org_id=org,project_id=project)
        assert len(ledger['payments'])==1 and ledger['payments'][0]['receipt_id']


def test_invoice_already_issued_requires_reconciliation_before_another_solution(documentary_tenant,monkeypatch):
    org,other,users,_=documentary_tenant
    project,_,version_a,_,token=offered_alternative(org,users['OWNER'])
    monkeypatch.setattr(invoices,'SupabaseDocumentStorage',FakeStorage)
    with as_user(users['OWNER']):
        issued=invoices.issue_invoice(org_id=org,project=projects.project_row(org,project),actor_id=users['OWNER'],document_kind='BOLETA')
        with documentary_backend():
            before=one('SELECT payload_json::text,file_sha256 FROM project_invoices WHERE id=%s',[issued['id']])
    with pytest.raises(DocumentaryError,match='quote_option_committed'):
        portal.decide_quote(**response(token,selected='REV-A'))
    with transaction.atomic(),portal.portal_backend():
        portal._approval_for_token(token)
        assert one('SELECT private.quote_has_conflicting_invoice(%s,%s,%s) AS present',[other,project,version_a])['present'] is False
    assert portal.portal_quote(token,track=False)['approval_status']=='PENDING'
    approved=portal.decide_quote(**response(token,selected='REV-B'))
    assert approved['approval_status']=='APPROVED' and approved['selected_revision']=='REV-B'
    with as_user(users['OWNER']),documentary_backend():
        assert one('SELECT payload_json::text,file_sha256 FROM project_invoices WHERE id=%s',[issued['id']])==before


def test_direct_simulator_does_not_bypass_approval(documentary_tenant,settings):
    org,_,users,_=documentary_tenant
    project,_,_,_=issue(org,users['OWNER'])
    settings.BILLING_FRONTEND_ORIGIN='http://127.0.0.1:5173'
    with as_user(users['OWNER']):
        link=simulated_flow.create_link(org_id=org,project_id=project,actor_id=users['OWNER'],data={
            'operation_key':str(uuid4()),'kind':'ANTICIPO','amount':D('1'), 'payer_email':'ana@example.test'})['link']
    capability=parse_qs(urlsplit(link['url']).query)['token'][0]
    for action in (lambda:simulated_flow.payer_status(link_id=link['id'],token=capability),
                   lambda:simulated_flow.confirm(link_id=link['id'],token=capability,outcome='PAID')):
        with pytest.raises(Exception) as denied:
            action()
        assert denied.value.contract_code=='payment_requires_approval'


def test_successor_capability_requires_sealed_permission_and_tenant_scope(documentary_tenant):
    org,_,users,_=documentary_tenant
    with connection.cursor() as cursor:
        cursor.execute("UPDATE tenancy_organizations SET document_preferences="
                       "jsonb_set(COALESCE(document_preferences,'{}'::jsonb),'{portal_successor_link}','true'::jsonb) WHERE id=%s",[org])
    _,_,version_a,version_b,_=offered_alternative(org,users['OWNER'])
    old=another_token(org,users['OWNER'],version_a)
    current=another_token(org,users['OWNER'],version_b)
    quote=portal.portal_quote(old,track=False)
    assert quote['superseded'] and quote['successor_path']=='/cotizacion/'+current
    assert quote['payment_provider'] is None and quote['quote_pdf_url'] is None
    with transaction.atomic(),portal.portal_backend():
        portal._approval_for_token(old)
        assert rows('SELECT * FROM private.quote_successor_link(%s,%s)',[uuid4(),version_a])==[]
        with pytest.raises(DatabaseError,match='permission denied'),transaction.atomic():
            rows('SELECT token_ciphertext FROM document_portal_links')


def test_concurrent_tokens_preserve_first_human_decision(documentary_committed_tenant):
    org,_,users,_=documentary_committed_tenant
    _,_,version,token=issue(org,users['OWNER'])
    second=another_token(org,users['OWNER'],version)
    inputs=[response(token),response(second,decision='DECLINED',note='Otra respuesta')]
    barrier=Barrier(2)
    def decide(data):
        try:
            barrier.wait(timeout=10)
            return portal.decide_quote(**data)['approval_status']
        finally:
            connections.close_all()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(decide,data) for data in inputs]
        states=[future.result(timeout=45) for future in futures]
    assert states[0]==states[1] and states[0] in ('APPROVED','DECLINED')
    with connection.cursor() as cursor:
        cursor.execute('SELECT count(*) FROM quote_decisions WHERE org_id=%s',[org])
        assert cursor.fetchone()[0]==1


def test_the_client_sees_the_3d_only_when_the_issuer_plan_includes_it(documentary_tenant):
    org, _, users, _ = documentary_tenant
    _, _, _, token = issue(org, users['OWNER'])
    assert portal.portal_quote(token, track=False)['client_3d'] is True
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_setting('role')")
        role = cursor.fetchone()[0]
        cursor.execute("RESET ROLE")
        cursor.execute("UPDATE public.tenancy_organizations SET subscription_tier='STARTER' WHERE id=%s", [org])
        cursor.execute(f"SET ROLE {role}" if role != "none" else "RESET ROLE")
    assert portal.portal_quote(token, track=False)['client_3d'] is False
