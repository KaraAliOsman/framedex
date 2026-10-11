"""Payer-controlled dispatch and encrypted return to the same proposal."""

from decimal import Decimal
import hashlib
import hmac
import secrets
from uuid import uuid4

from django.conf import settings
from django.db import transaction

from authentication.errors import contract_error
from documents.repository import one, rows
from notifications import crypto
from projects.provider_scope import provider_scope
from portal import service


def create(*, token, amount, payer_email, operation_key):
    with transaction.atomic(), service.portal_backend():
        approval = service._approval_for_token(token)
    # Public controllers verify this capability before every trusted scope;
    # callers cannot provide the org, project, actor or agreement identity.
    with provider_scope():
        quote = service.portal_quote(token, track=False)
    if (quote['superseded'] or quote['validity_expired'] or quote['approval_status'] != 'APPROVED'
        or not quote['payment_provider'] or not quote['payment']):
        raise contract_error(409, 'portal_payment_unavailable', 'El pago no está disponible en esta propuesta. Consulte su estado y contacte al fabricante.')
    if amount <= 0 or amount > Decimal(quote['payment']['balance']):
        raise contract_error(422, 'payment_exceeds_balance', 'El monto debe ser positivo y no superar el saldo vigente.')

    def prepare(link):
        # Runs under the locked deal claim, before dispatch to Flow. Never
        # patch a real provider's return URL after it has accepted the charge.
        current = service.portal_quote(token, track=False)
        if (current['approval_status'] != 'APPROVED' or not current['payment_provider']
            or current['superseded'] or current['validity_expired']
            or current['selected_revision'] != link['deal_revision']):
            raise contract_error(409, 'portal_payment_unavailable', 'La propuesta cambió. Consulte nuevamente el enlace antes de pagar.')
        identifier, access = uuid4(), secrets.token_urlsafe(32)
        one('INSERT INTO public.portal_payment_contexts(id,org_id,project_id,approval_id,payment_link_id,access_hash,token_ciphertext) '
            'VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id',
            [identifier, approval['org_id'], approval['project_id'], approval['id'], link['id'],
             hashlib.sha256(access.encode()).hexdigest(),
             crypto.seal({'portal_token': token, 'return_access': access}, org_id=approval['org_id'], mail_id=identifier)])
        origin = settings.BILLING_CALLBACK_ORIGIN.rstrip('/')
        if not origin.startswith(('https://', 'http://')):
            raise contract_error(422, 'payer_return_not_configured', 'El fabricante debe configurar el retorno público del pago antes de habilitarlo.')
        return f"{origin}/api/v1/portal/payments/{identifier}/return/?access={access}&redirect=true"

    from projects.payment_links import create_link
    result = create_link(org_id=approval['org_id'], project_id=approval['project_id'], actor_id=approval['created_by'],
        data={'operation_key': f"portal:{approval['id']}:{operation_key}", 'amount': amount, 'payer_email': payer_email,
              'kind': 'ANTICIPO' if Decimal(quote['payment']['collected']) == 0 else 'PARCIAL',
              'subject': f"{quote['project_code']} · {quote['selected_revision']} · propuesta aceptada",
              'simulated': quote['payment_provider'] == 'SIMULATED'},
        prepare_return=prepare, authorization=provider_scope)
    return {'url': result['link']['url'], 'simulated': result['link']['environment'] == 'simulated'}


def _open(row):
    return crypto.open_message(row['token_ciphertext'], org_id=row['org_id'], mail_id=row['id'])


def _path(context):
    payload = _open(context)
    return f"/cotizacion/{payload['portal_token']}?pago={context['id']}&access={payload['return_access']}"


def pending_path(*, token, approval, revision, balance, provider):
    """Resume only a charge created from this already verified capability."""
    with provider_scope():
        found = rows('SELECT c.*,l.url,l.status,l.environment FROM public.portal_payment_contexts c '
            'JOIN public.project_payment_links l ON l.id=c.payment_link_id AND l.org_id=c.org_id '
            'WHERE c.org_id=%s AND c.project_id=%s AND c.approval_id=%s '
            "AND l.deal_revision=%s AND l.status IN('DISPATCHING','PENDING','UNCERTAIN') "
            'AND l.amount>0 AND l.amount<=%s AND (l.expires_at IS NULL OR l.expires_at>now()) '
            'ORDER BY l.created_at DESC LIMIT 1',
            [approval['org_id'], approval['project_id'], approval['id'], revision, balance])
    if not found:
        return None
    charge = found[0]
    if ((charge['environment'] == 'simulated') != (provider == 'SIMULATED')
        or _open(charge)['portal_token'] != token):
        return None
    return charge['url'] if charge['status'] == 'PENDING' and charge['url'] else _path(charge)


def path_for_link(link):
    with provider_scope():
        found = rows('SELECT * FROM public.portal_payment_contexts WHERE org_id=%s AND payment_link_id=%s',
                     [link['org_id'], link['id']])
    return _path(found[0]) if found else None


def result(*, context_id, access):
    with provider_scope():
        found = rows('SELECT * FROM public.portal_payment_contexts WHERE id=%s', [context_id])
    if (not found or not isinstance(access, str)
        or not hmac.compare_digest(found[0]['access_hash'], hashlib.sha256(access.encode()).hexdigest())):
        raise contract_error(404, 'portal_payment_return_not_found', 'El resultado no está disponible. Consulte el enlace original del fabricante.')
    context = found[0]
    with provider_scope():
        link = one('SELECT * FROM public.project_payment_links WHERE id=%s AND org_id=%s', [context['payment_link_id'], context['org_id']])
        if link['environment'] != 'simulated' and link['status'] in ('DISPATCHING','PENDING','UNCERTAIN'):
            from projects.payment_links import recover_link
            # Provider recovery is a verified GET, never another charge.
            recover_link(org_id=context['org_id'], link_id=link['id'])
            link = one('SELECT * FROM public.project_payment_links WHERE id=%s AND org_id=%s', [link['id'], context['org_id']])
    return {'portal_path': _path(context),
            'status': link['status'], 'simulated': link['environment'] == 'simulated', 'amount': str(link['amount'])}
