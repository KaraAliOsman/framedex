"""P15: released OT → purchase → damaged receipt → exact stock, under RLS."""
from decimal import Decimal
from uuid import UUID,uuid4

from django.db import DatabaseError,transaction
import pytest

from tests.integration.test_shot09_documentary import (
    documentary_tenant as documentary_tenant,_seed_project,_freeze,_eligibility_data,as_user)
from tests.integration.test_shot08_pricing import owner_client
from documents.repository import one,rows,documentary_backend
from purchasing.service import create_eligibility,allocate_requirement,purchasing_state,confirm_order_type_batch
from production.service import release_production
from authentication.rls import authenticated_rls_context
from tests.integration.test_shot08_pricing import committed_commercial_rows as committed_commercial_rows

pytestmark=pytest.mark.rls_integration


def purchase_fixture(org,users):
    project,_,operation=_seed_project(org,users['OWNER'])
    version=UUID(_freeze(org,users['OWNER'],project,operation)['id'])
    with as_user(users['WORKSHOP_MANAGER']):
        state=purchasing_state(org,version)
        for kind in {r['order_type'] for r in state['requirements']}:
            lines=[r for r in state['requirements'] if r['order_type']==kind]
            eligible=create_eligibility(org_id=org,actor_id=users['WORKSHOP_MANAGER'],version_id=version,
                data=_eligibility_data(kind,[r['requirement_key'] for r in lines],kind))
            for line in lines:
                allocate_requirement(org_id=org,actor_id=users['WORKSHOP_MANAGER'],requirement_id=UUID(line['id']),
                                    eligibility_id=UUID(eligible['id']))
        release_production(org_id=org,version_id=version,actor_id=users['WORKSHOP_MANAGER'])
    return project,version


def test_released_needs_purchase_replay_and_exact_receipt_trace(documentary_tenant):
    org,other,users,_=documentary_tenant
    _,version=purchase_fixture(org,users)
    manager=owner_client(users['WORKSHOP_MANAGER'])
    estimator=owner_client(users['ESTIMATOR'])
    headers={'HTTP_X_ORGANIZATION_ID':str(org)}
    preview=manager.get('/api/v1/purchasing/needs/',**headers)
    assert preview.status_code==200,preview.data
    data=preview.json()
    assert data['lines'] and not data['blockers']
    assert all(line['orders'] and line['project_code'] for line in data['lines'])
    chosen=[line for line in data['lines'] if Decimal(line['purchase'])>0]
    body={'operation_key':str(uuid4()),'preview_hash':data['preview_hash'],'confirmed':True,
          'lines':[{'requirement_id':line['requirement_id'],'quantity':format(Decimal(line['purchase']),'.2f'),'unit_price':'1000.25'} for line in chosen]}
    endpoint='/api/v1/purchasing/needs/confirm/'
    assert estimator.post(endpoint,body,format='json',**headers).status_code==403
    first=manager.post(endpoint,body,format='json',**headers)
    assert first.status_code==200,first.data
    assert manager.post(endpoint,body,format='json',**headers).json()==first.json()
    conflict=manager.post(endpoint,{**body,'lines':[{**body['lines'][0],'unit_price':'2000.25'}]},format='json',**headers)
    assert conflict.status_code==422 and conflict.data['error']['code']=='purchase_operation_conflict'
    stale=manager.post(endpoint,{**body,'operation_key':str(uuid4())},format='json',**headers)
    assert stale.status_code==422 and stale.data['error']['code']=='purchase_preview_stale'
    assert manager.post(endpoint,{**body,'confirmed':False},format='json',**headers).status_code==422
    assert manager.get('/api/v1/purchasing/needs/',HTTP_X_ORGANIZATION_ID=str(other)).status_code==403
    order=next(o for o in first.json()['orders'] if o['order_type']=='SUPPLIER_PROFILE_PO')
    route=f"/api/v1/inventory/orders/{order['id']}/"
    assert manager.post(f"/api/v1/purchasing/orders/{order['id']}/send/",{'confirmed':True},format='json',**headers).status_code==200
    receiving=manager.get(route+'receiving/',**headers).json()
    line=receiving['lines'][0]
    receipt={'receipt_key':'P15-partial','supplier_document':'GUIA-15','received_on':'2026-10-10',
             'lines':[{'order_line_id':line['id'],'received_qty':'2','damaged_qty':'1','lot_code':'LOTE-15','rack_location':'A-15'}]}
    received=manager.post(route+'receipts/',receipt,format='json',**headers)
    assert received.status_code==201,received.data
    replay=manager.post(route+'receipts/',receipt,format='json',**headers)
    assert replay.status_code==200 and replay.json()==received.json()
    stock=estimator.get('/api/v1/inventory/stock/',**headers)
    assert stock.status_code==200,stock.data
    item=next(i for i in stock.json()['items'] if i['sku']==line['purchasing_sku'])
    assert Decimal(str(item['on_hand_qty']))==1
    assert Decimal(str(item['incoming_qty']))==Decimal(str(line['ordered_qty']))-1
    ledger=manager.get('/api/v1/inventory/movements/',**headers).json()['movements']
    move=next(m for m in ledger if m['movement_type']=='RECEIPT')
    assert move['lot_code']=='LOTE-15' and move['rack_location']=='A-15'
    assert move['supplier_document']=='GUIA-15' and move['received_on']=='2026-10-10'
    assert move['order_code'].startswith('OC-') and move['receipt_code'].startswith('REC-')
    # Authenticated cannot read documentary requirement lines. The stock API
    # deliberately crosses to documentary_backend for incoming orders.
    with authenticated_rls_context({'sub':str(users['ESTIMATOR']),'role':'authenticated','aal':'aal2'}),pytest.raises(DatabaseError),transaction.atomic():
        rows('SELECT id FROM order_requirement_lines WHERE org_id=%s',[org])
    overflow={'receipt_key':'P15-overflow','lines':[{'order_line_id':line['id'],
              'received_qty':str(Decimal(str(line['ordered_qty']))+5),'damaged_qty':'0'}]}
    denied=manager.post(route+'receipts/',overflow,format='json',**headers)
    assert denied.status_code==422 and denied.data['error']['code']=='receipt_surplus_confirmation_required',denied.data
    assert one('SELECT count(*) AS n FROM order_receipts WHERE org_id=%s',[org])['n']==1
    accepted=manager.post(route+'receipts/',{**overflow,'confirm_over_receipt':True},format='json',**headers)
    assert accepted.status_code==201,accepted.data
    index=manager.get('/api/v1/purchasing/orders/',**headers).json()['orders']
    assert all(Decimal(str(o['net_amount']))>0 for o in index)
    assert str(version) in {line['version_id'] for line in data['lines']}


