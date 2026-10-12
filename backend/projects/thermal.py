"""Tenant-scoped thermal authority, pure-engine assessment and sealed reports."""

from copy import deepcopy
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from authentication.errors import contract_error
from authentication.rls import catalog_backend
from catalogs.provenance import evidence_matches
from dekopen_engine.thermal import ThermalAuthority, ThermalProjectInput, assess_project, calculate_uw, fingerprint, glass_binding, thermal_geometry
from documents.repository import DocumentaryError, documentary_backend
from engine_api.repository import SystemParamsRepository
from pricing.repository import json_text, rows
from projects import service


def today():
    return datetime.now(ZoneInfo("America/Santiago")).date()


def catalog_fingerprint(params):
    value = params.model_dump(mode="json")
    value.pop("compatible_opening_systems", None)
    return fingerprint(value)


def _system(org_id, system_id):
    with catalog_backend():
        found = rows("SELECT * FROM public.profile_systems WHERE id=%s AND "
                     "(org_id=%s OR (org_id IS NULL AND is_global))", [system_id, org_id])
    if not found:
        raise contract_error(404, "catalog_system_not_found", "El sistema no está disponible para tu organización.")
    return found[0]


def _authority(row):
    payload = {key: row.get(key) for key in ThermalAuthority.model_fields}
    payload["id"] = str(row["id"])
    for key in ("reviewed_at", "reviewed_by"):
        payload[key] = str(payload[key]) if payload[key] is not None else None
    return ThermalAuthority.model_validate_json(json_text(payload))


def authorities(org_id, system_id):
    return tuple(_authority(row) for row in rows("SELECT * FROM public.catalog_thermal_authorities WHERE system_id=%s "
        "AND (org_id=%s OR org_id IS NULL) ORDER BY declared_at,id", [system_id, org_id]))


def authority_public(authority, org_id):
    value = authority.model_dump(mode="json")
    if authority.reviewed_by:
        labels = rows("SELECT private.catalog_reviewer_label(%s,%s) AS label", [authority.reviewed_by, org_id])
        value["reviewer_label"] = labels[0]["label"] if labels else "Revisor técnico"
    else:
        value["reviewer_label"] = None
    return value


def catalog_reports(org_id, system_id):
    system = _system(org_id, system_id)
    params = SystemParamsRepository().load_visible(UUID(str(system_id)), org_id)
    from catalogs.glass import load_products
    glasses = []
    for row in load_products(system_id, org_id):
        product = row.get("resolved_product")
        if product:
            binding, spacer = glass_binding(product)
            glasses.append({"sku": row["technical_sku"], "name": product.name, "fingerprint": binding,
                            "spacer": spacer, "synthetic": product.synthetic})
    return {"is_demo": bool(system["is_demo"]), "catalog_fingerprint": catalog_fingerprint(params),
        "profiles": [{"sku": row["sku"], "name": row["name"], "role": row["role"]} for row in rows(
            "SELECT DISTINCT ON(sku) sku,name,role FROM public.profile_articles WHERE system_id=%s "
            "AND (org_id=%s OR org_id IS NULL) ORDER BY sku,org_id NULLS LAST", [system_id, org_id])],
        "glasses": glasses,
        "specimens": [{"id": str(r["id"]), "label": f'{r["code"]} · posición {r["position_index"]} · {r["location_tag"]}'}
            for r in rows("SELECT p.id,p.position_index,p.location_tag,j.code FROM public.project_positions p "
                "JOIN public.projects j ON j.id=p.project_id AND j.org_id=p.org_id "
                "WHERE p.org_id=%s AND p.system_id=%s ORDER BY p.updated_at DESC,p.id LIMIT 200", [org_id,system_id])],
        "items": [authority_public(a, org_id) for a in authorities(org_id, system_id)]}


