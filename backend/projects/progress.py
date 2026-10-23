"""Read-only stages from the current offer, its chosen solution and real work.

No stage writes lifecycle state. Money is projected by the pure engine; an
old revision, a cancelled order or a simulated receipt cannot close a work.
"""

from collections import defaultdict
from decimal import Decimal

from dekopen_engine.work_queue import money_sum, outstanding
from documents.repository import documentary_backend, rows

STAGES = ("QUOTING", "SENT", "ACCEPTED", "WORKSHOP", "INSTALLED", "TO_COLLECT", "CLOSED", "CANCELLED")


def stage_from_facts(status, *, shared=False, accepted=False, orders=(), balance=None):
    if status == "CANCELLED":
        return "CANCELLED", "Obra cancelada."
    if status == "DRAFT":
        return "QUOTING", "Revisión en preparación."
    if orders:
        if all(value == "INSTALLED" for value in orders):
            if balance is None:
                return "INSTALLED", "Instalación registrada; falta comprobar el total de la venta."
            if balance > 0:
                return "TO_COLLECT", "Instalación registrada con saldo real pendiente."
            return "CLOSED", "Instalación completa y venta cubierta por pagos reales vigentes."
        return "WORKSHOP", "Hay órdenes de la solución vigente pendientes de instalación."
    if accepted or status in {"APPROVED", "IN_PRODUCTION", "COMPLETED"}:
        return "ACCEPTED", "Aceptación registrada; falta una instalación completa de la solución vigente."
    if shared:
        return "SENT", "Cotización compartida mediante un enlace para el cliente o correo entregado."
    return "QUOTING", "La revisión todavía no tiene un enlace compartido ni un envío confirmado."


def project_progress(org_id, project_ids):
    """Three bounded queries for the whole list; preserve caller claims/RLS."""
    if not project_ids:
        return {}
    with documentary_backend():
        facts = rows(
            """
            SELECT p.id,p.status::text,offered.id AS offering_id,
                   chosen.id AS version_id,c.kind AS decision,
                   chosen.snapshot_json#>>'{project,total_price_gross}' AS total,
                   chosen.snapshot_json#>>'{project,currency}' AS currency,
                   ARRAY(SELECT pos->>'id' FROM jsonb_array_elements(
                     COALESCE(chosen.snapshot_json->'positions','[]'::jsonb)) pos) AS positions,
                   EXISTS(SELECT 1 FROM public.customer_approvals a
                     WHERE a.org_id=p.org_id AND a.project_id=p.id
                       AND a.project_version_id=offered.id AND a.status<>'REVOKED'
                       AND (a.link_source='SHARE' OR a.view_count>0))
                   OR EXISTS(SELECT 1 FROM public.quotation_issues i
                     JOIN public.mail_outbox m ON m.id=i.mail_id AND m.org_id=i.org_id
                     WHERE i.org_id=p.org_id AND i.project_id=p.id
                       AND i.project_version_id=offered.id AND m.state='SENT') AS shared
            FROM public.projects p
            LEFT JOIN public.project_versions offered ON offered.org_id=p.org_id
              AND offered.project_id=p.id AND offered.revision_code=p.current_revision
            LEFT JOIN LATERAL private.quotation_choice(p.org_id,offered.id) c ON true
            LEFT JOIN public.project_versions chosen ON chosen.org_id=p.org_id
              AND chosen.id=CASE WHEN c.kind='APPROVED' THEN c.selected_version_id ELSE offered.id END
            WHERE p.org_id=%s AND p.id=ANY(%s)
            """, [org_id, project_ids],
        )
        orders = rows(
            """
            SELECT o.project_id,o.project_version_id,o.status::text,
                   o.payload_json->>'position_id' AS position_id
            FROM public.orders o
            WHERE o.org_id=%s AND o.project_id=ANY(%s)
              AND o.order_type='WORKSHOP_OT' AND o.status<>'CANCELLED'
              AND NOT EXISTS(SELECT 1 FROM public.orders r WHERE r.org_id=o.org_id
                AND r.status<>'CANCELLED' AND r.payload_json->>'remake_of'=o.id::text)
            """, [org_id, project_ids],
        )
        payments = rows(
            "SELECT project_id,amount FROM public.project_payments WHERE org_id=%s "
            "AND project_id=ANY(%s) AND voided_at IS NULL AND NOT simulated",
            [org_id, project_ids],
        )
    work, paid, covered = defaultdict(list), defaultdict(list), defaultdict(set)
    for order in orders:
        key = (order['project_id'], order['project_version_id'])
        work[key].append(order['status'])
        covered[key].add(order['position_id'])
    for payment in payments:
        paid[payment['project_id']].append(payment['amount'])
    result = {}
    for fact in facts:
        # A successor draft does not inherit an old quote's money or progress.
        total = fact['total'] if fact['status'] != 'DRAFT' else None
        currency = fact['currency'] if total is not None else None
        balance = (outstanding(Decimal(total), money_sum(paid[fact['id']]))
                   if total is not None and currency else None)
        key = (fact['id'], fact['version_id'])
        statuses = work[key]
        if statuses and (not fact['positions'] or set(fact['positions']) - covered[key]):
            statuses = [*statuses, 'MISSING']
        stage, reason = stage_from_facts(fact['status'], shared=fact['shared'],
            accepted=fact['decision'] == 'APPROVED',
            orders=statuses, balance=balance)
        result[str(fact['id'])] = {'stage': stage, 'reason': reason,
            'quoted_total': total, 'currency': currency}
    return result
