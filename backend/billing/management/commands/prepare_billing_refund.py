"""Freeze an exceptional refund for an authorized operator's separate dispatch."""

from decimal import Decimal
from uuid import UUID

from django.core.management.base import BaseCommand, CommandError

from billing import refunds
from billing.flow import FlowError
from dekopen_engine.commercial import PricingError


class Command(BaseCommand):
    help = 'Prepare an auditable exceptional refund; does not send a refund to Flow.'

    def add_arguments(self, parser):
        parser.add_argument('--org', required=True, type=UUID)
        parser.add_argument('--operation-key', required=True)
        parser.add_argument('--order', required=True, type=UUID)
        parser.add_argument('--amount', required=True, type=Decimal)
        parser.add_argument('--reason', required=True)
        parser.add_argument('--authorization', required=True)
        parser.add_argument('--grant', action='append', type=UUID, default=[])
        parser.add_argument('--end-entitlement', action='store_true')

    def handle(self, *args, **options):
        try:
            operation = refunds.prepare(options['org'], operation_key=options['operation_key'],
                order_id=options['order'], amount=options['amount'], reason=options['reason'],
                authorization=options['authorization'], grant_ids=options['grant'],
                revoke_period=options['end_entitlement'])
        except (FlowError, PricingError, ValueError) as error:
            raise CommandError(str(error)) from None
        self.stdout.write(str(operation['id']))
