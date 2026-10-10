"""Table-based email HTML with inline styles and MIME-compatible CID images."""

from __future__ import annotations

import base64
from html import escape
from pathlib import Path
from urllib.parse import urlsplit

from projects.brand_color import PAPER, effective_color

KINDS = ("MAGIC_LINK", "QUOTE", "APPROVAL", "PAYMENT", "ORDER_BLOCKED", "PURCHASE", "COLLECTION")


def render(
    kind: str,
    *,
    organization: dict,
    reference: str,
    body: str,
    action_url: str | None = None,
    logo: tuple[bytes, str] | None = None,
) -> dict:
    internal = kind in {"MAGIC_LINK", "APPROVAL", "ORDER_BLOCKED"}
    titles = {
        "MAGIC_LINK": "Tu enlace de acceso",
        "QUOTE": "Su cotización está disponible",
        "APPROVAL": "Aprobación recibida",
        "PAYMENT": "Su pago quedó registrado",
        "ORDER_BLOCKED": "Orden de taller bloqueada",
        "PURCHASE": "Su orden de compra",
        "COLLECTION": "Recordatorio de pago de su proyecto",
    }
    title = titles[kind]
    issuer = (
        "DEKOPEN"
        if internal
        else str(
            organization.get("commercial_name")
            or organization.get("name")
            or "Emisor sin identificar"
        )
    )
    color, _ = effective_color(None if internal else organization.get("brand_primary_color"))
    images = []
    if internal:
        logo = (
            Path(__file__).with_name("assets").joinpath("mail-lockup.png").read_bytes(),
            "image/png",
        )
    if logo:
        images.append(
            {"cid": "issuer", "data": base64.b64encode(logo[0]).decode(), "type": logo[1]}
        )
    masthead = (
        f'<img src="cid:issuer" width="176" style="max-width:176px;height:auto;display:block;border:0" alt="{escape(issuer, quote=True)}">'
        if logo
        else f'<p style="font-size:18px;font-weight:600;margin:0;color:{color}">{escape(issuer)}</p>'
    )
    contacts = (
        " · ".join(
            str(organization.get(key) or "")
            for key in ("brand_address", "brand_phone", "brand_email")
            if organization.get(key)
        )
        if not internal
        else ""
    )
    action = ""
    if action_url:
        parsed = urlsplit(action_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("mail_action_url_invalid")
        label = (
            "Entrar a DEKOPEN"
            if kind == "MAGIC_LINK"
            else "Revisar cotización"
            if kind == "QUOTE"
            else "Abrir en DEKOPEN"
        )
        action = f'<tr><td style="padding:0 24px 24px"><a href="{escape(action_url, quote=True)}" style="display:inline-block;background:{color};color:{PAPER};padding:12px 16px;text-decoration:none;border-radius:2px;font-weight:600">{label}</a></td></tr>'
    number_style = ";font-family:'IBM Plex Mono',monospace;font-variant-numeric:tabular-nums"
    paragraphs = "".join(
        f'<p style="margin:0 0 12px;line-height:1.5{number_style if kind == "PAYMENT" and index > 0 else ""}">{escape(line)}</p>'
        for index, line in enumerate(body.splitlines())
        if line
    )
    html = (
        '<!doctype html><html lang="es-CL"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{escape(title)}</title></head><body style=\"margin:0;background:#F5F7F6;color:#161C1F;font-family:'IBM Plex Sans',Arial,sans-serif\">"
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F5F7F6"><tr><td align="center" style="padding:24px 12px">'
        f'<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="width:100%;max-width:560px;background:{PAPER};border:1px solid #CDD5D6;border-top:3px solid {color}">'
        f'<tr><td style="padding:24px">{masthead}</td></tr><tr><td style="padding:0 24px 12px">'
        f'<h1 style="font-size:24px;font-weight:600;line-height:1.25;margin:0 0 12px">{escape(title)}</h1>'
        f"<p style=\"font-family:'IBM Plex Mono',monospace;font-size:13px;margin:0 0 20px\">{escape(reference)}</p>{paragraphs}</td></tr>{action}"
        f'<tr><td style="padding:16px 24px;border-top:1px solid #CDD5D6;font-size:12px;line-height:1.5;color:#465158">{escape(contacts or ("Asistente y operación de DEKOPEN" if internal else issuer))}</td></tr>'
        "</table></td></tr></table></body></html>"
    )
    return {
        "subject": f"{issuer} · {title} · {reference}",
        "html": html,
        "text": f"{issuer}\n{title}\n{reference}\n\n{body}\n\n{action_url or ''}\n{contacts}",
        "images": images,
        "from_name": issuer,
    }


def preview_html(message: dict) -> str:
    html = message["html"]
    for item in message["images"]:
        html = html.replace(f"cid:{item['cid']}", f"data:{item['type']};base64,{item['data']}")
    return html