def declare_report(org_id, system_id, actor_id, values):
    values = dict(values)
    specimen_id = values.pop("source_position_id", None)
    system = _system(org_id, system_id)
    params = SystemParamsRepository().load_visible(UUID(str(system_id)), org_id)
    payload = {**values, "catalog_fingerprint": catalog_fingerprint(params),
               "synthetic": bool(values.get("synthetic") or system["is_demo"] or system["data_provenance"] == "SEED_SYNTHETIC")}
    if values["kind"] == "PERFORMANCE":
        if not specimen_id:
            raise contract_error(422, "thermal_specimen_required", "Elige la posición que reproduce exactamente el producto ensayado.")
        specimen = service.position_row(org_id, specimen_id)
        geometry, reason = _position_geometry(org_id, specimen, params=params)
        if str(specimen["system_id"]) != str(system_id) or geometry is None or geometry.reasons:
            raise contract_error(422, "thermal_specimen_invalid", reason or "El producto ensayado necesita geometría y composición evaluables de este sistema.")
        payload["construction_fingerprint"] = geometry.construction_fingerprint
    if values.get("glass_sku"):
        from catalogs.glass import load_products
        found = [row for row in load_products(system_id, org_id) if row["technical_sku"] == values["glass_sku"] and row.get("resolved_product")]
        if len(found) != 1:
            raise contract_error(422, "thermal_glass_missing", "El vidrio necesita una composición única vigente en el catálogo.")
        product = found[0]["resolved_product"]
        payload["glass_fingerprint"], spacer = glass_binding(product)
        payload["synthetic"] = payload["synthetic"] or product.synthetic
        if values["kind"] == "SPACER" and values.get("spacer_code") != spacer:
            raise contract_error(422, "thermal_spacer_mismatch", "El separador del informe no coincide con la composición del termopanel.")
    else:
        payload["glass_fingerprint"] = None
    known = {row["sku"] for row in rows("SELECT sku FROM public.profile_articles WHERE system_id=%s "
        "AND (org_id=%s OR org_id IS NULL)", [system_id, org_id])}
    if not set(values.get("profile_skus", [])) <= known:
        raise contract_error(422, "thermal_profiles_invalid", "El informe contiene perfiles que no existen en esta combinación del catálogo.")
    try:
        model = ThermalAuthority.model_validate_json(json_text(payload))
    except ValueError as error:
        raise contract_error(400, "thermal_report_invalid", "Revisa los valores, fechas y alcance del informe térmico.") from error
    data = model.model_dump(mode="python", exclude={"id", "reviewed_by", "reviewed_at", "review_state"})
    fields = list(data)
    with catalog_backend():
        found = rows(f"INSERT INTO public.catalog_thermal_authorities ({','.join(fields)},org_id,system_id,declared_by) "
            f"VALUES ({','.join(['%s']*(len(fields)+3))}) RETURNING *",
            [*[list(value) if isinstance(value, tuple) else value for value in data.values()], org_id, system_id, actor_id])
    return authority_public(_authority(found[0]), org_id)


def review_report(org_id, system_id, report_id, actor_id, state):
    _system(org_id, system_id)
    expected = "REVIEWED" if state == "REVOKED" else "PENDING"
    with catalog_backend():
        found = rows("UPDATE public.catalog_thermal_authorities SET review_state=%s,reviewed_by=%s,reviewed_at=clock_timestamp() "
            "WHERE id=%s AND org_id=%s AND system_id=%s AND review_state=%s RETURNING *",
            [state, actor_id, report_id, org_id, system_id, expected])
    if not found:
        raise contract_error(409, "thermal_review_conflict", "El informe ya cambió de estado o no pertenece a tu organización. Recarga sus fuentes.")
    return authority_public(_authority(found[0]), org_id)


