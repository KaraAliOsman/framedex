"""Real PostgreSQL commercial authorities and atomic audit invariants."""

from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from uuid import uuid4

from django.db import connection, transaction, DatabaseError
import pytest

from authentication.rls import authenticated_rls_context
from authentication.types import Membership, TenantContext
from pricing.repository import PricingRepository, admin_write, audit_reason, commercial_backend, rows
from dekopen_engine.commercial import PricingError
from pricing.service import preview, apply_operation
from pricing.repository import json_text, one
from pricing.xlsx_import import import_rows, parse_xlsx
from backend.tests.test_pricing_contract import MAPPING, workbook_bytes

pytestmark = pytest.mark.rls_integration


@pytest.fixture
def commercial_rows(django_db_blocker):
    with django_db_blocker.unblock():
        if connection.vendor != 'postgresql':
            pytest.fail('SHOT-08 requires real PostgreSQL; never skipped')
        with transaction.atomic():
            org, other = uuid4(),uuid4()
            users = {role:uuid4() for role in ('OWNER','ESTIMATOR','WORKSHOP_MANAGER','INSTALLER')}
            with connection.cursor() as cursor:
                cursor.execute('INSERT INTO public.tenancy_organizations(id,name,tax_id) VALUES(%s,%s,%s),(%s,%s,%s)',
                               [org,'Pricing fixture A',str(org),other,'Pricing fixture B',str(other)])
                for role,user in users.items():
                    cursor.execute('INSERT INTO public.tenancy_memberships(org_id,user_id,role) VALUES(%s,%s,%s)',
                                   [org,user,role])
            yield org,other,users
            transaction.set_rollback(True)


@contextmanager
def as_user(user):
    with authenticated_rls_context({'sub':str(user),'role':'authenticated','aal':'aal2'}):
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('request.jwt.claim.sub',%s,true)",[str(user)])
        audit_reason('Independent SHOT-08 integration test')
        yield


def make_list(org, valid_from, price, currency='CLP', valid_to=None, active=True):
    parent = admin_write('cost-lists',org,{'supplier_name':'Fixture supplier','currency':currency,
                        'valid_from':valid_from,'valid_to':valid_to,'is_active':active},'Create fixture list')
    admin_write('cost-items',org,{'cost_list_id':parent['id'],'sku':'SKU-A','item_type':'PROFILE',
                'unit':'M','unit_cost':Decimal(price)},'Create fixture price')
    return parent['id']


def test_temporal_latest_ties_missing_and_no_silent_zero(commercial_rows):
    org,_,users = commercial_rows
    with as_user(users['OWNER']):
        make_list(org,date(2026,9,1),'10')
        make_list(org,date(2026,9,5),'12',valid_to=date(2026,9,10))
        make_list(org,date(2026,9,9),'99',active=False)
        repo = PricingRepository(org,date(2026,9,10),'CLP')
        assert repo.cost('SKU-A','M') == Decimal('12')
        assert PricingRepository(org,date(2026,9,11),'CLP').cost('SKU-A','M') == Decimal('10')
        make_list(org,date(2026,9,5),'13')
        with pytest.raises(PricingError,match='ambiguous_cost_list'):
            repo.cost('SKU-A','M')
        with pytest.raises(PricingError,match='cost_list_not_found'):
            repo.cost('MISSING','M')


def test_fx_snapshot_and_four_decimal_cost(commercial_rows):
    org,_,users = commercial_rows
    with as_user(users['OWNER']):
        make_list(org,date(2026,9,1),'0.1234','USD')
        fx = admin_write('fx',org,{'base_currency':'USD','quote_currency':'CLP',
                         'observed_rate':Decimal('900'),'observed_date':date(2026,9,10),
                         'effective_date':date(2026,9,10),'source':'Synthetic FX fixture'},'Record FX')
        repo = PricingRepository(org,date(2026,9,10),'CLP',fx['id'])
        assert repo.cost('SKU-A','M') == Decimal('116.613')
        with pytest.raises(PricingError,match='missing_fx_authority'):
            PricingRepository(org,date(2026,9,11),'CLP',fx['id']).cost('SKU-A','M')
        with pytest.raises(PricingError,match='fx_snapshot_immutable'):
            admin_write('fx',org,{'observed_rate':Decimal('901')},'Attempt change',fx['id'])


