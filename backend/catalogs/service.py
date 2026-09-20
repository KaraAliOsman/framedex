"""Tenant-scoped catalog persistence; callers enter authenticated RLS first."""

from dataclasses import dataclass
from decimal import Decimal
import json
from hashlib import sha256

from django.db import connection

from authentication.errors import contract_error
from catalogs.serializers import (
    ArticleWriteSerializer,
    BeadWriteSerializer,
    KitWriteSerializer,
    SystemWriteSerializer,
)


@dataclass(frozen=True)
class Resource:
    table: str
    serializer: type
    extra_columns: tuple[str, ...] = ()

    @property
    def fields(self):
        return tuple(self.serializer().fields)

    @property
    def projection(self):
        columns = ("id", "org_id", *self.fields, *self.extra_columns)
        return ", ".join(
            "contents::text AS contents" if name == "contents" else name for name in columns
        )


SYSTEMS = Resource(
    "profile_systems",
    SystemWriteSerializer,
    ("is_global", "is_demo"),
)
ARTICLES = Resource("profile_articles", ArticleWriteSerializer)
BEADS = Resource("glazing_bead_matrix", BeadWriteSerializer)
KITS = Resource("hardware_kits", KitWriteSerializer)


def _not_found():
    return contract_error(404, "catalog_not_found", "catalogs.errors.not_found")


def _fetch(resource, where, params, *, lock=False):
    suffix = " FOR UPDATE" if lock else " ORDER BY id"
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT {resource.projection} FROM public.{resource.table} WHERE {where}{suffix}",
            params,
        )
        names = [column[0] for column in cursor.description]
        result = [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]
    for row in result:
        row["read_only"] = (
            row["org_id"] is None or row.get("is_global", False) or row.get("is_demo", False)
        )
        if "contents" in row:
            row["contents"] = json.loads(
                row["contents"],
                parse_float=Decimal,
                parse_int=Decimal,
            )
        row["revision"] = catalog_revision(row)
    return result


def catalog_revision(row):
    encoded = json.dumps(row, sort_keys=True, separators=(",", ":"), default=str, allow_nan=False)
    return "sha256:" + sha256(encoded.encode("utf-8")).hexdigest()


def require_revision(current, expected):
    if expected != '"' + current["revision"] + '"':
        raise contract_error(409, "catalog_stale_edit", "catalogs.errors.stale_edit")


def _visibility(resource):
    if resource is SYSTEMS:
        return "(org_id = %s OR (org_id IS NULL AND is_global))"
    return (
        "(org_id = %s OR (org_id IS NULL AND system_id IN "
        "(SELECT id FROM public.profile_systems "
        "WHERE org_id IS NULL AND is_global)))"
    )


def list_rows(resource, org_id, system_id=None):
    where = _visibility(resource)
    params = [org_id]
    if system_id is not None:
        where += " AND system_id = %s"
        params.append(system_id)
    return _fetch(resource, where, params)


def retrieve(resource, org_id, row_id, *, lock=False):
    records = _fetch(
        resource,
        f"id = %s AND {_visibility(resource)}",
        [row_id, org_id],
        lock=lock,
    )
    if not records:
        raise _not_found()
    return records[0]


def _require_owned(row, org_id):
    if row["org_id"] != org_id or row["read_only"]:
        raise contract_error(
            403,
            "catalog_read_only",
            "catalogs.errors.read_only",
        )


def _bind_parent(resource, org_id, values):
    if resource is SYSTEMS:
        return

    system_id = values["system_id"]
    if system_id is None and resource is KITS:
        return

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT (org_id IS NULL AND is_global) "
            "FROM public.profile_systems "
            "WHERE id = %s AND (org_id = %s OR "
            "(org_id IS NULL AND is_global))",
            [system_id, org_id],
        )
        parent = cursor.fetchone()
        if parent is None:
            raise _not_found()

        if resource is BEADS:
            cursor.execute(
                "SELECT id FROM public.profile_articles "
                "WHERE id = %s AND system_id = %s "
                "AND role = 'GLAZING_BEAD' "
                "AND (org_id = %s OR (org_id IS NULL AND %s))",
                [
                    values["bead_article_id"],
                    system_id,
                    org_id,
                    parent[0],
                ],
            )
            if cursor.fetchone() is None:
                raise contract_error(
                    400,
                    "invalid_bead_binding",
                    "catalogs.errors.invalid_bead",
                )


