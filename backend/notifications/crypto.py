"""Capability-bearing mail is encrypted at rest, bound to tenant and row."""

import base64
import hashlib
import json
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings


def _cipher() -> AESGCM:
    return AESGCM(hashlib.sha256(settings.MAIL_ENCRYPTION_KEY.encode()).digest())


def seal(value: dict, *, org_id: object, mail_id: object) -> str:
    nonce = secrets.token_bytes(12)
    aad = f"mail:v1:{org_id}:{mail_id}".encode()
    data = json.dumps(value, ensure_ascii=False).encode()
    return base64.b64encode(nonce + _cipher().encrypt(nonce, data, aad)).decode()


def open_message(value: str, *, org_id: object, mail_id: object) -> dict:
    data = base64.b64decode(value, validate=True)
    aad = f"mail:v1:{org_id}:{mail_id}".encode()
    return json.loads(_cipher().decrypt(data[:12], data[12:], aad))
