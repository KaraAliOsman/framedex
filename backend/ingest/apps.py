from django.apps import AppConfig


class IngestConfig(AppConfig):
    name = "ingest"

    def ready(self):
        from ingest import handlers  # noqa: F401
