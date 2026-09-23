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
import re
import socket
import time
from typing import Any
from urllib.parse import urlparse

import httpx


MAX_BODY_BYTES = 1_048_576
# A configured base path may only contain plain ASCII segments — no
# encoded separators, dot segments, backslashes, or whitespace that could
# redirect the authenticated request on the approved host.
_BASE_PATH_RE = re.compile(r"/(?:[A-Za-z0-9._~-]+/)*[A-Za-z0-9._~-]*")


def _resolve_provider_hosts(hostname: str) -> list[str] | None:
    """Resolve the configured host once and return every validated global
    answer in resolver order, or None. Literal IPs are checked directly; a
    DNS name must resolve to global answers only — any non-global answer
    refuses the provider, and resolution failure refuses closed. Requests
    pin these exact addresses (Host header + SNI keep the configured name),
    so no second lookup exists for a rebinding attack to poison — while
    trying each answer preserves normal multi-address failover."""
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
        return resolved or None
    return [str(address)] if address.is_global else None


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
        # https-only, no userinfo/query/fragment, and the host must resolve
        # to global addresses only. Anything else refuses closed rather than
        # silently redirecting or dropping part of the configured endpoint.
        try:
            parsed = urlparse(self.base_url)
            hostname = parsed.hostname
            port = parsed.port or 443
        except ValueError as error:
            raise ProviderError("ai_provider_unavailable") from error
        if (
            parsed.scheme != "https"
            or not hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ProviderError("ai_provider_unavailable")
        connect_ips = _resolve_provider_hosts(hostname)
        if connect_ips is None:
            raise ProviderError("ai_provider_unavailable")
        base_path = parsed.path.rstrip("/")
        if base_path and (
            not _BASE_PATH_RE.fullmatch(base_path)
            or any(segment in (".", "..") for segment in base_path.split("/"))
        ):
            raise ProviderError("ai_provider_unavailable")
        self._host = hostname
        self._port = port
        self._connect_ips = connect_ips
        self._base_path = base_path

    def _send(
        self,
        client: httpx.Client,
        connect_ip: str,
        *,
        route: dict,
        capability: str,
        input_payload: dict,
        host_header: str,
        port_suffix: str,
        operation_key: str | None,
    ) -> bytes:
        """One pinned attempt: the URL carries the validated connect address
        while Host + SNI keep the configured name. The body streams in with
        a hard byte cap — an unbounded provider response cannot exhaust
        memory before it is rejected."""
        url_host = f"[{connect_ip}]" if ":" in connect_ip else connect_ip
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Host": host_header,
        }
        if operation_key:
            # The operation key doubles as the provider-level idempotency key
            # so a retry ambiguous to us can still dedupe provider-side.
            headers["Idempotency-Key"] = operation_key
        with client.stream(
            "POST",
            f"https://{url_host}{port_suffix}{self._base_path}/invoke",
            headers=headers,
            extensions={"sni_hostname": self._host},
            json={
                "model": route["provider_model"],
                "capability": capability,
                "input": input_payload,
            },
        ) as response:
            response.raise_for_status()
            content = bytearray()
            for chunk in response.iter_bytes(65536):
                content += chunk
                if len(content) > MAX_BODY_BYTES:
                    raise ProviderError("ai_provider_output_too_large")
        return bytes(content)

    def _request(
        self,
        *,
        route: dict,
        capability: str,
        input_payload: dict,
        client: httpx.Client | None = None,
        operation_key: str | None = None,
    ) -> bytes:
        """POST to the provider on each validated address until one connects.
        Connect-phase failures advance to the next pinned answer; any HTTP
        response (including errors) stops the loop — it is an answer, not a
        transport failure. Tests inject a MockTransport client so the real
        httpx request path (extensions, streaming) is exercised."""
        port_suffix = "" if self._port == 443 else f":{self._port}"
        header_host = f"[{self._host}]" if ":" in self._host else self._host
        host_header = (
            header_host if self._port == 443 else f"{header_host}:{self._port}"
        )
        if client is None:
            with httpx.Client(timeout=60.0) as owned:
                return self._attempts(
                    owned, route, capability, input_payload, host_header, port_suffix,
                    operation_key,
                )
        return self._attempts(
            client, route, capability, input_payload, host_header, port_suffix,
            operation_key,
        )

    def _attempts(
        self,
        client: httpx.Client,
        route: dict,
        capability: str,
        input_payload: dict,
        host_header: str,
        port_suffix: str,
        operation_key: str | None,
    ) -> bytes:
        last_error: httpx.HTTPError | None = None
        for connect_ip in self._connect_ips:
            try:
                return self._send(
                    client,
                    connect_ip,
                    route=route,
                    capability=capability,
                    input_payload=input_payload,
                    host_header=host_header,
                    port_suffix=port_suffix,
                    operation_key=operation_key,
                )
            except (httpx.ConnectError, httpx.ConnectTimeout) as error:
                last_error = error
        raise ProviderError("ai_provider_error") from last_error

    def invoke(
        self,
        *,
        route: dict,
        capability: str,
        input_payload: dict,
        client: httpx.Client | None = None,
        operation_key: str | None = None,
    ) -> dict[str, Any]:
        started = time.monotonic()
        # Ephemeral fetch URLs are resolved at wire time, never carried in
        # input_payload: the audited input hash must stay identical across
        # retries even though a fresh signed URL is minted each attempt.
        wire_input = dict(input_payload)
        if wire_input.get("storage_path"):
            from documents.storage import SupabaseDocumentStorage

            wire_input["document_url"] = SupabaseDocumentStorage().signed_url(
                str(wire_input["storage_path"])
            )
        try:
            content = self._request(
                route=route,
                capability=capability,
                input_payload=wire_input,
                client=client,
                operation_key=operation_key,
            )
            body = json.loads(content)
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
            # Usage feeds an INT4 audit column — a malformed or impossible count
            # is a provider error, not an audit-time database exception raised
            # after the paid call already succeeded.
            if not (
                0 <= tokens_prompt <= 2_147_483_647
                and 0 <= tokens_completion <= 2_147_483_647
            ):
                raise TypeError("provider token usage is outside the audit range")
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

    def invoke(
        self, *, route: dict, capability: str, input_payload: dict,
        operation_key: str | None = None,
    ) -> dict[str, Any]:
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
