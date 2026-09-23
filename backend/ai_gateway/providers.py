"""Provider transports for the AI gateway.

Routes (capability → provider/model/cost) are operational config in ai_routes;
tenants only ever see the white-label public_name. Real providers are wired via
environment: AI_GATEWAY_{PROVIDER}_API_KEY and AI_GATEWAY_{PROVIDER}_BASE_URL.
MOCK is the deterministic default used by seeded routes and tests — it never
performs network I/O."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import socket
import time
from typing import Any
from urllib.parse import urlparse

import httpx


MAX_BODY_BYTES = 1_048_576


def _resolve_provider_host(hostname: str) -> str | None:
    """Resolve the configured host once and return a global connect address,
    or None. Literal IPs are checked directly; a DNS name must resolve to
    global answers only — any non-global answer refuses the provider, and
    resolution failure refuses closed. The request pins this exact address
    (Host header + SNI keep the configured name), so there is no second
    lookup for a rebinding attack to poison."""
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            infos = socket.getaddrinfo(hostname, 443, proto=socket.IPPROTO_TCP)
        except (socket.gaierror, UnicodeError):
            return None
        resolved: list[str] = []
        for info in infos:
            if not info[4] or not info[4][0]:
                continue
            try:
                candidate = ipaddress.ip_address(info[4][0])
            except ValueError:
                return None
            if not candidate.is_global:
                return None
            resolved.append(info[4][0])
        return resolved[0] if resolved else None
    return str(address) if address.is_global else None


class ProviderError(Exception):
    """Sanitized provider failure — never carries credentials or payloads."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class HttpProvider:
    """Generic JSON invocation endpoint: POST {model, capability, input}."""

    def __init__(self, *, provider: str):
        self.provider = provider
        self.api_key = os.environ.get(f"AI_GATEWAY_{provider}_API_KEY", "")
        self.base_url = os.environ.get(f"AI_GATEWAY_{provider}_BASE_URL", "").rstrip("/")
        if not self.api_key or not self.base_url:
            raise ProviderError("ai_provider_unavailable")
        # Provider URLs are operator config, but a compromised value must not
        # turn the gateway into an authenticated proxy for internal services:
        # https-only, and the host must not resolve to a non-global address.
        try:
            parsed = urlparse(self.base_url)
            hostname = parsed.hostname
        except ValueError as error:
            raise ProviderError("ai_provider_unavailable") from error
        if parsed.scheme != "https" or not hostname:
            raise ProviderError("ai_provider_unavailable")
        connect_ip = _resolve_provider_host(hostname)
        if connect_ip is None:
            raise ProviderError("ai_provider_unavailable")
        self._host = hostname
        self._port = parsed.port or 443
        self._connect_ip = connect_ip

    def invoke(self, *, route: dict, capability: str, input_payload: dict) -> dict[str, Any]:
        started = time.monotonic()
        try:
            url_host = f"[{self._connect_ip}]" if ":" in self._connect_ip else self._connect_ip
            port_suffix = "" if self._port == 443 else f":{self._port}"
            host_header = (
                self._host if self._port == 443 else f"{self._host}:{self._port}"
            )
            response = httpx.post(
                f"https://{url_host}{port_suffix}/invoke",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Host": host_header,
                },
                extensions={"sni_hostname": self._host},
                json={
                    "model": route["provider_model"],
                    "capability": capability,
                    "input": input_payload,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            if len(response.content) > MAX_BODY_BYTES:
                raise ProviderError("ai_provider_output_too_large")
            body = response.json()
            if not isinstance(body, dict):
                raise TypeError("provider body is not an object")
            usage = body.get("usage") or {}
            if not isinstance(usage, dict):
                raise TypeError("provider usage is not an object")
            output = body.get("output") if "output" in body else body.get("text")
            if not isinstance(output, str):
                raise TypeError("provider output is not a string")
            tokens_prompt = int(usage.get("prompt_tokens") or 0)
            tokens_completion = int(usage.get("completion_tokens") or 0)
        except ProviderError:
            raise
        except (httpx.HTTPError, TypeError, ValueError) as error:
            raise ProviderError("ai_provider_error") from error
        return {
            "output": output,
            "tokens_prompt": tokens_prompt,
            "tokens_completion": tokens_completion,
            "latency_ms": int((time.monotonic() - started) * 1000),
        }


class MockProvider:
    """Deterministic provider — a real output a test can assert, never I/O."""

    def invoke(self, *, route: dict, capability: str, input_payload: dict) -> dict[str, Any]:
        started = time.monotonic()
        digest = hashlib.sha256(
            json.dumps(input_payload, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
        output = (
            f"{route['public_name']} [{capability}] "
            f"respuesta determinista para {digest}"
        )
        serialized = json.dumps(input_payload, default=str)
        return {
            "output": output,
            "tokens_prompt": max(1, len(serialized) // 8),
            "tokens_completion": max(1, len(output) // 8),
            "latency_ms": int((time.monotonic() - started) * 1000),
        }


def provider_for(route: dict):
    name = str(route["provider"]).upper()
    if name == "MOCK":
        return MockProvider()
    return HttpProvider(provider=name)
