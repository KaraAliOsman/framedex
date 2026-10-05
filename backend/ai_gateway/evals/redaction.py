"""Private environment and credential fields never become evaluation artifacts."""

from collections.abc import Mapping
import os
import re
from typing import Any

_PRIVATE_ENV = re.compile(r"KEY|SECRET|TOKEN|PASSWORD|CREDENTIAL|DATABASE_URL", re.IGNORECASE)
_PRIVATE_FIELD = re.compile(
    r"^(?:authorization|token|api[_-]?key|(?:access|refresh|service_role)[_-]?token|"
    r".*(?:password|secret|credential)(?:[_-]?key)?)$", re.IGNORECASE,
)
_JWT = re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")


def redact_report(value: Any, *, environment: Mapping[str, str] | None = None) -> Any:
    secrets = sorted({v for k, v in (os.environ if environment is None else environment).items()
                      if _PRIVATE_ENV.search(k) and len(v) >= 8}, key=len, reverse=True)

    def clean(item: Any) -> Any:
        if isinstance(item, dict):
            return {key: "[redacted]" if _PRIVATE_FIELD.fullmatch(str(key)) else clean(part)
                    for key, part in item.items()}
        if isinstance(item, list):
            return [clean(part) for part in item]
        if isinstance(item, str):
            for secret in secrets:
                item = item.replace(secret, "[redacted]")
            return _JWT.sub("[redacted JWT]", item)
        return item

    return clean(value)
