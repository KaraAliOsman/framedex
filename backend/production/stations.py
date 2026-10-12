"""Tenant-bound, explicit workstation preference. It never grants a domain role."""

from uuid import UUID

from documents.repository import DocumentaryError, one, rows


def operator_station(*, org_id: UUID, actor_id: UUID) -> dict:
    from production.service import _CENTER_KIND_FOR_STATION, _STEP_LABELS

    centers = rows(
        "SELECT kind FROM public.work_centers WHERE org_id = %s AND active",
        [str(org_id)],
    )
    kinds = {str(center["kind"]) for center in centers}
    available = [
        {"code": code, "label": _STEP_LABELS[code]}
        for code, kind in _CENTER_KIND_FOR_STATION.items() if kind in kinds
    ]
    selected = rows(
        "SELECT station_code FROM public.production_operator_stations "
        "WHERE org_id = %s AND user_id = %s",
        [str(org_id), str(actor_id)],
    )
    return {
        "selected_code": selected[0]["station_code"] if selected else None,
        "stations": available,
    }


def select_station(*, org_id: UUID, actor_id: UUID, station_code: str) -> dict:
    available = operator_station(org_id=org_id, actor_id=actor_id)
    if station_code not in {station["code"] for station in available["stations"]}:
        raise DocumentaryError(
            "operator_station_unavailable",
            detail="Esta estación no tiene un puesto activo. Pide al jefe de taller que lo habilite.",
        )
    one(
        "INSERT INTO public.production_operator_stations(org_id, user_id, station_code) "
        "VALUES (%s, %s, %s) ON CONFLICT (org_id, user_id) DO UPDATE "
        "SET station_code = EXCLUDED.station_code, updated_at = now() RETURNING station_code",
        [str(org_id), str(actor_id), station_code],
    )
    return {**available, "selected_code": station_code}
