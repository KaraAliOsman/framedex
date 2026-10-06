"""Exact, source-preserving catalog interchange. Parsing never publishes rows.

XLSX numeric lexemes come from OOXML, not a binary-float reader. The same
columns validate manual rows, AI candidates and the human's reviewed edits.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from io import BytesIO, StringIO
import json
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from dekopen_engine.models import BayOpeningType, ProfileRole, SystemFamily

VERSION = "DEKOPEN CATÁLOGO V1"
MAX_ROWS = 2000
MAX_EXPANDED_BYTES = 30_000_000
FAMILIES = {"CASEMENT": "Practicable", "SLIDING": "Corredera", "LIFT_SLIDE": "Elevable",
            "DOOR": "Puerta de entrada", "FACADE_FIXED": "Fijo de gran formato"}
OPENINGS = {"FIXED": "Fijo", "TURN_LEFT": "Practicable izquierda", "TURN_RIGHT": "Practicable derecha",
    "TILT_TURN_LEFT": "Oscilobatiente izquierda", "TILT_TURN_RIGHT": "Oscilobatiente derecha",
    "AWNING": "Proyectante", "SLIDING": "Corredera", "SLIDING_2L": "Corredera dos hojas",
    "SLIDING_3L": "Corredera tres hojas", "SLIDING_4L": "Corredera cuatro hojas",
    "DOOR_ENTRY": "Puerta de entrada", "DOOR_DOUBLE": "Puerta doble"}
ROLES = {"FRAME": "Marco", "SASH": "Hoja practicable", "MULLION_V": "Montante", "MULLION_H": "Travesaño",
    "INVERSOR": "Inversor", "GLAZING_BEAD": "Junquillo", "COUPLER": "Acoplador", "ADDITIONAL": "Adicional",
    "THRESHOLD": "Umbral", "CHANNEL": "Canal", "SLIDING_SASH": "Hoja corredera", "INTERLOCK": "Encuentro",
    "RAIL": "Riel", "DOOR_SASH": "Hoja de puerta", "FRAME_EXTENSION": "Ensanche",
    "SILL": "Vierteaguas", "COVER_TRIM": "Tapajuntas", "PLINTH": "Zócalo"}
assert set(FAMILIES) == {value.value for value in SystemFamily}
assert set(OPENINGS) == {value.value for value in BayOpeningType}
assert set(ROLES) == {value.value for value in ProfileRole}


@dataclass(frozen=True)
class Column:
    key: str
    label: str
    kind: str = "text"
    required: bool = False
    choices: dict[str, str] | None = None


def c(key, label, kind="text", required=False, choices=None):
    return Column(key, label, kind, required, choices)


SYSTEM = c("system_code", "Código de sistema", required=True)
SKU = c("sku", "SKU", required=True)
SOURCE = c("source", "Fuente", required=True)
NAME = c("name", "Nombre", required=True)
MATERIAL = c("material", "Material", required=True, choices={"PVC": "PVC", "ALUMINIUM": "Aluminio"})

SCHEMAS: dict[str, tuple[Column, ...]] = {
    "Sistemas": (SYSTEM, NAME, c("system_family", "Familia", required=True, choices=FAMILIES), MATERIAL,
        c("depth_mm", "Profundidad (mm)", "positive", True), c("chamber_count", "Cámaras", "integer", True),
        c("sash_overlap_mm", "Traslape de hoja (mm)", "decimal", True),
        c("glass_clearance_white_mm", "Holgura vidrio blanco (mm)", "decimal", True),
        c("glass_clearance_foil_mm", "Holgura vidrio foliado (mm)", "decimal", True),
        c("corner_bracket_loss_mm", "Descuento escuadra (mm)", "decimal", True),
        c("hook_depth_mm", "Profundidad gancho (mm)", "decimal", True),
        c("door_threshold_mm", "Umbral de puerta (mm)", "decimal", True),
        c("door_bottom_clearance_mm", "Holgura inferior puerta (mm)", "decimal", True),
        c("door_leaf_side_clearance_mm", "Holgura lateral puerta (mm)", "decimal", True),
        c("rebate_depth_mm", "Rebaje (mm)", "decimal"), c("end_milling_overlap_mm", "Solape fresado (mm)", "decimal"),
        c("chamber_clearance_mm", "Holgura de cámara (mm)", "positive"),
        c("finishes", "Colores separados por |", "list", True), c("manufacturer", "Fabricante"),
        c("version", "Versión", "integer", True), c("is_active", "Activo", "boolean", True),
        c("sliding.pulley_height_mm", "Altura rodamiento (mm)", "decimal"),
        c("sliding.central_overlap_mm", "Traslape central (mm)", "decimal"),
        c("sliding.lateral_clearance_mm", "Holgura lateral corredera (mm)", "decimal"),
        c("sliding.end_add_mm", "Adición corredera (mm)", "decimal"),
        c("sliding.glazing_deduction_width_mm", "Descuento vidrio ancho (mm)", "decimal"),
        c("sliding.glazing_deduction_height_mm", "Descuento vidrio alto (mm)", "decimal"),
        c("sliding.rail_type", "Tipo de riel", choices={"mono": "Un carril", "dual": "Doble carril"}),
        c("sliding.rail_count", "Cantidad de carriles", "integer"),
        c("sliding.separate_rail", "Riel separado", "boolean"),
        c("sliding.interlock_required", "Encuentro requerido", "boolean"), SOURCE),
    "Perfiles": (SYSTEM, SKU, NAME, c("role", "Rol", required=True, choices=ROLES), MATERIAL,
        c("face_width_mm", "Ancho de cara (mm)", "positive", True),
        c("commercial_length_mm", "Largo comercial (mm)", "positive"),
        c("weight_kg_m", "Masa de perfil (kg/m)", "positive"),
        c("steel_weight_kg_m", "Masa refuerzo (kg/m)", "decimal"), SOURCE),
    "Roles y reglas de corte": (SYSTEM, SKU, c("role", "Rol", required=True, choices=ROLES),
        c("angle_degrees", "Ángulo de corte", "angle", True),
        c("welding_loss_per_end_mm", "Pérdida de soldadura", "decimal", True),
        c("joint_deduction_per_end_mm", "Descuento unión por extremo (mm)", "decimal", True),
        c("meeting_deduction_mm", "Descuento encuentro (mm)", "decimal", True),
        c("cut_step_mm", "Paso de redondeo (mm)", "positive", True),
        c("rounding", "Redondeo", required=True, choices={"UP": "Hacia arriba", "DOWN": "Hacia abajo", "NEAREST": "Más cercano"}), SOURCE),
    "Refuerzos": (SYSTEM, SKU, c("reinforcement_sku", "SKU de refuerzo", required=True),
        c("reinforcement_type", "Tipo de refuerzo", required=True),
        c("minimum_length_mm", "Largo mínimo (mm)", "decimal", True),
        c("required_finishes", "Colores obligatorios separados por |", "list", True),
        c("required_non_white", "Obligatorio en color", "boolean", True),
        c("cut_deduction_mm", "Descuento refuerzo (mm)", "decimal", True),
        c("screws_per_m", "Tornillos por metro", "positive", True),
        c("screw_sku", "SKU de tornillo", required=True), c("screw_weight_kg", "Masa tornillo (kg)", "decimal"), SOURCE),
    "Límites": (SYSTEM, c("opening_type", "Apertura", required=True, choices=OPENINGS),
        c("min_leaf_width_mm", "Ancho mínimo de hoja (mm)", "positive", True),
        c("max_leaf_width_mm", "Ancho máximo de hoja (mm)", "positive", True),
        c("min_leaf_height_mm", "Alto mínimo de hoja (mm)", "positive", True),
        c("max_leaf_height_mm", "Alto máximo de hoja (mm)", "positive", True),
        c("max_leaf_weight_kg", "Peso máximo de hoja (kg)", "positive"),
        c("min_aspect_ratio", "Relación alto/ancho mínima", "positive", True),
        c("max_aspect_ratio", "Relación alto/ancho máxima", "positive", True), SOURCE),
    "Colores y SKU por color": (SYSTEM, SKU, c("finish", "Color", required=True),
        c("commercial_sku", "SKU comercial por color", required=True),
        c("physical_stock_identity", "Identidad de stock", required=True), SOURCE),
    "Vidrios": (SYSTEM, SKU, c("glass_spec", "Composición de vidrio", required=True),
        c("name", "Nombre comercial"), c("synthetic", "Ejemplo sintético", "boolean"),
        c("ug", "Ug de proveedor (W/m²K)", "positive"),
        c("solar_factor", "Factor solar g de proveedor", "decimal"),
        c("light_transmittance", "Transmisión luminosa de proveedor", "decimal"),
        c("safety_class", "Clase NCh 135 de proveedor", choices={"A":"A", "B":"B", "C":"C"}),
        c("weight_kg_m2", "Peso declarado de proveedor (kg/m²)", "positive"),
        c("minimum_area_m2", "Área mínima facturable (m²)", "decimal"),
        c("min_width_mm", "Ancho mínimo de vidrio (mm)", "positive"),
        c("max_width_mm", "Ancho máximo de vidrio (mm)", "positive"),
        c("min_height_mm", "Alto mínimo de vidrio (mm)", "positive"),
        c("max_height_mm", "Alto máximo de vidrio (mm)", "positive"),
        c("max_area_m2", "Área máxima de vidrio (m²)", "positive"),
        c("max_aspect_ratio", "Relación de aspecto máxima de vidrio", "positive"),
        c("tempering_sku", "SKU recargo templado"), c("polishing_sku", "SKU recargo pulido"),
        c("drilling_sku", "SKU recargo perforación"), c("bars_per_m_sku", "SKU palillaje por metro"),
        c("bars_per_crossing_sku", "SKU palillaje por cruce"),
        c("purchasing_sku", "SKU de compra", required=True), c("manufacturer_name", "Fabricante", required=True),
        c("version", "Versión", "integer", True),
        c("glass_thickness_mm", "Espesor para junquillo (mm)", "positive"),
        c("bead_sku", "SKU de junquillo"), c("bead_width_mm", "Ancho de junquillo (mm)", "positive"),
        c("gasket_interior_mm", "Junta interior (mm)", "decimal"),
        c("gasket_exterior_mm", "Junta exterior (mm)", "decimal"),
        c("cut_add_mm", "Adición al corte de junquillo (mm)", "decimal"), SOURCE),
    "Reglas de vidrio": (c("code", "Código de regla", required=True), NAME,
        c("zone", "Zona de riesgo", required=True, choices={"DOOR":"Puerta", "SIDELIGHT":"Panel lateral",
            "LOW_PANE":"Paño bajo", "LARGE_PANE":"Gran ventanal"}),
        c("maximum_sill_mm", "Antepecho de referencia (mm)", "decimal"),
        c("minimum_area_m2", "Área de referencia (m²)", "positive"),
        c("required_classes", "Clases admitidas separadas por |", "list", True),
        c("mandatory", "Obligatoria", "boolean", True),
        c("synthetic", "Ejemplo sintético", "boolean", True), SOURCE),
    "Herrajes": (SYSTEM, SKU, NAME, c("opening_type", "Apertura", required=True, choices={
        "TURN": "Practicable", "TILT_TURN": "Oscilobatiente", "SLIDING": "Corredera",
        "DOOR": "Puerta", "AWNING": "Proyectante"}),
        c("min_leaf_width_mm", "Ancho mínimo de hoja (mm)", "positive", True),
        c("max_leaf_width_mm", "Ancho máximo de hoja (mm)", "positive", True),
        c("min_leaf_height_mm", "Alto mínimo de hoja (mm)", "positive", True),
        c("max_leaf_height_mm", "Alto máximo de hoja (mm)", "positive", True),
        c("max_leaf_weight_kg", "Peso máximo de hoja (kg)", "positive", True),
        c("weight_kg", "Masa de kit (kg)", "decimal"),
        c("rail_type", "Tipo de riel", required=True, choices={"mono": "Un carril", "dual": "Doble carril"}),
        c("carriage_capacity_kg", "Capacidad de carros (kg)", "positive"),
        c("carriages_qty", "Cantidad de carros", "count", True),
        c("stay_arms_qty", "Cantidad de compases", "count", True),
        c("is_active", "Activo", "boolean", True), c("contents", "Componentes (JSON)", "json", True), SOURCE),
    "Precios de costo": (SYSTEM, SKU, c("list_code", "Lista de costo", required=True),
        c("supplier_name", "Proveedor", required=True),
        c("currency", "Moneda", required=True, choices={"CLP": "CLP", "USD": "USD"}),
        c("valid_from", "Vigente desde (aaaa-mm-dd)", "date", True),
        c("valid_to", "Vigente hasta (aaaa-mm-dd)", "date"),
        c("item_type", "Tipo de artículo", required=True,
            choices={"PROFILE": "Perfil", "REINFORCEMENT": "Refuerzo", "GLASS": "Vidrio", "HARDWARE": "Herraje", "OTHER": "Otro"}),
        c("unit", "Unidad", required=True, choices={"BAR": "Barra", "M": "Metro", "M2": "Metro cuadrado", "KIT": "Kit", "EA": "Unidad"}),
        c("unit_cost", "Costo unitario", "decimal", True), SOURCE),
}


def column_letter(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def normalize(value: object, column: Column) -> object:
    if value is None or str(value).strip() in ("", "UNKNOWN", "Sin dato"):
        if column.kind == "list" and value == "[]":
            return []
        return None
    if isinstance(value, float):
        raise ValueError("usa un decimal exacto escrito como texto")
    if column.kind == "json":
        return json.loads(str(value), parse_float=Decimal) if isinstance(value, str) else value
    if column.kind == "list":
        if isinstance(value, list):
            return [str(item).strip() for item in value]
        return [] if value == "[]" else [item.strip() for item in str(value).split("|") if item.strip()]
    text = str(value).strip()
    if column.choices:
        matches = [key for key, label in column.choices.items() if text.casefold() in (key.casefold(), label.casefold())]
        if not matches:
            raise ValueError("elige " + ", ".join(column.choices.values()))
        return matches[0]
    if column.kind in ("decimal", "positive", "integer", "count", "angle"):
        try:
            if not re.fullmatch(r"[+-]?\d+(?:[.,]\d+)?", text):
                raise InvalidOperation
            parsed = Decimal(text.replace(",", "."))
        except InvalidOperation as error:
            raise ValueError("debe ser un número" + (" en mm" if "mm" in column.key else "")) from error
        if not parsed.is_finite() or parsed < 0:
            raise ValueError("debe ser un número finito mayor o igual a cero")
        if column.kind in ("positive", "integer") and parsed <= 0:
            raise ValueError("debe ser mayor que cero")
        if column.kind in ("integer", "count"):
            if parsed != parsed.to_integral_value():
                raise ValueError("debe ser un entero")
            return int(parsed)
        if column.kind == "angle":
            if parsed not in (Decimal("45"), Decimal("90")):
                raise ValueError("debe ser 45 o 90 grados")
            return int(parsed)
        return format(parsed, "f")
    if column.kind == "boolean":
        if text.casefold() in ("true", "sí", "si", "1"):
            return True
        if text.casefold() in ("false", "no", "0"):
            return False
        raise ValueError("debe ser Sí o No")
    if column.kind == "date":
        from datetime import date
        try:
            return date.fromisoformat(text).isoformat()
        except ValueError as error:
            raise ValueError("usa una fecha aaaa-mm-dd") from error
    if len(text) > 500:
        raise ValueError("no puede superar 500 caracteres")
    return text


def candidate(sheet: str, raw: dict, *, key: str, row: int, method: str,
              refs: dict | None = None) -> dict:
    values, evidence, errors = {}, {}, []
    for index, column in enumerate(SCHEMAS[sheet], 1):
        reference = (refs or {}).get(column.key) or {
            "ref": f"{sheet}!{column_letter(index)}{row}",
            "quote": str(raw.get(column.key) or ""), "confidence": "HIGH"}
        try:
            value = normalize(raw.get(column.key), column)
            if method == "AI" and reference.get("confidence") != "HIGH":
                value = None
            if value is None and column.required:
                raise ValueError("Sin dato: completa este campo con su fuente")
        except (ValueError, TypeError, InvalidOperation) as error:
            value = None
            errors.append({"field": column.key, "column": column.label,
                           "message": f"Fila {row}, columna ‘{column.label}’: {error}."})
        values[column.key] = value
        evidence[column.key] = {**reference, "method": method}
    return {"key": key, "sheet": sheet, "values": values, "fields": evidence,
            "row": row, "method": method, "errors": errors,
            "confidence": "HIGH_CANDIDATE" if not errors else "REVIEW_REQUIRED"}


def _xlsx_tables(content: bytes) -> list[tuple[str, list[dict[str, str]]]]:
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(BytesIO(content)) as archive:
        if sum(item.file_size for item in archive.infolist()) > MAX_EXPANDED_BYTES:
            raise ValueError("La planilla descomprimida supera 30 MB.")
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            strings = ["".join(item.itertext()) for item in root.findall("x:si", ns)]
        relationships = {item.attrib["Id"]: item.attrib["Target"]
                         for item in ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
        tables = []
        for sheet in ET.fromstring(archive.read("xl/workbook.xml")).findall("x:sheets/x:sheet", ns):
            relation = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            target = relationships[relation]
            path = target.lstrip("/") if target.startswith("/") else "xl/" + target
            if ".." in path.split("/"):
                raise ValueError("La planilla contiene una referencia de hoja inválida.")
            table = []
            for xml_row in ET.fromstring(archive.read(path)).findall("x:sheetData/x:row", ns):
                cells = {}
                for cell in xml_row.findall("x:c", ns):
                    ref = cell.attrib["r"]
                    if cell.find("x:f", ns) is not None:
                        value = "=FORMULA_NO_ADMITIDA"
                    elif cell.attrib.get("t") == "inlineStr":
                        inline = cell.find("x:is", ns)
                        value = "" if inline is None else "".join(inline.itertext())
                    else:
                        value = cell.findtext("x:v", "", ns)
                        if cell.attrib.get("t") == "s":
                            value = strings[int(value)]
                    cells[re.sub(r"\d", "", ref)] = value
                cells["_row"] = xml_row.attrib["r"]
                table.append(cells)
            tables.append((sheet.attrib["name"], table))
        return tables


def parse_structured(kind: str, content: bytes) -> list[dict] | None:
    """None means an arbitrary supplier file; [] means a recognized empty template."""
    tables = []
    if kind == "XLSX":
        tables = _xlsx_tables(content)
        if not any(name in SCHEMAS for name, _ in tables):
            return None
    elif kind == "CSV":
        text = content.decode("utf-8-sig")
        first_line = text.splitlines()[0] if text.splitlines() else ""
        official = next((delimiter for delimiter in (";", ",", "\t")
                         if any(first_line.startswith(name + delimiter) for name in SCHEMAS)), None)
        if official is None:
            return None
        data = list(csv.reader(StringIO(text), delimiter=official))
        if not data or not data[0] or data[0][0] not in SCHEMAS:
            return None
        name = data[0][0]
        tables = [(name, [{**{column_letter(i): value for i, value in enumerate(values, 1)},
                          "_row": str(index)} for index, values in enumerate(data[1:], 2)])]
    else:
        return None
    candidates = []
    for name, table in tables:
        if name not in SCHEMAS:
            continue
        labels = {column.label: column.key for column in SCHEMAS[name]}
        headers = next((index for index, row in enumerate(table)
                        if row.get("A") == SCHEMAS[name][0].label), None)
        if headers is None:
            raise ValueError(f"Hoja ‘{name}’: falta la fila de encabezados oficiales.")
        columns = {letter: labels[label] for letter, label in table[headers].items() if label in labels}
        for row in table[headers + 1:]:
            raw = {key: row.get(letter) for letter, key in columns.items()}
            if not any(value for value in raw.values()):
                continue
            if len(candidates) >= MAX_ROWS:
                raise ValueError("La importación supera 2 000 filas; divídela en archivos más pequeños.")
            number = int(row["_row"])
            refs = {key: {"ref": f"{name}!{letter}{number}", "quote": row.get(letter, ""), "confidence": "HIGH"}
                    for letter, key in columns.items()}
            candidates.append(candidate(name, raw, key=f"r{len(candidates)}", row=number, method="MANUAL", refs=refs))
    return candidates


def export_csv(sheet: str, candidates: list[dict]) -> bytes:
    stream = StringIO(newline="")
    writer = csv.writer(stream, delimiter=";")
    writer.writerow([sheet, VERSION])
    columns = SCHEMAS[sheet]
    writer.writerow([column.label for column in columns])
    for entry in candidates:
        if entry.get("sheet") != sheet:
            continue
        values = entry["values"]
        row = []
        for column in columns:
            value = values.get(column.key)
            if value is None:
                text = ""
            elif column.choices:
                text = column.choices.get(str(value), str(value))
            elif isinstance(value, bool):
                text = "Sí" if value else "No"
            elif column.kind == "list":
                text = "|".join(value) if value else "[]"
            elif column.kind == "json":
                text = json.dumps(value, ensure_ascii=False, default=str)
            else:
                text = str(value)
            if text.startswith(("=", "+", "-", "@")):
                text = "'" + text
            row.append(text)
        writer.writerow(row)
    return stream.getvalue().encode("utf-8-sig")


def public_schema() -> dict:
    return {"version": VERSION, "sheets": [{"name": name,
        "columns": [{"key": column.key, "label": column.label, "kind": column.kind,
                     "required": column.required, "choices": column.choices}
                    for column in columns]} for name, columns in SCHEMAS.items()]}
