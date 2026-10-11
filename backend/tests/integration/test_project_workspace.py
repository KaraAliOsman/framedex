"""P21: presentation changes preserve tenant, physical and sealed authority."""
from uuid import UUID, uuid4
from copy import deepcopy

from django.db import DatabaseError, transaction, connection
import pytest

from backend.tests.integration.test_project_operations import setup_project, apply
from backend.tests.integration.test_shot09_documentary import documentary_tenant as documentary_tenant, as_user
from backend.tests.integration.test_opening_mounting import client_for, mounting_position
from authentication.errors import ContractAPIException
from dekopen_engine.design_operations import OperationError
from pricing.repository import commercial_backend
from projects import service
from projects.mounting import measurement_public
from projects.ops_registry import product_from_position
from projects.project_ops import preview_project_operations, signature, snapshot, undo_project_operations

pytestmark = pytest.mark.rls_integration


def test_metadata_and_reorder_preserve_bom_number_and_measurements(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users['OWNER']
    project, position, _, _ = mounting_position(org, actor)
    with as_user(actor):
        original = service.position_row(org, position['id'])
        _, duplicate = apply(org, actor, project['id'], [{'op': 'duplicate_positions', 'position_ids': [str(position['id'])]}])
        all_positions = duplicate['project']['positions']
        assert all_positions[1]['measurements'] is None
        ids = [str(item['id']) for item in all_positions]
        _, updated = apply(org, actor, project['id'], [{'op': 'set_positions', 'position_ids': ids,
            'placement': {'floor': 'Piso 2', 'room': 'Dormitorios'}, 'location': 'Norte', 'quantity': 3}])
        saved = service.position_row(org, position['id'])
        assert saved['bom_snapshot'] == original['bom_snapshot']
        assert saved['position_index'] == original['position_index']
        assert updated['project']['positions'][0]['measurements']['current']
        before = deepcopy(updated['project']['positions'])
        _, reordered = apply(org, actor, project['id'], [{'op': 'reorder_positions', 'position_ids': ids[::-1]}])
        assert [str(item['id']) for item in reordered['project']['positions']] == ids[::-1]
        assert {str(item['id']): item['position_index'] for item in reordered['project']['positions']} == {str(item['id']): item['position_index'] for item in before}
        restored = undo_project_operations(org, actor, project['id'], UUID(reordered['operation_id']))
        assert [str(item['id']) for item in restored['project']['positions']] == ids
        assert restored['project']['positions'][0]['placement'] == {'floor': 'Piso 2', 'room': 'Dormitorios'}
        removed = apply(org, actor, project['id'], [{'op': 'remove_positions', 'position_ids': ids}])[1]
        assert service.positions(org, project['id']) == []
        restored = undo_project_operations(org, actor, project['id'], UUID(removed['operation_id']))
        assert restored['project']['positions'][0]['measurements']['current']
        assert [str(item['id']) for item in restored['project']['positions']] == ids


def test_library_uses_full_shared_recipe_and_engine_gate(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users['OWNER']
    project, position = setup_project(org, actor)
    with as_user(actor):
        product = product_from_position(service.position_row(org, position['id']))
        glass = position['bom']['glasses'][0]['article_sku']
        op = {'op': 'add_design_position', 'system_id': str(position['design']['system_id']),
            'product': product, 'glass_sku': glass, 'color': position['design']['color'],
            'location': 'Biblioteca · comedor', 'quantity': 1}
        before = signature(snapshot(org, project['id']))
        proposal = preview_project_operations(org, actor, project['id'], [op])
        assert proposal['simulations'][0]['valid']
        assert signature(snapshot(org, project['id'])) == before
        _, result = apply(org, actor, project['id'], [op])
        created = result['project']['positions'][-1]
        assert created['location_tag'] == op['location']
        assert created['bom']['calculation_hash']
        assert created['design']['nominal_width_mm'] == position['design']['nominal_width_mm']
        with pytest.raises(OperationError, match='receta'):
            preview_project_operations(org, actor, project['id'], [{**op, 'product': {'version': 'product-v2'}}])


@pytest.mark.parametrize('op', ['remove_positions', 'duplicate_positions', 'set_positions', 'reorder_positions'])
def test_batch_refuses_duplicate_or_foreign_targets(documentary_tenant, op):
    org, _, users, _ = documentary_tenant
    actor = users['OWNER']
    project, position = setup_project(org, actor)
    with as_user(actor):
        for targets, expected in [([str(position['id'])] * 2, 'batch_duplicate_targets'), ([str(uuid4())], 'position_not_found')]:
            with pytest.raises(OperationError) as error:
                preview_project_operations(org, actor, project['id'], [{'op': op, 'position_ids': targets, **({'quantity': 2} if op == 'set_positions' else {})}])
            assert error.value.code == expected


def test_bulk_evidence_matches_scalar_and_read_projection_keeps_old_signatures(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users['OWNER']
    project, position, _, _ = mounting_position(org, actor)
    with as_user(actor):
        public = service.positions(org, project['id'])[0]
        assert public['measurements'] == measurement_public(org, position['id'], public['design'], 'REV-A')
        present = snapshot(org, project['id'])
        historical = deepcopy(present)
        for item in historical['positions']:
            for field in ('display_order', 'placement', 'system_name', 'system_demo', 'commercial'):
                item.pop(field, None)
        assert signature(present) == signature(historical)


def test_sealed_project_refuses_workspace_metadata_even_for_elevated_sql(documentary_tenant):
    from backend.tests.integration.test_shot09_documentary import _seed_project
    org, _, users, _ = documentary_tenant
    actor = users['OWNER']
    project_id, position_id, _ = _seed_project(org, actor, apply_pricing=True)
    with as_user(actor):
        with pytest.raises(ContractAPIException):
            preview_project_operations(org, actor, project_id, [{'op': 'set_positions', 'position_ids': [str(position_id)], 'placement': {'floor': 'Piso 9'}}])
    with pytest.raises(DatabaseError, match='project_workspace_revision_required'), transaction.atomic(), as_user(actor), commercial_backend(), connection.cursor() as cursor:
        cursor.execute("UPDATE public.project_positions SET placement=%s::jsonb WHERE id=%s", ['{"floor":"Piso 9"}', position_id])


def test_workspace_api_cannot_cross_tenant_or_bypass_role(documentary_tenant):
    org, other_org, users, _ = documentary_tenant
    project, position = setup_project(org, users['OWNER'])
    data = {'ops': [{'op': 'set_positions', 'position_ids': [str(position['id'])], 'quantity': 2}]}
    path = f"/api/v1/projects/{project['id']}/operations/preview/"
    assert client_for(users['INSTALLER']).post(path, data, format='json', HTTP_X_ORGANIZATION_ID=str(org)).status_code == 403
    assert client_for(users['OWNER']).post(path, data, format='json', HTTP_X_ORGANIZATION_ID=str(other_org)).status_code == 403
