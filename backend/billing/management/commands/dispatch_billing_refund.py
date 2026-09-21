"""Operator confirmation of a previously prepared, exceptional refund."""

from uuid import UUID

from django.core.management.base import BaseCommand, CommandError

from billing import offers, refunds
from billing.flow import FlowError
from dekopen_engine.commercial import PricingError


class Command(BaseCommand):
    help = 'Send the selected prepared refund once to Flow; an ambiguous dispatch is never retried.'

    def add_arguments(self, parser):
        parser.add_argument('--org', required=True, type=UUID)
        parser.add_argument('--operation', required=True, type=UUID)
        parser.add_argument('--receiver-email', required=True)

    def handle(self, *args, **options):
        try:
            client, callback, _, _ = offers.runtime()
            refunds.dispatch(options['org'], options['operation'], client,
                receiver_email=options['receiver_email'],
                callback_url=callback+'/api/v1/billing/flow/refund/'+str(options['operation'])+'/')
        except (FlowError, PricingError, ValueError) as error:
            raise CommandError(str(error)) from None
        self.stdout.write('Dispatch recorded; the signed Flow refund status determines completion.')