def _contents_json(components):
    # Emit qty as a JSON number, preserving Decimal exactly.
    # Strings remain escaped by the standard JSON encoder.
    encoded = []
    for component in components:
        encoded.append(
            '{"sku":'
            + json.dumps(component["sku"])
            + ',"name":'
            + json.dumps(component["name"])
            + ',"qty":'
            + str(component["qty"])
            + ',"unit":'
            + json.dumps(component["unit"])
            + "}"
        )
    return "[" + ",".join(encoded) + "]"


def _parameters(values):
    return [
        _contents_json(value) if name == "contents" else value for name, value in values.items()
    ]


SINGLETON_ROLES = {"FRAME", "SASH", "MULLION_V", "MULLION_H", "INVERSOR", "THRESHOLD"}


def create(resource, org_id, values):
    _bind_parent(resource, org_id, values)
    if resource is ARTICLES and values.get("role") in SINGLETON_ROLES:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT id FROM public.profile_articles "
                f"WHERE system_id = %s AND role = %s AND {_visibility(ARTICLES)}",
                [values["system_id"], values["role"], org_id],
            )
            if cursor.fetchone() is not None:
                raise contract_error(
                    409,
                    "catalog_write_conflict",
                    "catalogs.errors.catalog_constraint_conflict",
                )
    columns = tuple(values)
    placeholders = ["%s::jsonb" if name == "contents" else "%s" for name in columns]
    with connection.cursor() as cursor:
        cursor.execute(
            f"INSERT INTO public.{resource.table} "
            f"(org_id, {', '.join(columns)}) "
            f"VALUES (%s, {', '.join(placeholders)}) RETURNING id",
            [org_id, *_parameters(values)],
        )
        row_id = cursor.fetchone()[0]
    return retrieve(resource, org_id, row_id)


def update(resource, org_id, row_id, values, expected_revision=None):
    _require_owned(retrieve(resource, org_id, row_id), org_id)
    current = retrieve(resource, org_id, row_id, lock=True)
    _require_owned(current, org_id)
    require_revision(current, expected_revision)
    validator = resource.serializer(instance=current, data=values, partial=True)
    if not validator.is_valid():
        raise contract_error(
            400,
            "catalog_validation_error",
            "catalogs.errors.validation",
            error_extra={"fields": validator.errors},
        )
    values = validator.validated_data
    if "system_id" in values and values["system_id"] != current["system_id"]:
        raise contract_error(
            400,
            "catalog_parent_immutable",
            "catalogs.errors.parent_immutable",
        )
    target_role = values.get("role", current.get("role"))
    if resource is ARTICLES and target_role in SINGLETON_ROLES:
        target_system_id = values.get("system_id", current.get("system_id"))
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT id FROM public.profile_articles "
                f"WHERE system_id = %s AND role = %s AND id != %s AND {_visibility(ARTICLES)}",
                [target_system_id, target_role, row_id, org_id],
            )
            if cursor.fetchone() is not None:
                raise contract_error(
                    409,
                    "catalog_write_conflict",
                    "catalogs.errors.catalog_constraint_conflict",
                )
    _bind_parent(resource, org_id, {**current, **values})
    if values:
        assignments = [
            f"{name} = %s::jsonb" if name == "contents" else f"{name} = %s" for name in values
        ]
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE public.{resource.table} SET {', '.join(assignments)} "
                "WHERE id = %s AND org_id = %s",
                [*_parameters(values), row_id, org_id],
            )
            if cursor.rowcount != 1:
                raise contract_error(
                    409, "catalog_write_conflict", "catalogs.errors.catalog_constraint_conflict"
                )
    return retrieve(resource, org_id, row_id)


def delete(resource, org_id, row_id, expected_revision=None):
    _require_owned(retrieve(resource, org_id, row_id), org_id)
    current = retrieve(resource, org_id, row_id, lock=True)
    _require_owned(current, org_id)
    require_revision(current, expected_revision)
    with connection.cursor() as cursor:
        cursor.execute(
            f"DELETE FROM public.{resource.table} WHERE id = %s AND org_id = %s",
            [row_id, org_id],
        )
        if cursor.rowcount != 1:
            raise contract_error(
                409, "catalog_write_conflict", "catalogs.errors.catalog_constraint_conflict"
            )
