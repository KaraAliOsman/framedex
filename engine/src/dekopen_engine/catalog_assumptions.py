"""Context-local trace of catalog inputs consumed by a calculation.

This records dependencies only. It never resolves values or changes formulas.
Nested module calculations contribute to their assembly and keep their own trace.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field

from .models import CatalogAssumption, EngineResult, SystemParams


@dataclass
class CatalogConsumption:
    params: SystemParams
    used: set[tuple[str, str, str]] = field(default_factory=set)

    def attach(self, result: EngineResult) -> EngineResult:
        assumptions = {item.rule: item for item in result.assumptions}
        for item in self.params.value_origins:
            if item.origin != "SUGGESTED":
                continue
            if not any(scope == item.scope and key == item.key and (
                item.rule == rule or item.rule.startswith(rule + ".")
                or rule.startswith(item.rule + ".")) for scope, key, rule in self.used):
                continue
            rule = ":".join(part for part in (item.scope, item.key, item.rule) if part)
            assumptions[rule] = CatalogAssumption(rule=rule, value=item.value)
        if not assumptions:
            return result
        return result.model_copy(update={"assumptions": [assumptions[key] for key in sorted(assumptions)]})


_traces: ContextVar[tuple[CatalogConsumption, ...]] = ContextVar("catalog_consumption", default=())


@contextmanager
def catalog_consumption(params: SystemParams) -> Iterator[CatalogConsumption]:
    trace = CatalogConsumption(params)
    if not params.value_origins:
        yield trace
        return
    token = _traces.set((*_traces.get(), trace))
    try:
        yield trace
    finally:
        _traces.reset(token)


def consume(scope: str, key: str, *rules: str) -> None:
    for trace in _traces.get():
        trace.used.update((scope, key, rule) for rule in rules)


def system_inputs(*rules: str) -> None:
    consume("SYSTEM", "", *rules)


def profile_inputs(sku: str, *rules: str) -> None:
    consume("PROFILE", sku, *rules)
