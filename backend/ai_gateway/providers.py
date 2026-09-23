"""Provider transports for the AI gateway.

Routes (capability → provider/model/cost) are operational config in ai_routes;
tenants only ever see the white-label public_name. Real providers are wired via
environment: AI_GATEWAY_{PROVIDER}_API_KEY and AI_GATEWAY_{PROVIDER}_BASE_URL.
MOCK is the deterministic default used by seeded routes and tests — it never
performs network I/O."""

from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any

import httpx


MAX_BODY_BYTES = 1_048_576


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

    def invoke(self, *, route: dict, capability: str, input_payload: dict) -> dict[str, Any]:
        started = time.monotonic()
        try:
            response = httpx.post(
                f"{self.base_url}/invoke",
                headers={"Authorization": f"Bearer {self.api_key}"},
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
            output = body.get("output") or body.get("text") or ""
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
