"""Mailpit sandbox and authenticated SMTP share the same MIME message."""

import base64
from email.headerregistry import Address
from email.message import EmailMessage
import smtplib
import ssl

from django.conf import settings


def integration() -> dict:
    connected = settings.MAIL_PROVIDER == "smtp" and bool(
        settings.MAIL_SMTP_HOST and settings.MAIL_FROM_ADDRESS
    )
    return {
        "provider": settings.MAIL_PROVIDER,
        "connected": connected,
        "status": "Conectado" if connected else "No conectado · sandbox Mailpit",
        "instructions": "Configura el remitente, SMTP con TLS y SPF/DKIM/DMARC según docs/operations/ACTIVACION.md. El sandbox entrega solo a Mailpit.",
    }


def mime_message(payload: dict, *, mail_id: object, recipient: str) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = payload["subject"]
    message["From"] = Address(
        display_name=payload["from_name"], addr_spec=settings.MAIL_FROM_ADDRESS
    )
    message["To"] = Address(addr_spec=recipient)
    message["Message-ID"] = f"<{mail_id}@{settings.MAIL_FROM_ADDRESS.split('@')[-1]}>"
    message.set_content(payload["text"])
    message.add_alternative(payload["html"], subtype="html")
    for image in payload.get("images", []):
        main, subtype = image["type"].split("/")
        message.get_payload()[-1].add_related(
            base64.b64decode(image["data"]), maintype=main, subtype=subtype, cid=f"<{image['cid']}>"
        )
    for attachment in payload.get("attachments", []):
        message.add_attachment(
            base64.b64decode(attachment["data"]),
            maintype="application",
            subtype="pdf",
            filename=attachment["filename"],
        )
    return message


def deliver(payload: dict, *, mail_id: object, recipient: str) -> None:
    provider = settings.MAIL_PROVIDER
    if provider not in {"sandbox", "smtp"}:
        raise ValueError("mail_provider_invalid")
    host = settings.MAIL_SMTP_HOST if provider == "smtp" else settings.MAIL_SANDBOX_HOST
    port = settings.MAIL_SMTP_PORT if provider == "smtp" else settings.MAIL_SANDBOX_PORT
    if provider == "sandbox" and host not in {"localhost", "127.0.0.1", "host.docker.internal"}:
        raise ValueError("mail_sandbox_host_invalid")
    message = mime_message(payload, mail_id=mail_id, recipient=recipient)
    transport = smtplib.SMTP_SSL if provider == "smtp" and settings.MAIL_SMTP_SSL else smtplib.SMTP
    kwargs = {"context": ssl.create_default_context()} if transport is smtplib.SMTP_SSL else {}
    with transport(host, port, timeout=15, **kwargs) as client:
        if provider == "smtp":
            if settings.MAIL_SMTP_STARTTLS:
                client.starttls(context=ssl.create_default_context())
            if not (settings.MAIL_SMTP_SSL or settings.MAIL_SMTP_STARTTLS):
                raise ValueError("mail_smtp_tls_required")
            if settings.MAIL_SMTP_USER:
                client.login(settings.MAIL_SMTP_USER, settings.MAIL_SMTP_PASSWORD)
        refused = client.send_message(message)
        if refused:
            raise smtplib.SMTPRecipientsRefused(refused)
