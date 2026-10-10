"""Read-only requirements over released OT; physical choices belong to the engine."""
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from django.db import transaction

from dekopen_engine.documentary_canonical import documentary_sha256_v1
from dekopen_engine.inventory import purchase_source_ledger, stock_shortfall
from dekopen_engine.models import EngineResult
from documents.repository import DocumentaryError, decoded, documentary_backend, json_text, one, rows
from inventory.production_stock import bar_stock_needs
from inventory.service import list_stock, stock_variant_key

ZERO = Decimal(0)
STATIONS = {'PROFILE': 'CUT', 'REINFORCEMENT': 'CUT', 'GLASS': 'GLAZE',
            'PANEL': 'GLAZE', 'HARDWARE_KIT': 'ASSEMBLE', 'FITTING': 'ASSEMBLE', 'ACCESSORY': 'ASSEMBLE'}


def proposal(*, org_id: UUID) -> dict:
    from engine_api.cutting_repository import CuttingRepository
    from production.service import _compute_optimization, _sheet_rules
    from purchasing.service import _requirements

    with documentary_backend():
        orders = rows(
            "SELECT o.id,o.order_code,o.project_id,o.project_version_id,o.payload_json,p.code AS project_code, "
            "v.revision_code FROM public.orders o "
            "JOIN public.projects p ON p.id=o.project_id AND p.org_id=o.org_id "
            "JOIN public.project_versions v ON v.id=o.project_version_id AND v.org_id=o.org_id "
            "WHERE o.org_id=%s AND o.order_type='WORKSHOP_OT' "
            "AND o.status NOT IN ('COMPLETED','DISPATCHED','INSTALLED','CANCELLED') ORDER BY o.created_at,o.id",
            [str(org_id)])
        snapshots = {str(v['id']): decoded(v['snapshot_json']) for v in rows(
            "SELECT id,snapshot_json FROM project_versions WHERE org_id=%s AND id=ANY(%s::uuid[])",
            [str(org_id), sorted({str(o['project_version_id']) for o in orders})])} if orders else {}
        done = {(str(s['order_id']), s['code']) for s in rows(
            "SELECT order_id,code FROM public.production_steps WHERE org_id=%s AND status='DONE'", [str(org_id)])}
        stock = list_stock(org_id=org_id)['items']
        pools = {(s['sku'], s['variant_key']): max(Decimal(str(s['available_qty'])), ZERO) for s in stock}
        transit = {(s['sku'], s['variant_key']): Decimal(str(s['incoming_qty'])) for s in stock}
        held = rows(
            "SELECT m.order_id,i.sku,i.variant_key,SUM(CASE WHEN m.movement_type='RESERVATION' THEN m.quantity "
            "WHEN m.movement_type IN ('RELEASE','CONSUMPTION') THEN -m.quantity ELSE 0 END) AS quantity "
            "FROM public.inventory_movements m JOIN public.inventory_items i ON i.id=m.item_id AND i.org_id=m.org_id "
            "WHERE m.org_id=%s GROUP BY m.order_id,i.sku,i.variant_key", [str(org_id)])
        reservations = {(str(h['order_id']), h['sku'], h['variant_key']): max(Decimal(str(h['quantity'])), ZERO) for h in held}
        grouped = defaultdict(list)
        offers, blockers = [], []
        used = set()
        repository, rules = CuttingRepository(request_cache=True), _sheet_rules(org_id)
        bar_needs = defaultdict(lambda: ZERO)
        for order in orders:
            oid = str(order['id'])
            grouped[str(order['project_version_id'])].append(order)
            payload = decoded(order['payload_json'])
            order['position_id'] = str(payload.get('position_id') or '')
            if (oid, 'CUT') in done:
                continue
            materials = payload.get('materials') or {}
            plan = payload.get('optimization')
            try:
                if plan and plan.get('invalidated'):
                    raise DocumentaryError('work_order_plan_invalidated')
                if not plan:
                    result = EngineResult.model_validate({**{key: materials.get(key) or [] for key in (
                        'profile_cuts', 'reinforcements', 'glasses', 'panels', 'fittings', 'hardware_items', 'leaf_weights')},
                        'finish': materials.get('finish')}, strict=False)
                    plan = _compute_optimization(org_id=org_id, result=result, system_id=str(payload['system_id']),
                        color=str(payload.get('color') or ''), quantity=int(payload.get('quantity') or 1),
                        position_id=order['position_id'], version_snapshot=snapshots[str(order['project_version_id'])],
                        strategy='fast', excluded_remnant_ids=used, stock_repository=repository, sheet_rules=rules)
                consumed = (plan.get('remnants') or {}).get('consumed') or [*plan.get('consumed_bars', []), *plan.get('consumed_sheets', [])]
                for remnant in consumed:
                    used.add(str(remnant['id']))
                    offers.append({'remnant_id': str(remnant['id']), 'order_id': oid,
                                   'order_code': order['order_code'], 'reserved': bool(payload.get('optimization'))})
                for need in bar_stock_needs(org_id=org_id, bars=(plan.get('bars') or {}).get('workshop_cut_plan') or []):
                    bar_needs[(oid, need['sku'], need['variant_key'])] += Decimal(str(need['needed']))
            except (DocumentaryError, ValueError, KeyError) as error:
                blockers.append({'order_id': oid, 'order_code': order['order_code'],
                                 'cause': 'Falta un plan vigente con autoridad de corte. Abre la OT y revisa su catálogo.',
                                 'code': getattr(error, 'code', 'purchase_plan_incomplete')})
        lines = []
        for version_id, version_orders in grouped.items():
            snapshot = snapshots[version_id]
            sources = purchase_source_ledger(snapshot)
            requirements = _requirements(UUID(version_id), org_id)
            claims = rows(
                "SELECT l.requirement_line_id,SUM(l.quantity-l.released_qty) AS qty, "
                "SUM(CASE WHEN o.status='DRAFT' THEN l.quantity-l.released_qty ELSE 0 END) AS draft "
                "FROM public.order_requirement_lines l JOIN public.orders o ON o.id=l.order_id AND o.org_id=l.org_id "
                "WHERE l.org_id=%s AND l.project_version_id=%s GROUP BY l.requirement_line_id", [str(org_id), version_id])
            committed = {str(r['requirement_line_id']): Decimal(str(r['qty'])) for r in claims}
            drafts = {str(r['requirement_line_id']): Decimal(str(r['draft'])) for r in claims}
            allocated = {str(a['requirement_line_id']): a for a in rows(
                "SELECT a.requirement_line_id,e.id AS eligibility_id,e.supplier_name,e.evidence "
                "FROM public.purchase_allocations a JOIN public.supplier_eligibility_versions e "
                "ON e.id=a.supplier_eligibility_id AND e.org_id=a.org_id WHERE a.org_id=%s AND a.project_version_id=%s",
                [str(org_id), version_id])}
            for req in requirements:
                rid = str(req['id'])
                spec = decoded(req['specification'])
                key = (str(req['purchasing_sku']), stock_variant_key(req.get('physical_stock_identity'), spec, req['category']))
                trace = decoded(req['source_trace'])
                missing = [source for source in trace if source not in sources]
                positions = {sources[source][0] for source in trace if source in sources}
                relevant = [o for o in version_orders if o['position_id'] in positions and
                            (str(o['id']), STATIONS[req['category']]) not in done]
                required = ZERO
                origins = []
                for order in relevant:
                    oid = str(order['id'])
                    if req['unit'] == 'BAR':
                        quantity = bar_needs[(oid, *key)]
                        bar_needs[(oid, *key)] = ZERO
                    else:
                        quantity = sum((sources[s][1] for s in trace if s in sources and
                                        sources[s][0] == order['position_id']), ZERO)
                    if quantity > ZERO:
                        origins.append({'id': oid, 'code': order['order_code'], 'quantity': str(quantity)})
                        required += quantity
                if required == ZERO and not missing:
                    continue
                own_keys = [(str(o['id']), *key) for o in relevant]
                own = sum((reservations.get(k, ZERO) for k in own_keys), ZERO)
                result = stock_shortfall(required=required, own_reserved=own,
                                         available=pools.get(key, ZERO), incoming=transit.get(key, ZERO))
                # Each physical pool is consumed once even across requirements.
                remaining = result['reserved']
                for held_key in own_keys:
                    taken = min(remaining, reservations.get(held_key, ZERO))
                    reservations[held_key] = reservations.get(held_key, ZERO) - taken
                    remaining -= taken
                pools[key] = pools.get(key, ZERO) - result['stock']
                transit[key] = transit.get(key, ZERO) - result['incoming']
                maximum = max(Decimal(str(req['quantity'])) - committed.get(rid, ZERO), ZERO)
                draft = min(result['purchase'], drafts.get(rid, ZERO))
                short = result['purchase'] - draft
                purchase, uncovered = min(short, maximum), max(short - maximum, ZERO)
                assignment = allocated.get(rid)
                until = decoded(assignment['evidence']).get('valid_until') if assignment else None
                if until and str(until) < datetime.now(ZoneInfo('America/Santiago')).date().isoformat():
                    assignment = None
                cause = ('Sin dato · hay fuentes históricas sin vínculo a una posición. Revisa la revisión.' if missing else
                         'El plan de OT requiere más material que la compra sellada. Revisa la consolidación o emite una revisión adicional.'
                         if uncovered > ZERO else None)
                lines.append({'requirement_id': rid, 'version_id': version_id,
                    'project_code': version_orders[0]['project_code'], 'project_id': str(version_orders[0]['project_id']),
                    'revision_code': version_orders[0]['revision_code'], 'order_type': req['order_type'],
                    'is_demo': bool(snapshot.get('is_demo')),
                    'sku': key[0], 'unit': req['unit'], 'specification': spec, 'required': str(required),
                    'reserved': str(result['reserved']), 'stock': str(result['stock']), 'incoming': str(result['incoming']),
                    'draft': str(draft), 'purchase': str(ZERO if missing else purchase), 'uncovered': str(uncovered),
                    'maximum': str(maximum), 'cause': cause,
                    'supplier_eligibility_id': str(assignment['eligibility_id']) if assignment else None,
                    'supplier_name': assignment['supplier_name'] if assignment else None, 'orders': origins})
        result = {'lines': lines, 'remnant_offers': offers, 'blockers': blockers}
        return {**result, 'preview_hash': documentary_sha256_v1(result)}


