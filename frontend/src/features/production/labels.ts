import { domainLabels } from "../../i18n/domainLabels";
import { t } from "../../i18n/es-CL";

export function stockSourceLabel(source: string | null | undefined): string {
  return source === "NEW"
    ? "Material nuevo"
    : source === "REMNANT"
      ? "Retazo"
      : "Sin dato · falta origen";
}

export function movementLabel(type: string | null | undefined): string {
  const known = new Set([
    "RECEIPT",
    "CONSUMPTION",
    "RESERVATION",
    "RELEASE",
    "ADJUSTMENT",
    "RETURN",
    "SCRAP",
  ]);
  return type && known.has(type)
    ? t(`inventory.movement.${type}` as Parameters<typeof t>[0])
    : "Sin dato · falta tipo de movimiento";
}

export function cutRoleLabel(role: string | null | undefined): string {
  if (role === null || role === undefined || role === "") return "Sin dato";
  const known: ReadonlySet<string> = new Set([
    "FRAME",
    "SASH",
    "MULLION_V",
    "MULLION_H",
    "INVERSOR",
    "GLAZING_BEAD",
    "COUPLER",
    "ADDITIONAL",
    "THRESHOLD",
    "CHANNEL",
    "REINFORCEMENT",
  ]);
  return known.has(role)
    ? (domainLabels[role] ?? t(`production.role.${role}` as Parameters<typeof t>[0]))
    : "Sin dato · falta etiqueta de pieza";
}

const OP_KINDS: ReadonlySet<string> = new Set([
  "SAW_CUT",
  "DRILL",
  "SLOT",
  "DRAINAGE",
  "VENTILATION",
  "HANDLE_PREP",
  "LOCK_PREP",
  "HINGE_PREP",
  "CORNER_CONNECTOR",
  "T_CONNECTOR",
  "MILLING",
  "END_MACHINING",
  "ROUTING",
  "GASKET_MARK",
  "CUSTOM",
]);

export function opKindLabel(kind: string | null | undefined): string {
  if (kind === null || kind === undefined || kind === "") return "Sin dato";
  return OP_KINDS.has(kind)
    ? (domainLabels[kind] ?? t(`production.opKind.${kind}` as Parameters<typeof t>[0]))
    : "Sin dato · falta etiqueta de operación";
}

/** Op label that never oversells authority: a feature declared only as a
 * mounting point reads "referencia de montaje", not an executable prep. */
export function opLabel(op: {
  kind?: string | null;
  detail?: Record<string, unknown> | null;
}): string {
  if (op?.detail?.feature === "point_prep") return t("production.opMountingRef");
  return opKindLabel(op?.kind);
}

// Mirrors _STEP_CONSUMED_KINDS in backend/production/service.py — which stock
// kinds a station physically consumes. A consuming step cannot START until the
// order carries a usable cut plan (backend also enforces it).
export const STEP_STOCK_KINDS: Record<string, string[]> = {
  CUT: ["BAR", "SHEET"],
  ASSEMBLE: ["HARDWARE_KIT", "FITTING"],
  HARDWARE: ["HARDWARE_KIT", "FITTING"],
  GLAZE: ["PANEL"],
};

const STOCK_KINDS: ReadonlySet<string> = new Set([
  "BAR",
  "SHEET",
  "KIT",
  "HARDWARE_KIT",
  "PANEL",
  "FITTING",
  "OFFCUT",
  "REMNANT",
]);

export function stockKindLabel(kind: string | null | undefined): string {
  if (kind === null || kind === undefined || kind === "") return "Sin dato";
  return STOCK_KINDS.has(kind)
    ? (domainLabels[kind] ?? t(`production.stockKindValue.${kind}` as Parameters<typeof t>[0]))
    : "Sin dato · falta etiqueta de operación";
}

const CENTER_KINDS: ReadonlySet<string> = new Set([
  "CUT",
  "PROFILE_CUT",
  "REINFORCEMENT_CUT",
  "MACHINING",
  "WELDING",
  "CRIMP",
  "CRIMPING",
  "CLEANING",
  "ASSEMBLY",
  "SASH_ASSEMBLY",
  "HARDWARE",
  "GLAZING",
  "QC",
  "PACK",
]);

