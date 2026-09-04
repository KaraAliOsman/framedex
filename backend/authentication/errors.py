"""One fail-closed error envelope for every SHOT-04 API failure."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException, AuthenticationFailed, NotAuthenticated
from rest_framework.response import Response


class ContractAPIException(APIException):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        detail: str,
        extra: Mapping[str, object] | None = None,
        error_extra: Mapping[str, object] | None = None,
    ) -> None:
        self.status_code = status_code
        self.contract_code = code
        self.public_detail = detail
        self.extra = dict(extra or {})
        self.error_extra = dict(error_extra or {})
        super().__init__(detail=detail, code=code)


def contract_error(
    status_code: int,
    code: str,
    detail: str,
    *,
    extra: Mapping[str, object] | None = None,
    error_extra: Mapping[str, object] | None = None,
) -> ContractAPIException:
    return ContractAPIException(
        status_code=status_code,
        code=code,
        detail=detail,
        extra=extra,
        error_extra=error_extra,
    )


def invalid_token() -> ContractAPIException:
    return contract_error(status.HTTP_401_UNAUTHORIZED, "invalid_token", "Invalid token")


def contract_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    from rest_framework.views import exception_handler as drf_exception_handler

    if isinstance(exc, ContractAPIException):
        error_body: dict[str, object] = {
            "code": exc.contract_code,
            "detail": exc.public_detail,
        }
        error_body.update(exc.error_extra)
        body: dict[str, object] = {"error": error_body}
        body.update(exc.extra)
        return Response(body, status=exc.status_code)

    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, NotAuthenticated):
        code = "authentication_required"
        detail = "Authentication is required"
    elif isinstance(exc, AuthenticationFailed):
        code = "invalid_token"
        detail = "Invalid token"
    else:
        code = "validation_error" if response.status_code == 400 else "request_failed"
        detail = "Request validation failed" if response.status_code == 400 else "Request failed"
    response.data = {"error": {"code": code, "detail": detail}}
    return response
