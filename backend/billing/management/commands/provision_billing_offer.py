"""Trusted operator command; never accepts a secret on the command line."""
from datetime import date
from decimal import Decimal
from uuid import UUID

from django.core.management.base import BaseCommand, CommandError

from billing import offers
from billing.flow import FlowError


class Command(BaseCommand):
    help = 'Provision an audited billing offer from explicit observed FX and an existing Flow plan.'

    def add_arguments(self, parser):
        parser.add_argument('--org', required=True, type=UUID)
        parser.add_argument('--product', required=True)
        parser.add_argument('--cycle', choices=['monthly','annual'])
        parser.add_argument('--flow-plan')
        parser.add_argument('--fx-rate', required=True, type=Decimal)
        parser.add_argument('--fx-source', required=True)
        parser.add_argument('--fx-date', required=True, type=date.fromisoformat)
        parser.add_argument('--fx-snapshot', required=True, type=UUID)
        parser.add_argument('--reason', required=True)

    def handle(self, *args, **options):
        try:
            client, callback, _, _ = offers.runtime()
            if options['flow_plan']:
                from dekopen_engine.billing import product_terms, platform_charge_clp
                remote = client.plan(options['flow_plan'])
                price, _ = product_terms(options['product'], options['cycle'])
                if (remote.get('planId') != options['flow_plan'] or remote.get('currency') != 'CLP'
                        or Decimal(str(remote.get('amount'))) != platform_charge_clp(price, options['fx_rate'])
                        or remote.get('interval') != {'monthly':3,'annual':4}[options['cycle']]
                        or remote.get('interval_count') != 1):
                    raise CommandError('The existing merchant plan does not match the approved price/cycle.')
            offer = offers.provision(options['org'],product_code=options['product'],billing_cycle=options['cycle'],
                environment='sandbox' if client.api_url=='https://sandbox.flow.cl/api' else 'production',
                provider_plan_id=options['flow_plan'],fx_rate=options['fx_rate'],fx_source=options['fx_source'],
                fx_observed_on=options['fx_date'],fx_snapshot_id=options['fx_snapshot'],reason=options['reason'])
            self.stdout.write(str(offer['id']))
            if options['flow_plan']:
                self.stdout.write('Configure the merchant plan urlCallback: '+callback+'/api/v1/billing/flow/plan/'+str(offer['id'])+'/')
        except (FlowError,ValueError) as error:
            raise CommandError(str(error)) from None
