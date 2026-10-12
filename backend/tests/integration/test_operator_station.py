"""P12 real RLS, role projections and atomic, idempotent QC remake."""
from uuid import uuid4

import pytest
from django.db import connection

from backend.tests.integration.test_shot09_documentary import documentary_tenant as documentary_tenant, as_user
from backend.tests.integration.test_shot08_pricing import owner_client
from documents.repository import one, rows

pytestmark = pytest.mark.rls_integration


def setup_work(org, users):
    operator, colleague = uuid4(), uuid4()
    project, order, step = uuid4(), uuid4(), uuid4()
    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO auth.users(id) VALUES(%s),(%s)",[operator,colleague])
        cursor.execute("INSERT INTO tenancy_memberships(org_id,user_id,role) VALUES(%s,%s,'OPERATOR'),(%s,%s,'OPERATOR')",[org,operator,org,colleague])
        cursor.execute("INSERT INTO projects(id,org_id,code,name,client_name,delivery_address,created_by) VALUES(%s,%s,'P12-DEMO','Taller DEMO','Cliente privado','Dirección privada',%s)",[project,org,users['OWNER']])
        cursor.execute("INSERT INTO orders(id,org_id,project_id,order_type,status,order_code,payload_json) VALUES(%s,%s,%s,'WORKSHOP_OT','RELEASED','OT-P12-DEMO',%s::jsonb)",[order,org,project,'{"schema":"production_wo_v1","quantity":1,"materials":{},"routing":["QC","PACK"]}'])
        center=uuid4()
        cursor.execute("INSERT INTO work_centers(id,org_id,code,name,kind) VALUES(%s,%s,'QC-P12','Calidad','QC')",[center,org])
        cursor.execute("INSERT INTO production_steps(id,org_id,order_id,sequence,code,label,status,work_center_id) VALUES(%s,%s,%s,1,'QC','Control de calidad','READY',%s)",[step,org,order,center])
        cursor.execute("INSERT INTO production_steps(org_id,order_id,sequence,code,label,status) VALUES(%s,%s,2,'PACK','Embalaje','READY')",[org,order])
    return operator,colleague,order,step


def test_station_is_per_user_and_tenant_and_operator_http_reads_are_private(documentary_tenant):
    org,other,users,_=documentary_tenant
    operator,colleague,order,_=setup_work(org,users)
    client=owner_client(operator)
    headers={"HTTP_X_ORGANIZATION_ID":str(org)}
    route='/api/v1/production/operator-station/'
    assert client.get(route,**headers).json()['selected_code'] is None
    selected=client.put(route,{"station_code":"QC"},format='json',**headers)
    assert selected.status_code == 200,selected.data
    assert client.get(route,**headers).json()['selected_code'] == 'QC'
    queue=client.get('/api/v1/production/station-queue/',**headers)
    assert queue.status_code == 200,queue.data
    assert len(queue.json()['stations']) == 1
    assert queue.json()['stations'][0]['code'] == 'QC'
    assert len(queue.json()['stations'][0]['entries']) == 1
    assert all(e['is_next'] for s in queue.json()['stations'] for e in s['entries'])
    with as_user(colleague):
        assert rows('SELECT * FROM production_operator_stations') == []
    denied=client.put(route,{"station_code":"QC"},format='json',HTTP_X_ORGANIZATION_ID=str(other))
    assert denied.status_code == 403
    for path in ('prep/',f'orders/{order}/delivery/',f'orders/{order}/dispatch-note/',f'orders/{order}/dispatch-note-dte/',f'orders/{order}/dispatch-note-envio/'):
        response=client.get('/api/v1/production/'+path,**headers)
        assert response.status_code == 403,(path,response.data)
    trace=client.get(f'/api/v1/production/orders/{order}/trace/',**headers)
    assert trace.status_code == 200,trace.data
    assert 'client_name' not in trace.json()['project']
    assert 'Cliente privado' not in str(trace.json()) and 'Dirección privada' not in str(trace.json())
    detail=client.get(f'/api/v1/production/orders/{order}/',**headers)
    assert detail.status_code == 200,detail.data
    assert not {'delivery_address','dispatch_note_dte','dispatch_note_code'} & detail.json().keys()


def test_failed_measurement_only_blocks_when_explicit_and_supervisor_remake_retries_once(documentary_tenant):
    org,_,users,_=documentary_tenant
    operator,_,order,step=setup_work(org,users)
    headers={"HTTP_X_ORGANIZATION_ID":str(org)}
    client,manager=owner_client(operator),owner_client(users['WORKSHOP_MANAGER'])
    body={"action":"QC_CHECK","qc_check":{"check":"Escuadra","expected":"0.00 mm","actual":"1.00 mm","result":"FAIL"}}
    endpoint=f'/api/v1/production/steps/{step}/transition/'
    measurement=client.post(endpoint,body,format='json',**headers)
    assert measurement.status_code == 200,measurement.data
    assert one('SELECT status FROM orders WHERE id=%s',[order])['status'] == 'RELEASED'
    blocked=client.post(endpoint,{**body,"block_on_fail":True},format='json',**headers)
    assert blocked.status_code == 200,blocked.data
    assert blocked.json()['order_status'] == 'HOLD'
    assert rows("SELECT payload FROM production_step_events WHERE order_id=%s AND event='QC_FAILED'",[order])
    operation={"confirmed":True,"operation_key":str(uuid4()),"note":"Escuadra rechazada en control final","item_code":"P01-U01-M01"}
    remake_route=f'/api/v1/production/orders/{order}/qc-remake/'
    assert client.post(remake_route,operation,format='json',**headers).status_code == 403
    rejected=manager.post(remake_route,{**operation,'confirmed':False},format='json',**headers)
    assert rejected.status_code == 422,rejected.data
    first=manager.post(remake_route,operation,format='json',**headers)
    assert first.status_code == 201,first.data
    again=manager.post(remake_route,operation,format='json',**headers)
    assert again.status_code == 201,again.data
    assert first.json()['id'] == again.json()['id']
    assert first.json()['order_code'] == 'OT-P12-DEMO-RM-01'
    assert first.json()['payload']['remake_reason']['qc_item'] == operation['item_code']
    assert one("SELECT count(*) AS n FROM orders WHERE org_id=%s AND payload_json->>'remake_of'=%s",[org,str(order)])['n'] == 1
    assert one('SELECT status FROM orders WHERE id=%s',[order])['status'] == 'HOLD'
