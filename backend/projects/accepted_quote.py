"""Read a chosen sealed solution; restore it only into an explicit new draft."""

from decimal import Decimal
from django.db import transaction

from dekopen_engine.quotation import quotation_line
from documents.repository import decoded, documentary_backend
from pricing.repository import json_text, rows


def selected_projects(org_id, project_ids):
    if not project_ids:
        return {}
    with documentary_backend():
        found = rows("SELECT p.id AS project_id,offered.id AS offering_id,offered.revision_code AS offering_revision,"
            "v.id AS version_id,v.revision_code,v.emitted_at,v.snapshot_json::text AS snapshot_json "
            "FROM public.projects p JOIN public.project_versions offered ON offered.project_id=p.id AND offered.org_id=p.org_id "
            "AND offered.revision_code=p.current_revision "
            "JOIN LATERAL private.quotation_choice(p.org_id,offered.id) c ON c.kind='APPROVED' "
            "JOIN public.project_versions v ON v.id=c.selected_version_id AND v.org_id=p.org_id "
            "WHERE p.org_id=%s AND p.id=ANY(%s) AND v.id<>offered.id AND p.status<>'DRAFT'", [org_id, project_ids])
    return {str(item['project_id']): item for item in found}


def public_solution(value, chosen, *, detail):
    from projects.service import position_public
    snapshot = decoded(chosen['snapshot_json'])
    project = snapshot['project']
    value['accepted_version_id'] = str(chosen['version_id'])
    value['accepted_revision'] = chosen['revision_code']
    value['accepted_source'] = 'Opción emitida aceptada en el ofrecimiento de revisión ' + chosen['offering_revision'].removeprefix('REV-')
    for key in ('total_price_net', 'total_price_tax', 'total_price_gross'):
        value[key] = str(project[key])
    value['currency'] = project['currency']
    value['position_count'] = len(snapshot['positions'])
    if not detail:
        return value
    value['quotation_validity_source'] = 'Vigencia del ofrecimiento de revisión ' + chosen['offering_revision'].removeprefix('REV-') + '; solución aceptada de revisión ' + chosen['revision_code'].removeprefix('REV-')
    bom = {str(item['position_id']): item['engine_result'] for item in snapshot['bom']}
    positions = []
    for source in snapshot['positions']:
        row = {**source, 'project_id': value['id'], 'updated_at': chosen['emitted_at'],
               'bom_snapshot': bom[str(source['id'])]}
        item = position_public(row)
        line = quotation_line(quantity=source['quantity'], net=Decimal(str(source['price_net'])), currency=value['currency'])
        item.update(system_name=source.get('system_name') or 'Serie de la cotización · nombre por completar', system_demo=bool(source.get('is_demo')),
            measurements=source.get('measurements'), commercial={'unit_net': str(line.unit_net),
            'line_net': str(line.net), 'source': value['accepted_source']})
        positions.append(item)
    value['positions'] = positions
    return value


def restore_draft(org_id, project_id, chosen, successor):
    """The caller proved the live offer is unchanged and opened successor.

    Copy geometry and preserved motor output, never accepted prices or a site
    confirmation. Documentary preparation must be reviewed for the new draft.
    """
    snapshot = decoded(chosen['snapshot_json'])
    sources = snapshot['positions']
    ids = [source['id'] for source in sources]
    bom = {str(item['position_id']): item['engine_result'] for item in snapshot['bom']}
    with transaction.atomic():
        rows('DELETE FROM public.project_positions WHERE org_id=%s AND project_id=%s AND NOT(id=ANY(%s)) RETURNING id',
             [org_id, project_id, ids])
        # Reserve an unused ordinal range during reordering; physical numbers
        # are then copied exactly from the chosen solution, inside this tx.
        rows('UPDATE public.project_positions SET position_index=position_index+(SELECT COALESCE(MAX(position_index),0)+1 '
             'FROM public.project_positions WHERE org_id=%s AND project_id=%s) WHERE org_id=%s AND project_id=%s RETURNING id',
             [org_id, project_id, org_id, project_id])
        for source in sources:
            rows('INSERT INTO public.project_positions(id,org_id,project_id,position_index,location_tag,quantity,typology,system_id,'
                 'width_mm,height_mm,color_interior,color_exterior,parametric_tree,bom_snapshot,display_order) '
                 'VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s) '
                 'ON CONFLICT(id) DO UPDATE SET position_index=EXCLUDED.position_index,location_tag=EXCLUDED.location_tag,'
                 'quantity=EXCLUDED.quantity,typology=EXCLUDED.typology,system_id=EXCLUDED.system_id,width_mm=EXCLUDED.width_mm,'
                 'height_mm=EXCLUDED.height_mm,color_interior=EXCLUDED.color_interior,color_exterior=EXCLUDED.color_exterior,'
                 'parametric_tree=EXCLUDED.parametric_tree,bom_snapshot=EXCLUDED.bom_snapshot,display_order=EXCLUDED.display_order,'
                 'updated_at=clock_timestamp() WHERE project_positions.org_id=EXCLUDED.org_id AND project_positions.project_id=EXCLUDED.project_id RETURNING id',
                 [source['id'], org_id, project_id, source['position_index'], source['location_tag'], source['quantity'],
                  source['typology'], source['system_id'], source['width_mm'], source['height_mm'], source['color_interior'],
                  source['color_exterior'], json_text(source['parametric_tree']), json_text(bom[str(source['id'])]), source['position_index']])
        fields = ('name','client_name','client_rut','client_email','client_phone','client_giro','client_comuna','client_address','delivery_address','notes_commercial')
        rows('UPDATE public.projects SET ' + ','.join(key+'=%s' for key in fields) + ' WHERE org_id=%s AND id=%s RETURNING id',
             [*(snapshot['project'].get(key) or '' for key in fields), org_id, project_id])
    with documentary_backend():
        rows('UPDATE public.project_documentary_inputs SET payment_terms=%s,commercial_terms=%s::jsonb WHERE org_id=%s AND project_id=%s RETURNING project_id',
             [snapshot['project'].get('payment_terms') or '', json_text(snapshot['project'].get('commercial_terms') or {}), org_id, project_id])