def test_role_and_cross_tenant_cost_confidentiality(commercial_rows):
    org,other,users = commercial_rows
    with as_user(users['OWNER']):
        make_list(org,date(2026,9,1),'7')
        with pytest.raises(DatabaseError), transaction.atomic():
            make_list(other,date(2026,9,1),'8')
    for role in ('ESTIMATOR','INSTALLER'):
        with as_user(users[role]):
            assert rows('SELECT * FROM public.cost_list_items') == []
            assert rows('SELECT * FROM public.price_audit_logs') == []
            assert rows('SELECT * FROM public.pricing_operations') == []
            with pytest.raises(DatabaseError), transaction.atomic():
                rows('SELECT total_cost_net FROM public.projects')
            with pytest.raises(DatabaseError), transaction.atomic():
                rows('SELECT cost_net FROM public.project_positions')
    with as_user(users['WORKSHOP_MANAGER']):
        assert len(rows('SELECT * FROM public.cost_list_items')) == 1
        assert rows("UPDATE public.cost_list_items SET unit_cost=99 RETURNING id") == []
    with as_user(users['ESTIMATOR']), commercial_backend():
        assert PricingRepository(org,date(2026,9,10),'CLP').cost('SKU-A','M') == Decimal('7')
        with pytest.raises(PricingError,match='cost_list_not_found'):
            PricingRepository(other,date(2026,9,10),'CLP').cost('SKU-A','M')


def test_audit_precedes_mutation_and_failure_rolls_back(commercial_rows):
    org,_,users = commercial_rows
    # An AFTER-row assertion checks evidence already exists when the row becomes visible.
    with connection.cursor() as cursor:
        cursor.execute("""CREATE FUNCTION pg_temp.assert_price_audit() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN IF NOT EXISTS(SELECT 1 FROM public.price_audit_logs WHERE entity_id=NEW.id
            AND new_record->>'unit_cost'=to_jsonb(NEW)->>'unit_cost') THEN
            RAISE EXCEPTION 'audit_was_not_first'; END IF; RETURN NEW; END $$;
          CREATE TRIGGER zz_assert_audit AFTER INSERT OR UPDATE ON public.cost_list_items
          FOR EACH ROW EXECUTE FUNCTION pg_temp.assert_price_audit();""")
    with as_user(users['OWNER']):
        list_id = make_list(org,date(2026,9,1),'1.2345')
        item = rows('SELECT id FROM public.cost_list_items WHERE cost_list_id=%s',[list_id])[0]
        admin_write('cost-items',org,{'unit_cost':Decimal('1.2346')},'Fourth digit',item['id'])
        audit = rows("SELECT old_value,new_value,actor_user_id FROM public.price_audit_logs "
                     "WHERE entity_id=%s AND field='UPDATE'",[item['id']])[0]
        assert (audit['old_value'],audit['new_value']) == (Decimal('1.2345'),Decimal('1.2346'))
        assert audit['actor_user_id']==users['OWNER']
        with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("SELECT set_config('app.pricing_reason','',true)")
            cursor.execute('UPDATE public.cost_list_items SET unit_cost=9 WHERE id=%s',[item['id']])
        assert rows('SELECT unit_cost FROM public.cost_list_items WHERE id=%s',[item['id']])[0]['unit_cost']==Decimal('1.2346')
        with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
            cursor.execute('DELETE FROM public.price_audit_logs WHERE entity_id=%s',[item['id']])


