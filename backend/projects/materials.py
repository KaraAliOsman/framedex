"""Materials and draft cut of a work, read from the saved engine results (v1 07).

Nothing here computes geometry, lengths or bars: the per-window EngineResult
saved with each position is the source, and the cut draft is the engine's
`optimize_cut` over the catalog's declared stock and cutting profile. The
presentation separates four things the workshop reads differently:

- consumption (what the design uses: pieces, metres, m², kits),
- cut (bars, sequence, angles — only with declared stock and profile),
- purchase presentation (whole bars to buy, from the same optimisation),
- stock (not read here; the draft says it assumes new bars).

A missing authority is reported as its cause and the action that resolves
it; zero is never used for an unknown value.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from dekopen_engine.cutting import (
    AmbiguousCuttingProfile,
    AmbiguousStockAuthority,
    InvalidCutContract,
    MissingCuttingProfile,
    MissingStockAuthority,
    optimize_cut,
    pieces_from_result,
)
from dekopen_engine.models import EngineResult
from engine_api.cutting_repository import CuttingRepository
from pricing.repository import json_text, rows
from pricing.service import decoded

THOUSAND = Decimal("1000")

ROLE_ES = {
    "FRAME": "Marco", "SASH": "Hoja", "MULLION_V": "Montante vertical", "MULLION_H": "Travesaño",
    "INVERSOR": "Inversor", "GLAZING_BEAD": "Junquillo", "COUPLER": "Acople", "ADDITIONAL": "Adicional",
    "THRESHOLD": "Umbral", "CHANNEL": "Canal", "SLIDING_SASH": "Hoja corredera", "INTERLOCK": "Traslapo",
    "RAIL": "Riel", "DOOR_SASH": "Hoja de puerta", "FRAME_EXTENSION": "Ensanche", "SILL": "Alféizar",
    "COVER_TRIM": "Tapajunta", "PLINTH": "Zócalo",
}
FINISH_ES = {"WHITE": "Blanco", "FOILED": "Foliado"}


def _role(value: object) -> str:
    name = str(value or "").rsplit(".", 1)[-1]
    return ROLE_ES.get(name, name.replace("_", " ").capitalize())


def _positions(org_id: UUID, project_id: UUID) -> list[dict]:
    found = rows(
        "SELECT id, position_index, location_tag, quantity, system_id, color_interior, bom_snapshot, updated_at "
        "FROM public.project_positions WHERE project_id=%s AND org_id=%s ORDER BY display_order, position_index",
        [str(project_id), str(org_id)],
    )
    out = []
    for row in found:
        stored = decoded(row["bom_snapshot"])
        payload = {key: value for key, value in (stored or {}).items() if key != "calculation_hash"}
        result = EngineResult.model_validate_json(json_text(payload))
        color = stored["finish"]["combination"]["code"] if isinstance(stored, dict) and stored.get("finish") else row["color_interior"]
        out.append({**row, "result": result, "color": str(color)})
    return out


def _profile_names(org_id: UUID, systems: set[str], skus: set[str]) -> dict[tuple[str, str], str]:
    if not systems or not skus:
        return {}
    found = rows(
        "SELECT system_id, sku, name, org_id FROM public.profile_articles "
        "WHERE system_id = ANY(%s::uuid[]) AND sku = ANY(%s) AND (org_id IS NULL OR org_id=%s)",
        [sorted(systems), sorted(skus), str(org_id)],
    )
    names: dict[tuple[str, str], str] = {}
    # The organisation's own article wins over the shared catalog's.
    for row in sorted(found, key=lambda item: item["org_id"] is not None):
        names[(str(row["system_id"]), row["sku"])] = row["name"]
    return names


def _article_titles(org_id: UUID, names: dict, systems: set[str]) -> dict[str, str]:
    """Workshop name of each cut SKU: profile articles and their steel bars."""
    titles = {sku: name for (_, sku), name in names.items() if name}
    if systems:
        for row in rows("SELECT sku, commercial_sku, name FROM public.reinforcement_articles "
                        "WHERE system_id = ANY(%s::uuid[]) AND (org_id IS NULL OR org_id=%s) AND is_active",
                        [sorted(systems), str(org_id)]):
            for sku in (row["sku"], row["commercial_sku"]):
                if sku and row["name"]:
                    titles.setdefault(sku, row["name"])
    return titles


def _label(position: dict) -> str:
    return f'V{position["position_index"]}' + (f' · {position["location_tag"]}' if position.get("location_tag") else "")


def _add(groups: dict, kind: str, key: tuple, base: dict, *, count: int, length_mm: Decimal | None = None,
         area_m2: Decimal | None = None, window: str | None = None) -> None:
    entry = groups[kind].setdefault(key, {**base, "count": 0, "length_mm": Decimal("0") if length_mm is not None else None,
                                          "area_m2": Decimal("0") if area_m2 is not None else None, "windows": []})
    entry["count"] += count
    if length_mm is not None:
        entry["length_mm"] += length_mm
    if area_m2 is not None:
        entry["area_m2"] += area_m2
    if window and window not in entry["windows"]:
        entry["windows"].append(window)


def _empty() -> dict:
    return {"profiles": {}, "reinforcements": {}, "glass": {}, "hardware": {}, "other": {}}


def _collect(groups: dict, position: dict, names: dict, *, multiplier: int, window: str | None) -> None:
    result: EngineResult = position["result"]
    system = str(position["system_id"])
    for cut in result.profile_cuts:
        color = cut.stock_color or position["color"]
        name = names.get((system, cut.sku)) or f"Perfil {_role(cut.role).lower()}"
        _add(groups, "profiles", (cut.sku, color), {"reference": cut.commercial_sku or cut.sku, "name": name,
             "finish": FINISH_ES.get(color, color), "unit": "m"},
             count=cut.qty * multiplier, length_mm=cut.length_mm * cut.qty * multiplier, window=window)
    for steel in result.reinforcements:
        sku = steel.reinforcement_sku or f"Refuerzo de {steel.parent_profile_sku}"
        _add(groups, "reinforcements", (sku,), {"reference": steel.reinforcement_sku or "Según perfil " + steel.parent_profile_sku,
             "name": f"Refuerzo de acero · {_role(steel.role).lower()}", "finish": None, "unit": "m"},
             count=steel.qty * multiplier, length_mm=steel.length_mm * steel.qty * multiplier, window=window)
    for glass in result.glasses:
        spec = glass.glass_spec or "Vidrio sin composición declarada"
        _add(groups, "glass", (glass.article_sku or spec,), {"reference": glass.article_sku or spec, "name": f"Vidrio {spec}",
             "finish": None, "unit": "m²"}, count=multiplier, area_m2=glass.area_m2 * multiplier, window=window)
    for panel in result.panels:
        _add(groups, "other", ("PANEL", panel.sku), {"reference": panel.sku, "name": panel.name, "finish": None, "unit": "m²"},
             count=multiplier, area_m2=panel.area_m2 * multiplier, window=window)
    for kit in result.hardware_items:
        _add(groups, "hardware", (kit.kit_sku,), {"reference": kit.kit_sku, "name": kit.name, "finish": None, "unit": "kit"},
             count=kit.qty * multiplier, window=window)
    for fitting in result.fittings:
        _add(groups, "other", ("FITTING", fitting.sku), {"reference": fitting.sku, "name": fitting.kind.replace("_", " ").capitalize(),
             "finish": None, "unit": "un."}, count=fitting.qty * multiplier, window=window)


def _rows(groups: dict) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for kind, entries in groups.items():
        items = []
        for entry in entries.values():
            items.append({
                **entry,
                # Metres keep the mm precision: 3 decimals, never rounded up here.
                "length_m": None if entry["length_mm"] is None else str((entry["length_mm"] / THOUSAND).quantize(Decimal("0.001"))),
                "length_mm": None if entry["length_mm"] is None else str(entry["length_mm"]),
                "area_m2": None if entry["area_m2"] is None else str(entry["area_m2"].quantize(Decimal("0.0001"))),
            })
        out[kind] = sorted(items, key=lambda item: (item["name"], item["reference"]))
    return out


def project_materials(org_id: UUID, project_id: UUID) -> dict:
    """Consumption per window and consolidated, straight from the saved results."""
    positions = _positions(org_id, project_id)
    names = _profile_names(org_id, {str(p["system_id"]) for p in positions},
                           {cut.sku for p in positions for cut in p["result"].profile_cuts})
    consolidated = _empty()
    windows = []
    for position in positions:
        own = _empty()
        _collect(own, position, names, multiplier=1, window=None)
        _collect(consolidated, position, names, multiplier=int(position["quantity"]), window=_label(position))
        windows.append({
            "position_id": str(position["id"]),
            "label": _label(position),
            "quantity": int(position["quantity"]),
            "materials": _rows(own),
        })
    return {
        "consolidated": _rows(consolidated),
        "windows": windows,
        "freshness": _freshness(org_id, project_id, positions),
    }


DESIGN_FIELDS = ("quantity", "system_id", "width_mm", "height_mm", "color_interior", "color_exterior",
                 "parametric_tree")


def _design(item: dict) -> tuple:
    def value(key):
        found = item.get(key)
        if key == "parametric_tree":
            return json_text(decoded(found) if isinstance(found, str) else found)
        if key in ("width_mm", "height_mm") and found is not None:
            return str(Decimal(str(found)).normalize())
        return str(found)
    return tuple(value(key) for key in DESIGN_FIELDS)


def _freshness(org_id: UUID, project_id: UUID, positions: list[dict]) -> dict:
    """Outputs of an issued revision stay historical when the design changed later.

    The design is what the windows are — measures, series, colors and the
    parametric tree — compared with what the revision sealed. Applying the
    sealed prices or renaming a window is not a design change.
    """
    from documents.repository import documentary_backend
    with documentary_backend():
        latest = rows(
            "SELECT id, revision_code, snapshot_json::text AS snapshot FROM public.project_versions "
            "WHERE project_id=%s AND org_id=%s ORDER BY emitted_at DESC, id DESC LIMIT 1",
            [str(project_id), str(org_id)],
        )
    if not latest:
        return {"latest_revision": None, "design_changed": False}
    sealed = {str(item["id"]): _design(item) for item in decoded(latest[0]["snapshot"]).get("positions", [])}
    current = {str(item["id"]): _design(item) for item in rows(
        "SELECT id," + ",".join(DESIGN_FIELDS[:-1]) + ",parametric_tree::text AS parametric_tree "
        "FROM public.project_positions WHERE project_id=%s AND org_id=%s", [str(project_id), str(org_id)])}
    return {"latest_revision": latest[0]["revision_code"], "latest_version_id": str(latest[0]["id"]),
            "design_changed": sealed != current}


def cut_draft(org_id: UUID, project_id: UUID) -> dict:
    """The engine's cut over the whole work with the catalog's declared stock
    and the company's cutting profile — a draft to read, never a released order.
    Missing authority returns every cause at once and no partial plan."""
    positions = _positions(org_id, project_id)
    repository = CuttingRepository()
    missing: list[dict] = []
    stocks: dict[str, object] = {}
    pieces = []
    labels = {str(position["id"]): _label(position) for position in positions}
    names = _profile_names(org_id, {str(p["system_id"]) for p in positions},
                           {cut.sku for p in positions for cut in p["result"].profile_cuts})
    for position in positions:
        result: EngineResult = position["result"]
        system = UUID(str(position["system_id"]))
        from catalogs.use_levels import series_use
        usage = series_use(org_id, system, result=result)
        gate = next(item for item in usage["levels"] if item["level"] == "MANUFACTURABLE")
        if not gate["ok"]:
            missing.extend({"cause": item["action"], "action": item["action"],
                "path": f"/catalogs/systems?system={system}", "pending": item} for item in gate["pending"])
            continue
        defaults: dict[str, str] = {}
        ok = True
        for sku in sorted({cut.sku for cut in result.profile_cuts}):
            try:
                stock = repository.profile_stock(system, org_id, sku, position["color"])
                stocks[stock.stock_authority_id] = stock
            except (MissingStockAuthority, AmbiguousStockAuthority) as error:
                ok = False
                missing.append(_missing_stock(names.get((str(system), sku)) or sku, sku, error, labels[str(position["id"])]))
        for parent, requested in sorted({(cut.parent_profile_sku, cut.reinforcement_sku) for cut in result.reinforcements},
                                        key=lambda item: (item[0], item[1] or "")):
            try:
                stock, _ = repository.reinforcement_stock(system, org_id, parent, requested, position["color"])
                stocks[stock.stock_authority_id] = stock
                if requested is None:
                    defaults[parent] = stock.workshop_sku
            except (MissingStockAuthority, AmbiguousStockAuthority) as error:
                ok = False
                missing.append(_missing_stock(f"Refuerzo de {parent}", requested or parent, error, labels[str(position["id"])]))
        if not ok:
            continue
        per_unit = pieces_from_result(result, color=position["color"], source_position_id=str(position["id"]),
                                      reinforcement_skus=defaults)
        pieces += [piece.model_copy(update={"unit_index": unit}) for unit in range(1, int(position["quantity"]) + 1)
                   for piece in per_unit]
    try:
        profile = repository.cutting_profile(org_id)
    except MissingCuttingProfile:
        profile = None
        missing.append({"cause": "La empresa no tiene un perfil de corte por defecto (disco y despuntes).",
                        "action": "Configura el perfil de corte en Empresa › Taller.", "path": "/settings/general?section=production"})
    except AmbiguousCuttingProfile:
        profile = None
        missing.append({"cause": "Hay más de un perfil de corte marcado por defecto.",
                        "action": "Deja uno solo por defecto en Empresa › Taller.", "path": "/settings/general?section=production"})
    if missing or profile is None:
        return {"state": "MISSING", "missing": missing}
    if not pieces:
        return {"state": "EMPTY", "missing": []}
    try:
        plan = optimize_cut(pieces, [stocks[key] for key in sorted(stocks)], profile, strategy="fast")
    except InvalidCutContract as error:
        return {"state": "MISSING", "missing": [{
            "cause": "Una pieza no cabe en la barra declarada o el corte no es válido con el perfil de corte actual.",
            "action": "Revisa el largo comercial del perfil y los despuntes en Catálogos y Empresa › Taller.",
            "path": "/catalogs/systems", "detail": type(error).__name__}]}
    data = plan.model_dump(mode="json")
    titles = _article_titles(org_id, names, {str(p["system_id"]) for p in positions})
    for bar in data["workshop_cut_plan"]:
        for cut in bar["cuts"]:
            cut["window"] = labels.get(str(cut.get("source_position_id")), "")
            role = _role(cut.get("role"))
            cut["role_label"] = f"Acero de {role.lower()}" if cut.get("source_kind") == "REINFORCEMENT" else role
        skus = {cut.get("workshop_sku") for cut in bar["cuts"]}
        bar["name"] = next((titles[sku] for sku in sorted(skus, key=str) if sku in titles), None)
    for line in data["purchase_list"]:
        line["name"] = next((bar["name"] for bar in data["workshop_cut_plan"]
                             if bar["commercial_sku"] == line["commercial_sku"] and bar.get("name")), None)
    return {
        "state": "READY",
        "missing": [],
        "profile": {"code": profile.code, "kerf_mm": str(profile.kerf_mm), "head_trim_mm": str(profile.head_trim_mm),
                    "tail_trim_mm": str(profile.tail_trim_mm)},
        # The draft assumes new bars from the catalog; stock and remnants are
        # applied when the released order is optimised.
        "stock_source": "NEW_BARS",
        "bars": data["workshop_cut_plan"],
        "purchase": data["purchase_list"],
        "unplaced": data["unplaced"],
        "metrics": data["metrics"],
    }


def _missing_stock(name: str, sku: str, error: Exception, window: str) -> dict:
    ambiguous = isinstance(error, AmbiguousStockAuthority)
    return {
        "cause": (f"{name} ({sku}) tiene más de una barra comercial posible para este acabado." if ambiguous
                  else f"{name} ({sku}) no tiene barra comercial declarada para este acabado."),
        "action": "Declara una sola barra (largo comercial y referencia de compra) en Catálogos." if ambiguous
                  else "Declara su largo comercial y su referencia de compra en Catálogos.",
        "path": "/catalogs/systems",
        "window": window,
    }