def confirm_proposal(*, org_id: UUID, actor_id: UUID, data: dict) -> dict:
    from production.service import optimize_work_order
    from purchasing.service import confirm_order_type_batch
    if not data['confirmed']:
        raise DocumentaryError('order_batch_confirmation_required')
    request_hash = documentary_sha256_v1(data)
    with transaction.atomic(), documentary_backend():
        rows("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", [f'purchase-needs:{org_id}'])
        prior = rows("SELECT request_hash,result FROM public.purchase_need_decisions WHERE org_id=%s AND operation_key=%s",
                     [str(org_id), data['operation_key']])
        if prior:
            if prior[0]['request_hash'] != request_hash:
                raise DocumentaryError('purchase_operation_conflict', detail='Esta decisión ya se usó con otro contenido. Revisa las órdenes creadas.')
            return decoded(prior[0]['result'])
        preview = proposal(org_id=org_id)
        if preview['preview_hash'] != data['preview_hash']:
            raise DocumentaryError('purchase_preview_stale', detail='El stock o las OT cambiaron. Actualiza las necesidades antes de confirmar.')
        by_id = {line['requirement_id']: line for line in preview['lines']}
        groups, prices = defaultdict(dict), {}
        selected_orders = set()
        for choice in data['lines']:
            rid = str(choice['requirement_id'])
            if rid in prices or rid not in by_id:
                raise DocumentaryError('purchase_choice_invalid', detail='Elige cada necesidad una sola vez desde la propuesta actual.')
            line = by_id[rid]
            if not line['supplier_eligibility_id'] or line['cause'] or choice['quantity'] > Decimal(line['maximum']):
                raise DocumentaryError('purchase_choice_invalid', detail='Revisa el proveedor, el plan y la cantidad antes de crear la OC.')
            groups[(line['version_id'], line['order_type'])][rid] = choice['quantity']
            prices[rid] = choice.get('unit_price')
            selected_orders.update(o['id'] for o in line['orders'])
        # Secure drops relied on by this human purchase decision atomically.
        remnant_groups = defaultdict(set)
        for offer in preview['remnant_offers']:
            if not offer['reserved'] and offer['order_id'] in selected_orders:
                remnant_groups[offer['order_id']].add(offer['remnant_id'])
        for oid, expected in remnant_groups.items():
            optimize_work_order(org_id=org_id, order_id=UUID(oid), actor_id=actor_id, color='', strategy='fast')
            held = {str(r['id']) for r in rows("SELECT id FROM inventory_remnants WHERE org_id=%s AND reserved_order_id=%s AND status='RESERVED'",
                                             [str(org_id), oid])}
            if not expected.issubset(held):
                raise DocumentaryError('purchase_preview_stale', detail='Cambió la elección de retazos. Actualiza la propuesta antes de comprar.')
        orders = []
        for (version, kind), quantities in sorted(groups.items()):
            output, _ = confirm_order_type_batch(org_id=org_id, actor_id=actor_id, version_id=UUID(version),
                order_type=kind, confirmed=True, quantities=quantities, unit_prices=prices)
            orders.extend(output)
        result = {'orders': orders}
        one("INSERT INTO public.purchase_need_decisions(org_id,operation_key,request_hash,result,actor_id) VALUES(%s,%s,%s,%s::jsonb,%s) RETURNING id",
            [str(org_id), data['operation_key'], request_hash, json_text(result), str(actor_id)])
        return result
