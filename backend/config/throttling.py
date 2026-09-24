"""Atomic shared Redis quota for authenticated API use (PRD-19: 100/min)."""

import hashlib

from django.conf import settings
import redis
from rest_framework.throttling import BaseThrottle

from authentication.errors import contract_error

WINDOW = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then redis.call('EXPIRE', KEYS[1], 60) end
return count
"""


class ProductionRateThrottle(BaseThrottle):
    def allow_request(self, request, view):
        if not settings.PRODUCTION:
            return True
        # Verified user ID cannot be rotated by forging an organization or forwarding header.
        identity = str(request.user.id) if request.user else request.META.get('REMOTE_ADDR', '')
        key = 'dekopen:api:' + hashlib.sha256(identity.encode()).hexdigest()
        try:
            with redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2,
                                      socket_timeout=2) as client:
                return int(client.eval(WINDOW, 1, key)) <= 100
        except redis.RedisError:
            raise contract_error(503, 'rate_limit_unavailable',
                                 'El servicio está temporalmente ocupado. Intenta nuevamente.') from None

    def wait(self):
        return 60


class PortalRateThrottle(BaseThrottle):
    """Anonymous portal endpoints: 30 requests/min per client IP.

    Token probing and decision flooding get the same Redis quota as the
    authenticated API, keyed on REMOTE_ADDR since no user exists.
    """

    LIMIT = 30

    def allow_request(self, request, view):
        if not settings.PRODUCTION:
            return True
        identity = request.META.get('REMOTE_ADDR', '')
        key = 'dekopen:portal:' + hashlib.sha256(identity.encode()).hexdigest()
        try:
            with redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2,
                                      socket_timeout=2) as client:
                return int(client.eval(WINDOW, 1, key)) <= self.LIMIT
        except redis.RedisError:
            raise contract_error(503, 'rate_limit_unavailable',
                                 'El servicio está temporalmente ocupado. Intenta nuevamente.') from None

    def wait(self):
        return 60