def test_rack_transfer_scrap_reason_actor_and_history_is_private(documentary_tenant):
    org,other,users,_=documentary_tenant
    authority=one('SELECT id FROM profile_purchase_mappings WHERE org_id IS NULL LIMIT 1')['id']
    manager=owner_client(users['WORKSHOP_MANAGER'])
    headers={'HTTP_X_ORGANIZATION_ID':str(org)}
    created=manager.post('/api/v1/inventory/remnants/',{'kind':'BAR','stock_authority_id':str(authority),
        'length_mm':'2100','rack_location':'A-01','notes':'Material DEMO'},format='json',**headers)
    assert created.status_code==201,created.data
    remnant=created.json()['id']
    base=f'/api/v1/inventory/remnants/{remnant}/'
    move={'confirmed':True,'reason':'Orden de bodega revisada','rack_location':'B-02'}
    assert manager.post(base+'move/',{**move,'confirmed':False},format='json',**headers).status_code==422
    assert manager.post(base+'move/',move,format='json',**headers).status_code==200
    assert manager.post(base+'scrap/',{},format='json',**headers).status_code==400
    assert manager.post(base+'scrap/',{'confirmed':True,'reason':'Perfil dañado y revisado'},format='json',**headers).status_code==200
    events=manager.get('/api/v1/inventory/remnants/',**headers).json()['events']
    moved=next(e for e in events if e['action']=='MOVE')
    assert moved['previous_rack']=='A-01' and moved['rack_location']=='B-02'
    assert moved['actor_id']==str(users['WORKSHOP_MANAGER']) and moved['reason']==move['reason']
    assert any(e['action']=='SCRAPPED' and e['reason']=='Perfil dañado y revisado' for e in events)
    assert manager.post(base+'move/',move,format='json',**headers).status_code==422
    with as_user(users['WORKSHOP_MANAGER']):
        assert rows('SELECT id FROM inventory_remnant_events WHERE org_id=%s',[other])==[]
        with documentary_backend(),pytest.raises(DatabaseError),transaction.atomic():
            rows("UPDATE inventory_remnant_events SET reason='forged' WHERE org_id=%s RETURNING id",[org])