def test_xlsx_preview_apply_and_partial_failure_rollback(commercial_rows):
    org,other,users = commercial_rows
    workbook = workbook_bytes([['EXCEL-1','Exact description','M','1.2345']])
    parsed = parse_xlsx(workbook,MAPPING,'.')
    with as_user(users['OWNER']):
        list_id = make_list(org,date(2026,9,1),'1')
        count = one('SELECT count(*) AS n FROM public.price_audit_logs')['n']
        assert import_rows(org,list_id,parsed,'Preview import',False)==parsed
        assert one('SELECT count(*) AS n FROM public.price_audit_logs')['n']==count
        assert rows("SELECT id FROM public.cost_list_items WHERE sku='EXCEL-1'")==[]
        import_rows(org,list_id,parsed,'Apply exact workbook',True)
        item = one("SELECT * FROM public.cost_list_items WHERE sku='EXCEL-1'")
        assert item['unit_cost']==Decimal('1.2345')
        assert item['description']=='Exact description'
        assert one('SELECT reason FROM public.price_audit_logs WHERE entity_id=%s',[item['id']])['reason']=='Apply exact workbook'
        with pytest.raises(PricingError,match='cost_list_not_found'):
            import_rows(other,list_id,parsed,'Wrong tenant',True)
        failing = [{**parsed[0],'sku':'MUST-ROLLBACK'},parsed[0]]
        count = one('SELECT count(*) AS n FROM public.price_audit_logs')['n']
        with pytest.raises(DatabaseError), transaction.atomic():
            import_rows(org,list_id,failing,'Conflicting import',True)
        assert rows("SELECT id FROM public.cost_list_items WHERE sku='MUST-ROLLBACK'")==[]
        assert one('SELECT count(*) AS n FROM public.price_audit_logs')['n']==count


def test_configuration_requires_base_glass_and_finite_authorities(commercial_rows):
    org,_,users = commercial_rows
    with as_user(users['OWNER']):
        with pytest.raises(DatabaseError), transaction.atomic():
            admin_write('configurations',org,{'context_code':'NO-BASE','typology':'FIXED',
                'pricing_mode':'PRICE_PER_M2_BY_TYPOLOGY','currency':'CLP','rate_per_m2':Decimal('1')},'Invalid base')
        with pytest.raises(DatabaseError), transaction.atomic():
            admin_write('fx',org,{'base_currency':'USD','quote_currency':'CLP',
                'observed_rate':Decimal('NaN'),'observed_date':date(2026,9,10),
                'effective_date':date(2026,9,10),'source':'Invalid fixture'},'Reject nonfinite')


def seed_commercial_project(org, owner):
    system = one("SELECT id FROM public.profile_systems WHERE code='DEMO_60'")['id']
    project = one('INSERT INTO public.projects(org_id,code,name,client_name,created_by) '
                  'VALUES(%s,%s,%s,%s,%s) RETURNING id',[org,str(uuid4()),'Commercial gate','Fixture',owner])['id']
    tree = {'id':'root','type':'BAY','opening_type':'FIXED','glass_spec':'4-12-4 Float Incoloro',
            'glass_thickness_mm':'24.00','glass_article_sku':'GLASS-BASE'}
    one('INSERT INTO public.project_positions(org_id,project_id,position_index,quantity,typology,system_id,'
        'width_mm,height_mm,parametric_tree,bom_snapshot) VALUES(%s,%s,1,1,%s,%s,1000,1000,%s::jsonb,%s::jsonb) RETURNING id',
        [org,project,'FIXED',system,json_text(tree),'{}'])
    with as_user(owner):
        parent = admin_write('cost-lists',org,{'supplier_name':'Gate','currency':'CLP','valid_from':date(2026,9,1)},'Gate setup')
        for sku,unit,cost in [('DEMO-BAR-MARCO','BAR','100'),('DEMO-BAR-JQ-10','BAR','100'),
                              ('DEMO-STEEL-BAR-MARCO','BAR','100'),('GLASS-BASE','M2','100')]:
            admin_write('cost-items',org,{'cost_list_id':parent['id'],'sku':sku,'item_type':'FIXTURE',
                        'unit':unit,'unit_cost':Decimal(cost)},'Gate input')
        admin_write('rules',org,{'pricing_mode':'COST_PLUS_MARGIN','default_margin_pct':Decimal('0.35'),
                    'tax_rate_pct':Decimal('0.19'),'waste_factor_pct':Decimal('0.08'),
                    'labor_rate_per_m2':Decimal('15'),'installation_rate_per_m2':Decimal('12')},'Gate rules')
        for mode in ('PRICE_PER_M2_BY_TYPOLOGY','FIXED_PRICE_MATRIX_DIMENSIONAL','COMMERCIAL_LIST_WITH_DISCOUNTS'):
            values = {'context_code':'DEFAULT','typology':'FIXED','pricing_mode':mode,'currency':'CLP'}
            if mode=='PRICE_PER_M2_BY_TYPOLOGY':
                values.update(rate_per_m2=Decimal('2000'),base_glass_sku='GLASS-BASE')
            if mode=='COMMERCIAL_LIST_WITH_DISCOUNTS':
                values['catalog_price']=Decimal('2000')
            config=admin_write('configurations',org,values,'Gate config')
            if mode=='FIXED_PRICE_MATRIX_DIMENSIONAL':
                admin_write('matrix-cells',org,{'configuration_id':config['id'],'width_mm':1000,
                            'height_mm':1000,'price':Decimal('2000')},'Gate matrix')
    return project


