"""Poll the durable job queue and execute claimed work.

Development:  python backend/manage.py runjobs --once
Production:   python backend/manage.py runjobs --poll 2 --batch 8
"""

from django.core.management.base import BaseCommand

from jobs import worker


class Command(BaseCommand):
    help = "Claim and execute queued job_runs rows (durable background worker)."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")
        parser.add_argument("--batch", type=int, default=8)
        parser.add_argument("--poll", type=float, default=2.0)
        parser.add_argument("--worker-id", type=str, default="")

    def handle(self, *args, **options):
        worker_id = options["worker_id"] or worker.worker_id_default()
        if options["once"]:
            processed = worker.run_once(worker_id=worker_id, batch=options["batch"])
            self.stdout.write(f"{worker_id}: processed {processed} job(s)")
            return
        try:
            worker.run_forever(
                worker_id=worker_id,
                batch=options["batch"],
                poll_seconds=options["poll"],
            )
        except KeyboardInterrupt:
            self.stdout.write(f"{worker_id}: stopped")