def test_partial_purchase_capacity_keeps_original_evidence_and_requires_fresh_preview(documentary_tenant):
    org,_,users,_=documentary_tenant
    _,version=purchase_fixture(org,users)
    with as_user(users['WORKSHOP_MANAGER']),documentary_backend():
        state=purchasing_state(org,version)
        line=next(r for r in state['requirements'] if r['order_type']=='SUPPLIER_PROFILE_PO' and r['quantity']>1)
        original=one('SELECT specification,quantity FROM purchase_requirement_lines WHERE id=%s',[line['id']])
        a,_=confirm_order_type_batch(org_id=org,actor_id=users['WORKSHOP_MANAGER'],version_id=version,
             order_type='SUPPLIER_PROFILE_PO',confirmed=True,quantities={line['id']:Decimal(1)})
        b,_=confirm_order_type_batch(org_id=org,actor_id=users['WORKSHOP_MANAGER'],version_id=version,
             order_type='SUPPLIER_PROFILE_PO',confirmed=True,quantities={line['id']:Decimal(line['quantity'])-1})
        assert a[0]['id']!=b[0]['id']
        assert one('SELECT specification,quantity FROM purchase_requirement_lines WHERE id=%s',[line['id']])==original


def test_manual_remnant_cannot_forge_catalog_color_identity_or_size(documentary_tenant):
    org,_,users,_=documentary_tenant
    authority=one('SELECT id FROM profile_purchase_mappings WHERE org_id IS NULL LIMIT 1')['id']
    manager=owner_client(users['WORKSHOP_MANAGER'])
    headers={'HTTP_X_ORGANIZATION_ID':str(org)}
    base={'kind':'BAR','stock_authority_id':str(authority),'length_mm':'2100','rack_location':'A-01'}
    for change in ({'color':'FORGED'},{'physical_stock_identity':'FORGED'},{'length_mm':'999999'}):
        response=manager.post('/api/v1/inventory/remnants/',{**base,**change},format='json',**headers)
        assert response.status_code==422,response.data
    one("INSERT INTO inventory_items(org_id,sku,name,category,unit,attributes) VALUES(%s,'SHEET-P15','Lámina DEMO','GLASS','SHEET',"
        "'{\"sheet_width_mm\":\"2000\",\"sheet_height_mm\":\"1000\",\"glass_sku\":\"VIDRIO-BASE\"}') RETURNING id",[org])
    sheet={'kind':'SHEET','sheet_workshop_sku':'SHEET-P15','width_mm':'500','height_mm':'400','rack_location':'V-01'}
    for change in ({'color':'FORGED'},{'physical_stock_identity':'FORGED'},{'material':'FORGED'},{'width_mm':'2001'}):
        response=manager.post('/api/v1/inventory/remnants/',{**sheet,**change},format='json',**headers)
        assert response.status_code==422,response.data
    created=manager.post('/api/v1/inventory/remnants/',sheet,format='json',**headers)
    assert created.status_code==201,created.data
    assert created.data['material']=='GLASS' and created.data['physical_stock_identity'] is None


def test_concurrent_purchase_intents_seal_one_order_set(committed_commercial_rows):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import close_old_connections,connection
    from purchasing.needs import proposal,confirm_proposal
    org,_,users=committed_commercial_rows
    purchase_fixture(org,users)
    with as_user(users['WORKSHOP_MANAGER']):
        preview=proposal(org_id=org)
    body={'operation_key':str(uuid4()),'preview_hash':preview['preview_hash'],'confirmed':True,
          'lines':[{'requirement_id':UUID(line['requirement_id']),'quantity':Decimal(line['purchase']),
                    'unit_price':Decimal('1000.25')} for line in preview['lines'] if Decimal(line['purchase'])>0]}
    barrier=Barrier(2)
    def decide(_):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            with as_user(users['WORKSHOP_MANAGER']):
                return confirm_proposal(org_id=org,actor_id=users['WORKSHOP_MANAGER'],data=body)
        finally:
            connection.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(decide,[1,2]))
    assert results[0]==results[1] and results[0]['orders']
    assert one('SELECT count(*) AS n FROM purchase_need_decisions WHERE org_id=%s',[org])['n']==1
    assert one("SELECT count(*) AS n FROM orders WHERE org_id=%s AND order_type<>'WORKSHOP_OT'",[org])['n']==len(results[0]['orders'])