def price_request(project, user, mode='COST_PLUS_MARGIN', discount='0'):
    return {'project_id':project,'pricing_mode':mode,'currency':'CLP','effective_date':date(2026,9,10),
            'context_code':'DEFAULT','discount_pct':Decimal(discount),'target_margin':Decimal('0.35'),
            'segment':'RETAIL','confirmed':False,'reason':'Independent gate preview','_actor_id':user}


def tenant(org,role):
    membership=Membership(organization_id=org,organization_name='Fixture',role=role)
    return TenantContext(active_organization=membership,memberships=(membership,))


@pytest.mark.parametrize('mode',['COST_PLUS_MARGIN','PRICE_PER_M2_BY_TYPOLOGY',
    'FIXED_PRICE_MATRIX_DIMENSIONAL','TARGET_GROSS_MARGIN_PROJECT','COMMERCIAL_LIST_WITH_DISCOUNTS'])
def test_five_modes_resolve_real_bom_and_apply_atomically(commercial_rows,mode):
    org,_,users=commercial_rows
    project=seed_commercial_project(org,users['OWNER'])
    with as_user(users['OWNER']),commercial_backend():
        output=preview(org,tenant(org,'OWNER'),price_request(project,users['OWNER'],mode))
        assert output['state']=='PREVIEW'
        if mode in ('PRICE_PER_M2_BY_TYPOLOGY','FIXED_PRICE_MATRIX_DIMENSIONAL','COMMERCIAL_LIST_WITH_DISCOUNTS'):
            assert output['project_net']==Decimal('2000')
            assert output['project_tax']==Decimal('380')
        else:
            # Independent G1 oracle: (4024+3676+3880)/6000*100 + .8281*100
            # = 275.81 materials; *1.08 + 15+12 = 324.8748; /.65 -> CLP500.
            assert output['project_net']==Decimal('500')
            assert output['project_tax']==Decimal('95')
        applied=apply_operation(org,users['OWNER'],'OWNER',output['id'],'Apply approved gate',False)
        assert applied['state']=='APPLIED'
        persisted=one('SELECT total_price_net FROM public.projects WHERE id=%s',[project])
        assert persisted['total_price_net']==Decimal(str(output['project_net']))
        with pytest.raises(PricingError,match='operation_already_final'):
            apply_operation(org,users['OWNER'],'OWNER',output['id'],'Retry',False)


