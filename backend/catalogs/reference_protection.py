"""One atomic comparison for a complete catalog write or reviewed import batch."""

from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps

from django.core import signing
from django.db import connection, transaction

from authentication.errors import ContractAPIException, contract_error
from dekopen_engine.calibration import measurement_comparison, physical_reference
from pricing.repository import json_text

SALT = "catalog-reference-change-v1"
_active = ContextVar("catalog_reference_change", default=None)


def _current(org_id, system_id, reference):
    from catalogs.reference_windows import calculate
    from engine_api.repository import SystemNotFound, UnsupportedCatalogContract
    try:
        _, result = calculate(org_id, system_id, reference["input"])
        return {"output": physical_reference(result), "error": None, "measurements": measurement_comparison(result, {})}
    except (ValueError, SystemNotFound, UnsupportedCatalogContract) as error:
        return {"output": None, "error": str(error), "measurements": []}
    except ContractAPIException as error:
        return {"output": None, "error": error.public_detail, "measurements": []}


@contextmanager
def protect_changes(org_id, review_token=None):
    if connection.vendor != "postgresql":
        yield
        return
    active = _active.get()
    if active is not None:
        if active["org_id"] != str(org_id):
            raise ValueError("A catalog batch cannot span organizations")
        yield
        return
    state = {"org_id": str(org_id), "systems": {}, "mutations": []}
    marker = _active.set(state)
    try:
        with transaction.atomic():
            yield
            differences = []
            for system_id, before in state["systems"].items():
                for reference, previous in before["references"]:
                    current = _current(org_id, system_id, reference)
                    if previous != current:
                        differences.append({"system_id": system_id, "reference_id": str(reference["id"]),
                            "expected_output": reference["expected_output"], "before": previous, "after": current})
            if differences:
                from catalogs.reference_windows import _digest
                identity = {"org_id": str(org_id), "mutations": _digest(json_text(state["mutations"])),
                    "before": {key: item["fingerprint"] for key, item in state["systems"].items()},
                    "differences": _digest(differences)}
                accepted = None
                if review_token:
                    try:
                        accepted = signing.loads(review_token, salt=SALT, max_age=1800)
                    except signing.BadSignature:
                        pass
                if accepted != identity:
                    raise contract_error(409, "catalog_reference_changed",
                        "La edición cambia una ventana que ya comprobaste. Revisa el antes y el después antes de guardar.",
                        extra={"golden_review": {"changes": differences,
                            "review_token": signing.dumps(identity, salt=SALT, compress=True)}})
    finally:
        _active.reset(marker)


def _before(resource, org_id, operation, row_id, values):
    from catalogs import service
    from catalogs.use_levels import technical_fingerprint
    from catalogs.reference_windows import references
    state = _active.get()
    if state is None or resource not in (service.SYSTEMS, service.ARTICLES, service.BEADS, service.KITS):
        return
    if operation == "create":
        system_id = (values or {}).get("system_id")
    else:
        row = service.retrieve(resource, org_id, row_id)
        system_id = row["id"] if resource is service.SYSTEMS else row["system_id"]
    if system_id is None:
        return
    service._lock_singleton_role(system_id)
    system_id = str(system_id)
    if system_id not in state["systems"]:
        found = references(org_id, system_id)
        state["systems"][system_id] = {"fingerprint": technical_fingerprint(org_id, system_id) if found else None,
            "references": [(ref, _current(org_id, system_id, ref)) for ref in found]}
    if state["systems"][system_id]["references"]:
        state["mutations"].append({"table": resource.table, "operation": operation,
            "row_id": str(row_id) if row_id else None, "values": values})


def protected_write(operation):
    def decorate(function):
        @wraps(function)
        def wrapped(resource, org_id, *args, **kwargs):
            row_id = args[0] if args and operation != "create" else kwargs.get("row_id")
            values = (args[0] if args else kwargs.get("values")) if operation == "create" else (
                args[1] if len(args) > 1 else kwargs.get("values"))
            with protect_changes(org_id):
                _before(resource, org_id, operation, row_id, values)
                return function(resource, org_id, *args, **kwargs)
        return wrapped
    return decorate