def geometry_authority(org_id, system_id, geometry, color):
    if geometry is None:
        return False
    system = _system(org_id, system_id)
    with catalog_backend():
        profiles = rows("SELECT DISTINCT ON(sku) * FROM public.profile_articles WHERE system_id=%s AND sku=ANY(%s::text[]) "
                       "AND (org_id=%s OR org_id IS NULL) ORDER BY sku,org_id NULLS LAST", [system_id, list(geometry.profile_skus), org_id])
    if {row["sku"] for row in profiles} != set(geometry.profile_skus):
        return False
    if any(row.get("data_provenance") == "SEED_SYNTHETIC" for row in profiles):
        return False
    with catalog_backend():
        evidence = rows("SELECT * FROM public.catalog_parameter_evidence WHERE (org_id=%s OR org_id IS NULL) "
                        "AND review_state='REVIEWED'", [org_id])
    def covered(table, row, field):
        return any(e["authority_table"] == table and str(e["row_id"]) == str(row["id"])
            and e["field_name"] == field and e.get("reviewed_by") and e.get("reviewed_at")
            and e.get("extraction_method") != "HUMAN_CORRECTION"
            and (e.get("source_page") or e.get("source_url") or e.get("source_ref"))
            and evidence_matches(row, e) for e in evidence)
    required = ["rebate_depth_mm", "glass_clearance_white_mm" if color == "WHITE" else "glass_clearance_foil_mm"]
    if set(geometry.opening_types) != {"FIXED"}:
        required.append("sash_overlap_mm")
    for key in ("sliding_parameters", "paired_leaf_rule", "opening_capabilities"):
        if system.get(key):
            required.append(key)
    return all(covered("profile_systems", system, field) for field in required) and all(
        covered("profile_articles", row, "face_width_mm") for row in profiles)


def _position_geometry(org_id, position, *, calculations=None, params=None):
    from documents.service import _position_calculations
    system_id = UUID(str(position["system_id"]))
    params = params or SystemParamsRepository().load_visible(system_id, org_id)
    shape_reason = None
    try:
        if calculations is None:
            tree = service.decoded(position["parametric_tree"])
            from catalogs.glass import load_products
            products = {row["technical_sku"]: row["resolved_product"] for row in load_products(system_id, org_id)}
            tree = deepcopy(tree)
            def hydrate(node):
                product = products.get(node.get("glass_article_sku"))
                if not node.get("glass_product") and product:
                    node["glass_product"] = product.model_dump(mode="json")
                for child in node.get("children", []):
                    hydrate(child)
            if tree.get("version") == "product-v2":
                for module in tree["assembly"]["modules"]:
                    if module.get("tree"):
                        hydrate(module["tree"])
            else:
                hydrate(tree)
            calculations, _ = _position_calculations(tree=tree, width_mm=position["width_mm"], height_mm=position["height_mm"],
                color=position["color_interior"], params=params, system_id=system_id, org_id=org_id)
        # An area method cannot replace a coupled assembly's joint authority.
        if len(calculations) != 1:
            geometry = None
            shape_reason = "El conjunto necesita un método de área y puente térmico del acople; no se aproxima por su caja."
        else:
            geometry = thermal_geometry(calculations[0][1])
    except (ValueError, DocumentaryError):
        geometry = None
        shape_reason = "La geometría guardada necesita una evaluación exacta y vigente del motor."
    return geometry, shape_reason


def position_metric(org_id, position, *, calculations=None, params=None, as_of=None):
    system_id = UUID(str(position["system_id"]))
    params = params or SystemParamsRepository().load_visible(system_id, org_id)
    system = _system(org_id, system_id)
    geometry, shape_reason = _position_geometry(org_id, position, calculations=calculations, params=params)
    metric = calculate_uw(geometry, authorities(org_id, system_id),
        catalog_fingerprint=catalog_fingerprint(params), as_of=as_of or today(),
        synthetic=bool(system["is_demo"] or system["data_provenance"] == "SEED_SYNTHETIC"),
        geometry_authoritative=geometry_authority(org_id, system_id, geometry, position["color_interior"]))
    if shape_reason:
        metric["missing"].append(shape_reason)
    # Geometry owns the window area even when the thermal inputs are absent.
    area = metric["trace"]["area_m2"] if metric["trace"] else None
    return {"position_id": str(position["id"]), "position_index": position["position_index"],
        "location_tag": position["location_tag"], "quantity": position["quantity"],
        "window_area_m2": area, "thermal": metric}


def project_inputs(org_id, project):
    found = rows("SELECT * FROM public.project_thermal_inputs WHERE project_id=%s AND org_id=%s AND revision_code=%s",
                 [project["id"], org_id, project["current_revision"]])
    if not found:
        return ThermalProjectInput(), None
    return ThermalProjectInput.model_validate_json(json_text(service.decoded(found[0]["inputs"]))), found[0]["updated_at"]