def test_estimator_pending_owner_approval_and_stale_input(commercial_rows):
    org,_,users=commercial_rows
    project=seed_commercial_project(org,users['OWNER'])
    with as_user(users['ESTIMATOR']),commercial_backend():
        with pytest.raises(PricingError,match='pricing_permission_denied'):
            preview(org,tenant(org,'ESTIMATOR'),price_request(project,users['ESTIMATOR'],'TARGET_GROSS_MARGIN_PROJECT'))
        output=preview(org,tenant(org,'ESTIMATOR'),price_request(project,users['ESTIMATOR'],discount='0.15'))
        assert output['state']=='PENDING'
        with pytest.raises(PricingError,match='owner_approval_required'):
            apply_operation(org,users['ESTIMATOR'],'ESTIMATOR',output['id'],'Try unauthorized',False)
    with as_user(users['OWNER']),commercial_backend():
        assert apply_operation(org,users['OWNER'],'OWNER',output['id'],'Approve exact request',False)['state']=='APPLIED'
        next_output=preview(org,tenant(org,'OWNER'),price_request(project,users['OWNER']))
        rows('UPDATE public.project_positions SET quantity=2 WHERE project_id=%s RETURNING id',[project])
        with pytest.raises(PricingError,match='stale_pricing_operation'):
            apply_operation(org,users['OWNER'],'OWNER',next_output['id'],'Stale',False)


@pytest.mark.parametrize('session_role', ['postgres', 'service_role', 'OWNER', 'ESTIMATOR'])
def test_direct_commercial_insert_guard_all_fields(commercial_rows, session_role):
    """Real roles: zero drafts remain valid; every nonzero commercial field fails."""
    from contextlib import nullcontext
    from psycopg import sql

    org, _, users = commercial_rows
    system = one("SELECT id FROM public.profile_systems WHERE code='DEMO_60'")['id']
    identity = as_user(users[session_role]) if session_role in users else nullcontext()
    with transaction.atomic(), identity:
        with connection.cursor() as cursor:
            if session_role not in users:
                cursor.execute("SELECT set_config('request.jwt.claims','{}',true)")
                cursor.execute("SELECT set_config('request.jwt.claim.sub','',true)")
                cursor.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(session_role)))
                cursor.execute('SELECT auth.uid()')
                assert cursor.fetchone()[0] is None
            project = uuid4()
            cursor.execute('INSERT INTO public.projects(id,org_id,code,name,client_name,created_by) '
                           'VALUES(%s,%s,%s,%s,%s,%s)',
                           [project,org,str(project),'Zero draft','Fixture',users['OWNER']])
            position = uuid4()
            position_values = [position,org,project,1,'FIXED',system,'{}','{}']
            position_insert = ('INSERT INTO public.project_positions(id,org_id,project_id,position_index,'
                               'typology,system_id,parametric_tree,bom_snapshot{extra}) '
                               'VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb{value})')
            # Dimensions are mandatory but their schema defaults are not assumed.
            position_insert = position_insert.replace('bom_snapshot{extra}',
                'bom_snapshot,width_mm,height_mm{extra}').replace('%s::jsonb{value}',
                '%s::jsonb,1000,1000{value}')
            cursor.execute(position_insert.format(extra='',value=''),position_values)
            for field in ('total_cost_net','total_price_net','total_price_tax','total_price_gross'):
                attempted = uuid4()
                with pytest.raises(DatabaseError,match='pricing_service_required') as rejected, transaction.atomic():
                    cursor.execute(sql.SQL('INSERT INTO public.projects(id,org_id,code,name,client_name,created_by,{}) '
                        'VALUES(%s,%s,%s,%s,%s,%s,1)').format(sql.Identifier(field)),
                        [attempted,org,str(attempted),'Forbidden','Fixture',users['OWNER']])
                assert rejected.value.__cause__.sqlstate == '42501'
                cursor.execute('SELECT count(*) FROM public.projects WHERE id=%s',[attempted])
                assert cursor.fetchone()[0] == 0
            for field in ('cost_net','price_net','discount_pct'):
                attempted = uuid4()
                with pytest.raises(DatabaseError,match='pricing_service_required') as rejected, transaction.atomic():
                    cursor.execute(position_insert.format(extra=','+field,value=',0.01'),
                                   [attempted,org,project,2,'FIXED',system,'{}','{}'])
                assert rejected.value.__cause__.sqlstate == '42501'
                cursor.execute('SELECT count(*) FROM public.project_positions WHERE id=%s',[attempted])
                assert cursor.fetchone()[0] == 0
            cursor.execute('SELECT count(*) FROM public.projects WHERE id=%s',[project])
            assert cursor.fetchone()[0] == 1
            cursor.execute('SELECT count(*) FROM public.project_positions WHERE id=%s',[position])
            assert cursor.fetchone()[0] == 1


