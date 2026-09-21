"""Liveness is process-only; readiness checks actual PostgreSQL and Redis dependencies."""

from django.conf import settings
from django.db import connection, DatabaseError, transaction
from django.http import JsonResponse
from django.views.decorators.http import require_safe
import redis


@require_safe
def live(request):
    return JsonResponse({'status': 'alive'})


@require_safe
def ready(request):
    try:
        if connection.vendor != 'postgresql':
            raise DatabaseError('PostgreSQL required')
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout='2s'")
            cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_policies WHERE schemaname='public' "
                           "AND tablename='payments' AND policyname='billing_owner_read') "
                           "AND to_regclass('public.credit_lots') IS NOT NULL "
                           "AND to_regclass('public.billing_orders') IS NOT NULL "
                           "AND to_regclass('public.billing_credit_grants') IS NOT NULL "
                           "AND to_regclass('public.flow_subscription_intents') IS NOT NULL "
                           "AND to_regclass('public.flow_customer_operations') IS NOT NULL "
                           "AND to_regclass('public.credit_lot_movements') IS NOT NULL "
                           "AND to_regclass('public.billing_periods') IS NOT NULL "
                           "AND to_regclass('public.billing_lifecycle_events') IS NOT NULL "
                           "AND to_regclass('public.flow_lifecycle_operations') IS NOT NULL "
                           "AND to_regclass('public.billing_offers') IS NOT NULL "
                           "AND to_regclass('public.billing_checkouts') IS NOT NULL "
                           "AND to_regclass('public.billing_invoice_observations') IS NOT NULL")
            if not cursor.fetchone()[0]:
                raise DatabaseError('Required migration is absent')
        if not settings.REDIS_URL:
            raise redis.RedisError('Redis required')
        with redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2,
                                  socket_timeout=2) as client:
            client.ping()
    except (DatabaseError, redis.RedisError):
        return JsonResponse({'status': 'not_ready'}, status=503)
    return JsonResponse({'status': 'ready'})
