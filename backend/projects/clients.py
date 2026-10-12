"""Client registry: org-scoped records the project form picks from.

The project keeps its own client_* fields as the address-of-record snapshot —
sealed documents never read this table. The link exists so reuse stays
consistent and the picker can prefill. Clients are deactivated, never deleted:
historic projects may reference them.
"""

from uuid import uuid4
from psycopg import sql

from django.db import IntegrityError

from authentication.errors import contract_error
from pricing.repository import rows, write
from projects.rut import valid_rut
import re

COLUMNS = (
    "id",
    "name",
    "rut",
    "email",
    "phone",
    "address",
    "giro",
    "comuna",
    "notes",
    "is_active",
    "created_at",
    "updated_at",
    "party_kind",
    "merged_into_id",
)
FIELDS = ("name", "rut", "email", "phone", "address", "giro", "comuna", "notes")


def missing():
    raise contract_error(404, "client_not_found", "El cliente no está disponible.")


def client_row(org_id, client_id, *, lock=False):
    result = rows(
        f"SELECT {','.join(COLUMNS)} FROM public.clients "
        "WHERE id=%s AND org_id=%s" + (" FOR UPDATE" if lock else ""),
        [client_id, org_id],
    )
    if not result:
        missing()
    return result[0]


def _public(row):
    return {
        "id": str(row["id"]),
        **{key: row[key] or "" for key in FIELDS},
        "is_active": row["is_active"],
        "updated_at": row["updated_at"].isoformat(),
        "party_kind": row.get("party_kind", "UNKNOWN"),
        "merged_into_id": str(row["merged_into_id"]) if row.get("merged_into_id") else None,
        "rut_valid": valid_rut(row.get("rut")) if row.get("rut") else None,
    }


def client_public(org_id, client_id):
    result = _public(client_row(org_id, client_id))
    result.update(children(org_id, client_id))
    return result


def list_clients(org_id):
    result = [
        _public(row)
        for row in rows(
            f"SELECT {','.join(COLUMNS)} FROM public.clients "
            "WHERE org_id=%s ORDER BY is_active DESC, name, id LIMIT 500",
            [org_id],
        )
    ]
    child_groups = child_lists(org_id, [item["id"] for item in result])
    return [
        {**item, **child_groups.get(item["id"], {"contacts": [], "addresses": []})}
        for item in result
    ]


def create_client(org_id, actor_id, data):
    validate_rut(data.get("rut"))
    identity_lock(org_id)
    try:
        identity = uuid4()
        rows(
            "INSERT INTO public.clients(id,org_id,created_by,"
            + ",".join(FIELDS)
            + ") VALUES("
            + ",".join(["%s"] * (3 + len(FIELDS)))
            + ") RETURNING id",
            [identity, org_id, actor_id, *[_clean(data.get(key)) for key in FIELDS]],
        )
        if data.get("party_kind"):
            write(
                "UPDATE public.clients SET party_kind=%s WHERE org_id=%s AND id=%s",
                [data["party_kind"], org_id, identity],
            )
        sync_children(org_id, identity, data)
    except IntegrityError as error:
        raise contract_error(
            409, "client_rut_conflict", "Ya existe un cliente con ese RUT."
        ) from error
    return client_public(org_id, identity)


def update_client(org_id, client_id, data):
    identity_lock(org_id)
    row = client_row(org_id, client_id, lock=True)
    editable_client(row)
    if row["updated_at"] != data["expected_updated_at"]:
        raise contract_error(
            409, "stale_edit", "Otra persona guardó cambios. Recarga antes de reemplazarlos."
        )
    values = {key: _clean(data[key]) for key in FIELDS if key in data}
    if "rut" in data and rut_key(data["rut"]) != rut_key(row.get("rut")):
        validate_rut(data["rut"])
    if "party_kind" in data:
        values["party_kind"] = data["party_kind"]
    if "name" in values and not values["name"]:
        raise contract_error(400, "validation_error", "El nombre del cliente es obligatorio.")
    if not values and "contacts" not in data and "addresses" not in data:
        return _public(row)
    try:
        assignments = [f"{key}=%s" for key in values] + ["updated_at=clock_timestamp()"]
        rows(
            "UPDATE public.clients SET "
            + ",".join(assignments)
            + " WHERE id=%s AND org_id=%s RETURNING id",
            [*values.values(), client_id, org_id],
        )
        sync_children(org_id, client_id, data)
    except IntegrityError as error:
        raise contract_error(
            409, "client_rut_conflict", "Ya existe un cliente con ese RUT."
        ) from error
    return client_public(org_id, client_id)


def deactivate_client(org_id, client_id):
    identity_lock(org_id)
    row = client_row(org_id, client_id)
    editable_client(row)
    rows(
        "UPDATE public.clients SET is_active=FALSE,updated_at=clock_timestamp() "
        "WHERE id=%s AND org_id=%s RETURNING id",
        [row["id"], org_id],
    )