export function centerKindLabel(kind: string | null | undefined): string {
  if (kind === null || kind === undefined || kind === "") return "Sin dato";
  return CENTER_KINDS.has(kind)
    ? t(`production.centerKind.${kind}` as Parameters<typeof t>[0])
    : "Sin dato · falta etiqueta de operación";
}

const STATION_CODES: ReadonlySet<string> = new Set([
  "CUT",
  "PROFILE_CUT",
  "REINFORCEMENT_CUT",
  "MACHINING",
  "WELD",
  "CLEAN",
  "CRIMP",
  "SASH_ASSEMBLE",
  "ASSEMBLE",
  "HARDWARE",
  "GLAZE",
  "QC",
  "PACK",
  "INSTALL",
  "DISPATCH",
]);

export function stationCodeLabel(code: string | null | undefined): string {
  if (code === null || code === undefined || code === "") return "Sin dato";
  return STATION_CODES.has(code)
    ? t(`production.station.${code}` as Parameters<typeof t>[0])
    : "Sin dato · falta etiqueta de estación";
}

// Stations that physically work the sealed cut plan — mirrors
// _PLAN_REQUIRED_STATIONS / _OPS_EVIDENCE_STATIONS in
// backend/production/service.py: they can't start on a dead plan and must
// declare every routed member op at COMPLETE.
export const PLAN_REQUIRED_CODES: ReadonlySet<string> = new Set([
  "MACHINING",
  "PROFILE_CUT",
  "REINFORCEMENT_CUT",
]);

// Member-local vocabulary — mirrors the machining pack's operator language
// (backend/production/pack.py): the printed sheet and the screen name the
// same datum identically, so a stick reconciles paper↔web without a map.

export function opReferenceLabel(reference: string | null | undefined): string {
  if (reference === null || reference === undefined || reference === "") return "Sin dato";
  return domainLabels[reference] ?? "Sin dato · falta referencia";
}

const OP_FACES: ReadonlyMap<string, string> = new Map([
  ["OUTSIDE_FACE", "cara exterior"],
  ["INSIDE_FACE", "cara interior"],
  ["TOP_EDGE", "canto superior"],
  ["BOTTOM_EDGE", "canto inferior"],
  ["START_EDGE", "canto Ext. A"],
  ["END_EDGE", "canto Ext. B"],
]);

export function opFaceLabel(face: string | null | undefined): string {
  if (face === null || face === undefined || face === "") return "Sin dato";
  return OP_FACES.get(face) ?? domainLabels[face] ?? "Sin dato · falta cara";
}

const OP_BASES: ReadonlyMap<string, string> = new Map([
  ["cut_plan.head_trim", "Plan de corte"],
  ["cut_plan.placement", "Plan de corte"],
  ["cut_plan.tail_trim", "Plan de corte"],
  ["member_end_overlap", "Solape de extremo"],
]);

export function opBasisLabel(basis: string | null | undefined): string {
  if (basis === null || basis === undefined || basis === "") return "Sin dato";
  const mapped = OP_BASES.get(basis);
  if (mapped) return mapped;
  if (basis.startsWith("handle_requirement_policy:")) {
    return "Política de herraje sellada";
  }
  if (basis.startsWith("handle_policy:")) {
    return "Política de manilla sellada";
  }
  return "Sin dato · falta autoridad de operación";
}

export function opBoundaryLabel(boundary: string | null | undefined): string {
  if (boundary === null || boundary === undefined || boundary === "") return "Sin dato";
  return domainLabels[boundary] ?? "Sin dato · falta límite";
}

const REMNANT_STATUSES: ReadonlySet<string> = new Set([
  "AVAILABLE",
  "RESERVED",
  "CONSUMED",
  "SCRAPPED",
]);

export function remnantStatusLabel(status: string | null | undefined): string {
  if (status === null || status === undefined || status === "") return "Sin dato";
  return REMNANT_STATUSES.has(status)
    ? t(`production.remnantStatus.${status}` as Parameters<typeof t>[0])
    : "Sin dato · falta estado del retazo";
}
