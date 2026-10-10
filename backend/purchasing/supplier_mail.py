"""Explicit supplier mail, sealed PDF and the shared SMTP/Mailpit adapter."""
from uuid import UUID

from django.db import transaction

from dekopen_engine.documentary_canonical import documentary_sha256_v1
from documents.repository import DocumentaryError, decoded, documentary_backend, one
from documents.artifacts import generate_artifact
from notifications import service as mail, templates

DOCUMENTS={'SUPPLIER_PROFILE_PO':'DOC-04','SUPPLIER_GLASS_PO':'DOC-02',
           'SUPPLIER_HARDWARE_PO':'DOC-08','SUPPLIER_PANEL_PO':'DOC-08'}


def source(*,org_id:UUID,order_id:UUID) -> dict:
    with documentary_backend():
        order=one("SELECT id,project_id,project_version_id,order_type,status,payload_json,order_snapshot_hash, "
                  "private.entity_code(org_id,'OC',id,order_code) AS order_code "
                  "FROM public.orders WHERE id=%s AND org_id=%s",[str(order_id),str(org_id)],'order_not_found')
        snapshot=decoded(order['payload_json'])
        if order['order_type'] not in DOCUMENTS or documentary_sha256_v1(snapshot)!=order['order_snapshot_hash']:
            raise DocumentaryError('invalid_order_snapshot')
        if order['status'] in ('DRAFT','CANCELLED'):
            raise DocumentaryError('order_not_sent',detail="Registra el envío humano de esta OC antes de enviar su correo al proveedor.")
        recipient=(snapshot['order'].get('supplier_details') or {}).get('email') or ''
        body=f"Adjuntamos la orden de compra {order['order_code']} para su revisión.\nConfirme la disponibilidad y fecha de entrega."
        return {'order':order,'organization':snapshot.get('organization') or {},'recipient':recipient,'body':body,
                'document_type':DOCUMENTS[order['order_type']]}


def preview(*,org_id:UUID,order_id:UUID) -> dict:
    value=source(org_id=org_id,order_id=order_id)
    message=templates.render('PURCHASE',organization=value['organization'],reference=value['order']['order_code'],body=value['body'])
    return {'recipient':value['recipient'],'subject':message['subject'],'text':message['text'],
            'document_type':value['document_type']}


def send(*,org_id:UUID,order_id:UUID,actor_id:UUID,role:str,confirmed:bool,expected_recipient:str) -> dict:
    if not confirmed:
        raise DocumentaryError('order_send_confirmation_required')
    with transaction.atomic(),documentary_backend():
        one("SELECT id FROM public.orders WHERE id=%s AND org_id=%s FOR UPDATE",[str(order_id),str(org_id)],'order_not_found')
        value=source(org_id=org_id,order_id=order_id)
        if not value['recipient'] or expected_recipient!=value['recipient']:
            raise DocumentaryError('mail_preview_stale',detail="El correo no coincide con el proveedor sellado. Revisa su elegibilidad antes de crear la orden.")
        order=value['order']
        metadata,_=generate_artifact(org_id=org_id,actor_id=actor_id,role=role,project_version_id=UUID(str(order['project_version_id'])),
                    document_type=value['document_type'],file_format='PDF',order_id=order_id)
        document=one("SELECT * FROM public.document_artifacts WHERE id=%s AND org_id=%s",[metadata['id'],str(org_id)],'document_artifact_not_found')
        message=templates.render('PURCHASE',organization=value['organization'],reference=order['order_code'],
                                 body=value['body'],logo=mail._logo(value['organization']))
        message['attachments']=[mail._pdf_attachment(document,f"{order['order_code']}.pdf")]
        message['order_id']=str(order_id)
        message['document_sha256']=str(document['file_sha256'])
        return mail.seal_mail(org_id=org_id,actor_id=actor_id,event_key=f'purchase:{order_id}',kind='PURCHASE',
            recipient=value['recipient'],message=message,project_id=order['project_id'])