def linkable_client(org_id, client_id):
    """A project may only link a client that exists in the same org; the
    record may be inactive (historic projects keep their links) but never
    foreign."""
    editable_client(client_row(org_id, client_id))


def _clean(value):
    text = (value or "").strip()
    return text or None


def identity_lock(org_id):
    rows("SELECT private.lock_client_dossiers()")


def rut_key(value):
    return re.sub(r"[.\s-]", "", value or "").upper()


def validate_rut(value):
    if value and value.strip() and not valid_rut(value):
        raise contract_error(
            400, "client_rut_invalid", "Revisa el RUT y su dígito verificador antes de guardar."
        )


def editable_client(row):
    if row.get("merged_into_id"):
        raise contract_error(
            409,
            "client_already_merged",
            "Esta ficha fue fusionada. Abre la ficha consolidada para editarla.",
        )


def child_lists(org_id, identities):
    result = {str(identity): {"contacts": [], "addresses": []} for identity in identities}
    if not result:
        return result
    for key, table, columns in (
        (
            "contacts",
            "client_contacts",
            "id,client_id,name,contact_role,email,phone,is_primary,is_active,origin_id,updated_at",
        ),
        (
            "addresses",
            "client_addresses",
            "id,client_id,label,address,comuna,is_active,origin_id,updated_at",
        ),
    ):
        for child in rows(
            f"SELECT {columns} FROM public.{table} WHERE org_id=%s AND client_id=ANY(%s::uuid[]) AND is_active ORDER BY created_at,id",
            [org_id, list(result)],
        ):
            identity = str(child.pop("client_id"))
            child["id"] = str(child["id"])
            child["origin_id"] = str(child["origin_id"]) if child["origin_id"] else None
            child["updated_at"] = child["updated_at"].isoformat()
            result[identity][key].append(child)
    return result


def children(org_id, client_id):
    return child_lists(org_id, [client_id])[str(client_id)]


def _sync_child(org_id, client_id, table, incoming, fields):
    owned = {
        str(item["id"])
        for item in rows(
            f"SELECT id FROM public.{table} WHERE org_id=%s AND client_id=%s FOR UPDATE",
            [org_id, client_id],
        )
    }
    provided = [str(item["id"]) for item in incoming if item.get("id")]
    if len(set(provided)) != len(provided) or any(identity not in owned for identity in provided):
        raise contract_error(
            400,
            "client_child_not_available",
            "Un contacto o dirección no pertenece a esta ficha. Recarga antes de guardar.",
        )
    if table == "client_contacts" and sum(bool(item.get("is_primary")) for item in incoming) > 1:
        raise contract_error(
            400, "client_primary_conflict", "Elige un solo contacto principal para el proyecto."
        )
    # Retire first inside the locked transaction, freeing the one-primary slot.
    write(
        f"UPDATE public.{table} SET is_active=false,updated_at=clock_timestamp() WHERE org_id=%s AND client_id=%s",
        [org_id, client_id],
    )
    for item in incoming:
        identity = item.get("id") or uuid4()
        values = [item.get(field, False if field == "is_primary" else "") for field in fields]
        if str(identity) in owned:
            assignments = [sql.SQL("{}=%s").format(sql.Identifier(field)) for field in fields]
            query = sql.SQL(
                "UPDATE public.{} SET {},is_active=true,updated_at=clock_timestamp() WHERE org_id=%s AND client_id=%s AND id=%s"
            ).format(sql.Identifier(table), sql.SQL(",").join(assignments))
            write(query, [*values, org_id, client_id, identity])
        else:
            query = sql.SQL("INSERT INTO public.{}(id,org_id,client_id,{}) VALUES({})").format(
                sql.Identifier(table),
                sql.SQL(",").join(map(sql.Identifier, fields)),
                sql.SQL(",").join([sql.SQL("%s")] * (3 + len(fields))),
            )
            write(query, [identity, org_id, client_id, *values])


