"""Safe request metadata; never log bearer tokens, query strings or payment bodies."""

from time import monotonic

from django.conf import settings
import structlog


class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        structlog.contextvars.clear_contextvars()
        started = monotonic()
        response = self.get_response(request)
        if settings.PRODUCTION:
            match = request.resolver_match
            structlog.get_logger('dekopen.http').info(
                'http_request', route=match.route if match else None,
                method=request.method, status=response.status_code,
                user_id=str(request.user.id) if getattr(request, 'user', None) else None,
                org_id=getattr(request, 'verified_org_id', None),
                project_id=str(match.kwargs.get('project_id', '')) if match else None,
                version_id=str(match.kwargs.get('version_id', '')) if match else None,
                engine_version=settings.RELEASE_SHA, model_route=None,
                latency_ms=round((monotonic() - started) * 1000, 3),
            )
            response['Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none'"
            response['Cache-Control'] = 'no-store'
        structlog.contextvars.clear_contextvars()
        return response