def _live_positions(org_id, project_id):
    return rows(f"SELECT {','.join(service.POSITION_COLUMNS)} FROM public.project_positions "
                "WHERE project_id=%s AND org_id=%s ORDER BY position_index", [project_id, org_id])


def project_report(org_id, project_id, *, sealed=True):
    project = service.project_row(org_id, project_id)
    if sealed:
        with documentary_backend():
            versions = rows("SELECT snapshot_json->'thermal' AS thermal FROM public.project_versions WHERE "
                "project_id=%s AND org_id=%s AND revision_code=%s",
                [project_id, org_id, project["current_revision"]])
        if versions:
            thermal = service.decoded(versions[0]["thermal"])
            if thermal:
                return {**thermal, "sealed": True, "updated_at": None}
            return {"inputs": ThermalProjectInput().model_dump(mode="json"), "updated_at": None, "sealed": True,
                "assessment": {**assess_project(ThermalProjectInput(), []), "causes": ["Esta revisión histórica no contiene un informe térmico sellado. Inicia una revisión para agregarlo."]}}
    inputs, updated_at = project_inputs(org_id, project)
    positions = [position_metric(org_id, position) for position in _live_positions(org_id, project_id)]
    return {"inputs": inputs.model_dump(mode="json"), "updated_at": updated_at, "sealed": False,
            "assessment": assess_project(inputs, positions)}


def save_inputs(org_id, project_id, actor_id, values, expected_updated_at):
    project = service.project_row(org_id, project_id, lock=True)
    if project["status"] != "DRAFT":
        raise contract_error(409, "thermal_revision_required", "Inicia una revisión para cambiar el informe térmico emitido.")
    with documentary_backend():
        versions = rows("SELECT id FROM public.project_versions WHERE project_id=%s AND org_id=%s AND revision_code=%s",
                       [project_id, org_id, project["current_revision"]])
        if versions:
            raise contract_error(409, "thermal_revision_required", "Inicia una revisión para cambiar el informe térmico sellado.")
        _, timestamp = project_inputs(org_id, project)
        if timestamp != expected_updated_at:
            raise contract_error(409, "thermal_inputs_stale", "Otra persona cambió los datos térmicos. Recarga antes de guardar.")
        try:
            inputs = ThermalProjectInput.model_validate_json(json_text(values))
        except ValueError as error:
            raise contract_error(400, "thermal_inputs_invalid", "Revisa la zona, la fuente y las superficies de muro declaradas.") from error
        ids = {str(p["id"]) for p in _live_positions(org_id, project_id)}
        if not {p.position_id for p in inputs.positions} <= ids:
            raise contract_error(400, "thermal_position_invalid", "Una orientación no corresponde a las posiciones de este proyecto.")
        rows("INSERT INTO public.project_thermal_inputs(org_id,project_id,revision_code,inputs,declared_by) VALUES(%s,%s,%s,%s::jsonb,%s) "
            "ON CONFLICT(project_id,revision_code) DO UPDATE SET inputs=EXCLUDED.inputs,declared_by=EXCLUDED.declared_by,updated_at=clock_timestamp() RETURNING id",
            [org_id, project_id, project["current_revision"], inputs.model_dump_json(), actor_id])
    return project_report(org_id, project_id)


