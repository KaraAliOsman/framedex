"""Job-type registry: which durable jobs exist, who may enqueue them, and how
their payloads are validated. Handlers register themselves at import time via
the `register` decorator (see jobs.handlers, imported at app ready)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from rest_framework import serializers


class JobRegistryError(ValueError):
    pass


@dataclass(frozen=True)
class JobContext:
    """What a running handler knows about the row it was claimed for."""

    job_id: UUID
    org_id: UUID
    created_by: UUID | None
    attempt: int
    payload: dict[str, Any]


ProgressReporter = Callable[[float], None]
JobRunner = Callable[[dict[str, Any], JobContext, ProgressReporter], dict[str, Any]]


@dataclass(frozen=True)
class JobSpec:
    job_type: str
    roles: tuple[str, ...]
    payload_serializer: type[serializers.Serializer]
    run: JobRunner
    label: str


_REGISTRY: dict[str, JobSpec] = {}


def register(
    job_type: str,
    *,
    roles: tuple[str, ...],
    payload_serializer: type[serializers.Serializer],
    label: str = "",
) -> Callable[[JobRunner], JobRunner]:
    def decorator(run: JobRunner) -> JobRunner:
        if job_type in _REGISTRY:
            raise JobRegistryError(f"duplicate job type: {job_type}")
        _REGISTRY[job_type] = JobSpec(
            job_type=job_type,
            roles=roles,
            payload_serializer=payload_serializer,
            run=run,
            label=label or job_type,
        )
        return run

    return decorator


def spec_for(job_type: str) -> JobSpec | None:
    return _REGISTRY.get(job_type)


def public_types() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))


def reset_registry() -> None:
    _REGISTRY.clear()