def test_authorized_apply_audit_before_and_full_rollback(commercial_rows):
    """A second BEFORE trigger witnesses prior evidence; a late failure rolls all back."""
    org, _, users = commercial_rows
    project = seed_commercial_project(org,users['OWNER'])
    with connection.cursor() as cursor:
        cursor.execute("RESET ROLE")
        cursor.execute("""CREATE FUNCTION pg_temp.assert_commercial_before() RETURNS trigger
          LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$ BEGIN
          IF NOT EXISTS(SELECT 1 FROM public.price_audit_logs WHERE entity_id=NEW.id
            AND old_record=to_jsonb(OLD) AND new_record=to_jsonb(NEW)
            AND actor_user_id=auth.uid() AND reason='Apply owner fix gate') THEN
            RAISE EXCEPTION 'commercial_audit_not_before'; END IF;
          RETURN NEW; END $$;
          CREATE TRIGGER zz_assert_commercial_before BEFORE UPDATE ON public.project_positions
            FOR EACH ROW EXECUTE FUNCTION pg_temp.assert_commercial_before();
          CREATE TRIGGER zz_assert_commercial_before BEFORE UPDATE ON public.projects
            FOR EACH ROW EXECUTE FUNCTION pg_temp.assert_commercial_before();
          CREATE FUNCTION pg_temp.reject_commercial_apply() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
            IF NEW.state='APPLIED' THEN RAISE EXCEPTION 'forced_apply_rollback'; END IF;
            RETURN NEW; END $$;
          CREATE TRIGGER zz_reject_apply BEFORE UPDATE ON public.pricing_operations
            FOR EACH ROW EXECUTE FUNCTION pg_temp.reject_commercial_apply();""")
    with as_user(users['OWNER']), commercial_backend():
        operation = preview(org,tenant(org,'OWNER'),price_request(project,users['OWNER']))
    with connection.cursor() as cursor:
        cursor.execute('RESET ROLE')
    before_project = one('SELECT * FROM public.projects WHERE id=%s',[project])
    before_positions = rows('SELECT * FROM public.project_positions WHERE project_id=%s',[project])
    count = one('SELECT count(*) AS n FROM public.price_audit_logs WHERE org_id=%s',[org])['n']
    with pytest.raises(DatabaseError,match='forced_apply_rollback'), transaction.atomic():
        with as_user(users['OWNER']), commercial_backend():
            apply_operation(org,users['OWNER'],'OWNER',operation['id'],'Apply owner fix gate',False)
    assert one('SELECT * FROM public.projects WHERE id=%s',[project]) == before_project
    assert rows('SELECT * FROM public.project_positions WHERE project_id=%s',[project]) == before_positions
    assert one('SELECT state FROM public.pricing_operations WHERE id=%s',[operation['id']])['state']=='PREVIEW'
    assert one('SELECT count(*) AS n FROM public.price_audit_logs WHERE org_id=%s',[org])['n']==count
    with connection.cursor() as cursor:
        cursor.execute('DROP TRIGGER zz_reject_apply ON public.pricing_operations')
    with as_user(users['OWNER']), commercial_backend():
        assert apply_operation(org,users['OWNER'],'OWNER',operation['id'],
                               'Apply owner fix gate',False)['state']=='APPLIED'
    with connection.cursor() as cursor:
        cursor.execute('RESET ROLE')
    assert one('SELECT total_price_net FROM public.projects WHERE id=%s',[project])['total_price_net']==Decimal('500')
    assert one('SELECT count(*) AS n FROM public.price_audit_logs WHERE org_id=%s',[org])['n']==count+3
