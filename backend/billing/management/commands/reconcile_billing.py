from uuid import UUID
from django.core.management.base import BaseCommand, CommandError
from billing import commerce, offers, wallet
from billing.flow import FlowError
from billing.repository import rows
from dekopen_engine.commercial import PricingError


class Command(BaseCommand):
    help = 'Reconcile known billing subscriptions through signed GETs; safe to run repeatedly.'

    def add_arguments(self,parser):
        parser.add_argument('--org',type=UUID)

    def handle(self,*args,**options):
        client,_,_,zone=offers.runtime()
        organizations = ([{'org_id':options['org']}] if options['org'] else
            rows('SELECT DISTINCT org_id FROM public.flow_subscription_intents ORDER BY org_id'))
        failures=0
        for organization in organizations:
            org=organization['org_id']
            try:
                commerce.sync(org,client,provider_timezone=zone)
                wallet.summary(org)
                with wallet.financial_transaction(org):
                    if rows('SELECT id FROM public.billing_invoice_observations WHERE org_id=%s LIMIT 1',[org]):
                        raise FlowError('flow_invoice_requires_reconciliation')
                self.stdout.write(str(org)+': reconciled')
            except (FlowError,PricingError) as error:
                failures+=1
                self.stderr.write(str(org)+': '+error.code)
        if failures:
            raise CommandError(f'{failures} organizations require reconciliation; no mutation retried.')