def test_supplier_mail_uses_real_sealed_pdf_mime_and_one_delivery_intent(documentary_tenant,monkeypatch):
    from documents.storage import SupabaseDocumentStorage
    from notifications import adapters,crypto,service as mail_service
    org,_,users,_=documentary_tenant
    _,version=purchase_fixture(org,users)
    storage={}
    monkeypatch.setattr(SupabaseDocumentStorage,'upload_immutable',lambda _,key,content,media:storage.setdefault(key,content))
    monkeypatch.setattr(SupabaseDocumentStorage,'download_bounded',lambda _,key,max_bytes:storage[key] if len(storage[key])<=max_bytes else None)
    manager=owner_client(users['WORKSHOP_MANAGER'])
    headers={'HTTP_X_ORGANIZATION_ID':str(org)}
    with as_user(users['WORKSHOP_MANAGER']):
        created,_=confirm_order_type_batch(org_id=org,actor_id=users['WORKSHOP_MANAGER'],version_id=version,
              order_type='SUPPLIER_PROFILE_PO',confirmed=True)
    order=created[0]
    route=f"/api/v1/purchasing/orders/{order['id']}/"
    assert manager.post(route+'send/',{'confirmed':True},format='json',**headers).status_code==200
    preview=manager.get(route+'mail/',**headers)
    assert preview.status_code==200,preview.data
    recipient=preview.data['recipient']
    body={'confirmed':True,'expected_recipient':recipient}
    assert manager.post(route+'mail/',{**body,'confirmed':False},format='json',**headers).status_code==422
    assert manager.post(route+'mail/',{**body,'expected_recipient':'changed@example.test'},format='json',**headers).status_code==422
    first=manager.post(route+'mail/',body,format='json',**headers)
    assert first.status_code==200,first.data
    replay=manager.post(route+'mail/',body,format='json',**headers)
    assert replay.status_code==200 and replay.data['id']==first.data['id']
    assert len(storage)==1
    row=one('SELECT * FROM mail_outbox WHERE id=%s',[first.data['id']])
    payload=crypto.open_message(row['content_ciphertext'],org_id=org,mail_id=row['id'])
    with transaction.atomic(),mail_service.mail_backend():
        mail_service._check_live(row,payload)
    mime=adapters.mime_message(payload,mail_id=row['id'],recipient=recipient)
    attachments=list(mime.iter_attachments())
    assert len(attachments)==1 and attachments[0].get_filename()==order['order_code']+'.pdf'
    assert attachments[0].get_content().startswith(b'%PDF')
    assert attachments[0].get_content()==next(iter(storage.values()))
    assert order['order_code'] in mime['Subject'] and mime['To'].addresses[0].addr_spec==recipient
    with transaction.atomic(),mail_service.mail_backend():
        assert one('SELECT count(*) AS n FROM mail_outbox WHERE org_id=%s',[org])['n']==1
        one("UPDATE mail_outbox SET state='FAILED',attempt=1,error_code='mail_preflight_failed' WHERE id=%s RETURNING id",[row['id']])
    recovery={'expected_attempt':1,'confirmed_remote_absence':True}
    recovered=manager.post(f"/api/v1/mail/{row['id']}/recover/",recovery,format='json',**headers)
    assert recovered.status_code==200 and recovered.data['state']=='QUEUED',recovered.data
    quote=mail_service.seal_mail(org_id=org,actor_id=users['OWNER'],event_key='p15-quote-permission',kind='QUOTE',recipient=recipient,
        message={'subject':'Cotización DEMO','text':'Cotización','html':'<p>Cotización</p>','from_name':'DEMO'})
    with transaction.atomic(),mail_service.mail_backend():
        one("UPDATE mail_outbox SET state='FAILED',attempt=1 WHERE id=%s RETURNING id",[quote['id']])
    assert manager.post(f"/api/v1/mail/{quote['id']}/recover/",recovery,format='json',**headers).status_code==403