def alternatives(org_id, project_id, position_id):
    """Exhaustive finite visible catalog search, engine-valid, scoped and priced.

    Dimensions/opening/finish/quantity are preserved. Other positions govern
    their orientation's worst-U threshold too. No candidate applies itself.
    """
    from dekopen_engine.finishes import finish_selling_delta
    from decimal import Decimal
    from dekopen_engine.design_operations import apply_operations
    from projects.ops_registry import catalog_for, calculate_product, design_from_product, product_from_position, sale_price
    from authentication.errors import ContractAPIException
    from engine_api.adapter import InvalidEngineRequest, UnsupportedEngineContract
    from engine_api.repository import UnsupportedCatalogContract, SystemNotFound
    from dekopen_engine.catalog_rules import CatalogRuleError
    from dekopen_engine.openings import OpeningCapabilityError
    from dekopen_engine.weight import MissingFabricationAuthority
    candidate_errors = (ValueError, DocumentaryError, ContractAPIException, InvalidEngineRequest,
        UnsupportedEngineContract, UnsupportedCatalogContract, SystemNotFound, CatalogRuleError,
        OpeningCapabilityError, MissingFabricationAuthority)
    project = service.project_row(org_id, project_id)
    original = service.position_row(org_id, position_id)
    if str(original["project_id"]) != str(project_id):
        service.missing()
    inputs, _ = project_inputs(org_id, project)
    baseline = [position_metric(org_id, p) for p in _live_positions(org_id, project_id)]
    report = assess_project(inputs, baseline)
    target = next(p for p in report["positions"] if p["position_id"] == str(position_id))
    if target["verdict"] != "FAIL":
        return {"candidate": None, "evaluated": 0, "reason": "Primero completa los datos: solo se propone un reemplazo frente a un incumplimiento comprobado."}
    product = product_from_position(original)
    before_price = sale_price(org_id, product, original["system_id"], original["color_interior"], original["quantity"])
    if before_price.get("net") is None:
        return {"candidate": None, "evaluated": 0, "reason": before_price["reason"]}
    systems = rows("SELECT id,name FROM public.profile_systems WHERE is_active AND NOT is_demo AND data_provenance<>'SEED_SYNTHETIC' "
        "AND (org_id=%s OR (org_id IS NULL AND is_global)) ORDER BY name,id", [org_id])
    options = []
    evaluated = 0
    for system in systems:
        try:
            catalog = catalog_for(org_id, system["id"])
        except candidate_errors:
            continue
        for sku in sorted(catalog["glass_skus"]):
            evaluated += 1
            try:
                proposal = deepcopy(product)
                if str(system["id"]) != str(original["system_id"]):
                    # The API hydrates materials against the target system.
                    for module in proposal["assembly"]["modules"]:
                        def clear(node):
                            node.pop("glass_product", None)
                            node.pop("hardware_set_sku", None)
                            for child in node.get("children", []):
                                clear(child)
                        clear(module["tree"])
                ops = [{"op": "set_glass", "module": module["id"], "sku": sku}
                       for module in proposal["assembly"]["modules"]]
                proposal = apply_operations(proposal, ops, params=catalog["params"], catalog=catalog,
                    finish=original["color_interior"])["product"]
                calculation = calculate_product(org_id, proposal, system["id"], original["color_interior"], catalog)
                if calculation["status"] != "VALID":
                    continue
                design = design_from_product(proposal, system["id"], original["color_interior"])
                metric = position_metric(org_id, {**original, "system_id": system["id"], "parametric_tree": design["parametric_tree"],
                    "width_mm": design["nominal_width_mm"], "height_mm": design["nominal_height_mm"]}, params=catalog["params"])
                assessment = assess_project(inputs, [metric if p["position_id"] == str(position_id) else p for p in baseline])
                checked = next(p for p in assessment["positions"] if p["position_id"] == str(position_id))
                if checked["verdict"] != "PASS":
                    continue
                price = sale_price(org_id, proposal, system["id"], original["color_interior"], original["quantity"])
                if price.get("net") is None or price["currency"] != before_price["currency"]:
                    continue
                options.append({"system_id": str(system["id"]), "system_name": system["name"], "glass_sku": sku,
                    "product": proposal, "design": design, "price": price,
                    "delta_net": finish_selling_delta(Decimal(before_price["net"]), Decimal(price["net"])),
                    "before_price": before_price, "assessment": checked, "expected_updated_at": original["updated_at"]})
            except candidate_errors:
                continue
    options.sort(key=lambda item: (Decimal(item["price"]["net"]), item["system_name"], item["glass_sku"]))
    return {"candidate": options[0] if options else None, "evaluated": evaluated,
        "reason": None if options else "No hay un reemplazo con datos certificados, geometría compatible y precio conocido que cumpla. Completa el catálogo o revisa otra ventana del grupo.",
        "scope": "Menor precio neto indicativo entre todos los sistemas y vidrios visibles compatibles; mismo modo y tarifa predeterminados, sin descuento."}