def sync_children(org_id, client_id, data):
    if "contacts" in data:
        fields = ("name", "contact_role", "email", "phone", "is_primary")
        _sync_child(org_id, client_id, "client_contacts", data["contacts"], fields)
        primary = next((item for item in data["contacts"] if item.get("is_primary")), None)
        if primary:
            write(
                "UPDATE public.clients SET email=%s,phone=%s WHERE org_id=%s AND id=%s",
                [primary.get("email", ""), primary.get("phone", ""), org_id, client_id],
            )
        else:
            write(
                "UPDATE public.clients SET email='',phone='' WHERE org_id=%s AND id=%s",
                [org_id, client_id],
            )
    elif "email" in data or "phone" in data:
        current = client_row(org_id, client_id)
        principal = rows(
            "SELECT id FROM public.client_contacts WHERE org_id=%s AND client_id=%s AND is_primary AND is_active",
            [org_id, client_id],
        )
        if current.get("email") or current.get("phone"):
            if principal:
                write(
                    "UPDATE public.client_contacts SET email=%s,phone=%s,updated_at=clock_timestamp() WHERE id=%s AND org_id=%s",
                    [
                        current.get("email") or "",
                        current.get("phone") or "",
                        principal[0]["id"],
                        org_id,
                    ],
                )
            else:
                write(
                    "INSERT INTO public.client_contacts(org_id,client_id,email,phone,is_primary) VALUES(%s,%s,%s,%s,true)",
                    [org_id, client_id, current.get("email") or "", current.get("phone") or ""],
                )
        elif principal:
            write(
                "UPDATE public.client_contacts SET is_active=false WHERE id=%s AND org_id=%s",
                [principal[0]["id"], org_id],
            )
    if "addresses" in data:
        _sync_child(
            org_id, client_id, "client_addresses", data["addresses"], ("label", "address", "comuna")
        )


def add_note(org_id, client_id, actor_id, data):
    identity_lock(org_id)
    editable_client(client_row(org_id, client_id, lock=True))
    existing = rows(
        "SELECT id,client_id,body,created_by FROM public.client_notes WHERE org_id=%s AND operation_key=%s",
        [org_id, data["operation_key"]],
    )
    if existing:
        if (
            str(existing[0]["client_id"]) != str(client_id)
            or existing[0]["body"] != data["body"]
            or str(existing[0]["created_by"]) != str(actor_id)
        ):
            raise contract_error(
                409,
                "client_note_key_conflict",
                "Este registro ya guardó otra nota. Recarga antes de intentarlo.",
            )
        identity = existing[0]["id"]
    else:
        identity = uuid4()
        write(
            "INSERT INTO public.client_notes(id,org_id,client_id,operation_key,body) VALUES(%s,%s,%s,%s,%s)",
            [identity, org_id, client_id, data["operation_key"], data["body"]],
        )
    return rows(
        "SELECT id,body,author_label,created_at,is_legacy,source_updated_at FROM public.client_notes WHERE org_id=%s AND id=%s",
        [org_id, identity],
    )[0]


def merge_preview(org_id, source_id, target_id):
    source, target = client_public(org_id, source_id), client_public(org_id, target_id)
    blockers = []
    if str(source_id) == str(target_id):
        blockers.append("Elige una ficha distinta como destino.")
    if source.get("merged_into_id") or target.get("merged_into_id"):
        blockers.append("Una ficha ya fue fusionada. Abre su destino antes de continuar.")
    if (
        rut_key(source["rut"])
        and rut_key(target["rut"])
        and rut_key(source["rut"]) != rut_key(target["rut"])
    ):
        blockers.append(
            "Los RUT son distintos. Verifica la identidad del cliente antes de fusionar."
        )
    adopted = [
        {"field": key, "before": target.get(key), "after": source.get(key)}
        for key in ("rut", "email", "phone", "address", "giro", "comuna")
        if not (target.get(key) or "").strip() and (source.get(key) or "").strip()
    ]
    if target["party_kind"] == "UNKNOWN" and source["party_kind"] != "UNKNOWN":
        adopted.append(
            {"field": "party_kind", "before": target["party_kind"], "after": source["party_kind"]}
        )
    contacts = [
        item
        for item in source["contacts"]
        if not any(
            all(other[key] == item[key] for key in ("name", "contact_role", "email", "phone"))
            for other in target["contacts"]
        )
    ]
    addresses = [
        item
        for item in source["addresses"]
        if not any(
            all(other[key] == item[key] for key in ("label", "address", "comuna"))
            for other in target["addresses"]
        )
    ]
    return {
        "source": source,
        "target": target,
        "adopted_fields": adopted,
        "added_contacts": contacts,
        "added_addresses": addresses,
        "blockers": blockers,
        "consequence": "La ficha de origen quedará cerrada y su historia se consultará desde el destino. Se conservan los proyectos y documentos emitidos; la fusión queda registrada con su motivo.",
    }


def merge_client(org_id, source_id, data):
    if data.get("confirmed") is not True:
        raise contract_error(
            400,
            "client_merge_confirmation_required",
            "Revisa el efecto de la fusión antes de confirmar.",
        )
    preview = merge_preview(org_id, source_id, data["target_id"])
    if preview["blockers"]:
        raise contract_error(409, "client_merge_blocked", preview["blockers"][0])
    result = rows(
        "SELECT private.merge_clients(%s,%s,%s,%s,%s,%s) AS id",
        [
            org_id,
            source_id,
            data["target_id"],
            data["expected_source_updated_at"],
            data["expected_target_updated_at"],
            data["reason"],
        ],
    )
    return client_public(org_id, result[0]["id"])
