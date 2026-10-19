"""Operator-only review grant (dirección final 06 · 4).

Review environments need explicit, audited and isolated grants — never a
DEBUG bypass or a client field. This command refuses to run unless the
process declares REVIEW_OPERATOR_GRANTS=1 (set only by the local REVIEW
stack, never in production), records a ledger entry `REVIEW_GRANT` with the
operator's reason, and creates a lot that expires (default 7 days). It does
not touch plans, offers, subscriptions, prices or allowances.
"""

import os
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from django.core.management.base import BaseCommand, CommandError

from billing import lifecycle, wallet


class Command(BaseCommand):
    help = "Grant audited review credits to one organization (REVIEW environments only)."

    def add_arguments(self, parser):
        parser.add_argument("--org", required=True, type=UUID)
        parser.add_argument("--credits", required=True, type=int)
        parser.add_argument("--reason", required=True)
        parser.add_argument("--days", type=int, default=7)

    def handle(self, *args, **options):
        if os.environ.get("REVIEW_OPERATOR_GRANTS") != "1":
            raise CommandError("Review grants are disabled in this environment (REVIEW_OPERATOR_GRANTS != 1).")
        credits = options["credits"]
        if not 1 <= credits <= 5000:
            raise CommandError("Credits must be between 1 and 5000.")
        reason = " ".join(options["reason"].split())
        if len(reason) < 10:
            raise CommandError("A reason of at least 10 characters is required for the audit.")
        if not 1 <= options["days"] <= 30:
            raise CommandError("Review lots expire within 1–30 days.")
        org = options["org"]
        key = f"review-grant:{uuid4()}"
        expires = datetime.now(timezone.utc) + timedelta(days=options["days"])
        with wallet.financial_transaction(org):
            wallet.reconcile(org)
            lifecycle._grant(org, credits, key=key, origin="legacy", expires=expires,
                             reference=None, action="REVIEW_GRANT")
        self.stdout.write(f"Granted {credits} review credits to {org} ({key}); expires {expires.isoformat()}. "
                          f"Reason: {reason}")
