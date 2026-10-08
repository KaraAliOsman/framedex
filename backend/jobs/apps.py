from django.apps import AppConfig


class JobsConfig(AppConfig):
    name = "jobs"

    def ready(self) -> None:
        from jobs import handlers  # noqa: F401
        from notifications import handlers as mail_handlers  # noqa: F401
