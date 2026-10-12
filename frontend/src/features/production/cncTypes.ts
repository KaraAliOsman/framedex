export type Verdict = "PASS" | "WARN" | "BLOCK";
export type CncFinding = { code: string; level: Verdict; detail: Record<string, string> };
export type CncOp = {
  operation_id: string;
  kind: string;
  u_mm: string | null;
  x_mm: string | null;
  y_mm: string | null;
  face: string | null;
  reference: string | null;
  depth_mm: string | null;
  tool_id: string | null;
  basis: string;
  detail: Record<string, string>;
};
export type CncSection = {
  polygon: { x_mm: string; y_mm: string }[];
  depth_mm: string;
  orientation: string;
  local_origin: string;
  orientation_declared: boolean;
  origin_declared: boolean;
  authority_source: string;
  synthetic: boolean;
};
export type CncPreviewGeometry = {
  datum: string;
  length_mm: string | null;
  section: CncSection | null;
  section_fingerprint: string | null;
  marks: {
    operation_id: string;
    x_mm: string | null;
    face: string | null;
    section_coverage: string | null;
  }[];
};
export type CncGap = {
  kind: string;
  name?: string;
  detail: string;
  source?: string;
  component_name?: string;
  declaration?: string;
  position_index?: number;
  unit_index?: number;
  member_id?: string;
  bay_id?: string;
  leaf_id?: string;
};
export type MachineVerdict = {
  machine_id: string;
  machine_code: string;
  machine_name: string;
  verdict: Verdict;
  blockers: CncFinding[];
  warnings: CncFinding[];
  declared_unemitted: CncGap[];
};
export type CncMember = {
  member_id: string;
  member_label: string;
  workshop_sku: string | null;
  role: string | null;
  length_mm: string;
  operation_count: number;
  operations: CncOp[];
  machines: MachineVerdict[];
  preview: CncPreviewGeometry;
};
export type CncProgram = {
  id: string;
  program_no: string;
  member_id: string;
  member_label: string;
  operation_count: number;
  verdict: Verdict;
  fingerprint: string;
  status: string;
  machine_code: string;
  machine_id: string;
  created_at: string;
  replacement_id: string | null;
  replacement_no: string | null;
  identity: Record<string, string>;
  input_fingerprint: string;
};
export type CncTool = {
  authority_revision?: string;
  id: string;
  code: string;
  name: string;
  kind: string;
  diameter_mm: string | null;
  working_length_mm: string | null;
  max_depth_mm: string | null;
  compatible_kinds: string[] | null;
  active: boolean;
  authority_source: string;
};
export type CncSetup = {
  profile_sku: string;
  section_fingerprint: string;
  loading_orientation: string;
  axial_datum: string;
  source: string;
};
export type CncMachine = {
  authority_revision?: string;
  id: string;
  code: string;
  name: string;
  machine_type: string;
  profile_setups: CncSetup[];
  manufacturer: string;
  model: string;
  controller_family: string;
  coordinate_systems: string[];
  supported_kinds: string[] | null;
  supported_faces: string[] | null;
  max_member_length_mm: string | null;
  safe_margin_mm: string | null;
  clamp_zones: { start_mm: string; end_mm: string; label: string }[];
  tool_ids: string[];
  postprocessor_id: string;
  postprocessor_version: string;
  axes: string[] | null;
  clamps_declared: boolean;
  authority_source: string;
  units: string;
  encoding: string;
  active: boolean;
};
export type CncReview = {
  review_fingerprint: string;
  verdict: Verdict;
  blockers: CncFinding[];
  member_label: string;
  machine_code: string;
  preview: CncPreviewGeometry;
  document: { operations: CncOp[]; identity: Record<string, string> };
  declared_unemitted: CncGap[];
  previous_no: string | null;
  diff: {
    has_previous: boolean;
    added: CncOp[];
    removed: CncOp[];
    changed: { before: CncOp; after: CncOp }[];
    authority_changes: { field: string; before: unknown; after: unknown }[];
  };
};

export const operationLabels: Record<string, string> = {
  SAW_CUT: "Corte de sierra",
  DRILL: "Taladrado",
  SLOT: "Ranura",
  DRAINAGE: "Drenaje",
  VENTILATION: "Ventilación",
  HANDLE_PREP: "Preparación de manilla",
  LOCK_PREP: "Preparación de cerradura",
  HINGE_PREP: "Preparación de bisagra",
  CORNER_CONNECTOR: "Unión de esquina",
  T_CONNECTOR: "Unión en T",
  MILLING: "Fresado",
  END_MACHINING: "Mecanizado de extremo",
  ROUTING: "Fresado de contorno",
  GASKET_MARK: "Marca de burlete",
  CUSTOM: "Operación declarada",
};
export const faceLabels: Record<string, string> = {
  OUTSIDE_FACE: "Cara exterior",
  INSIDE_FACE: "Cara interior",
  TOP_EDGE: "Canto superior",
  BOTTOM_EDGE: "Canto inferior",
  START_EDGE: "Extremo inicial",
  END_EDGE: "Extremo final",
};
export const toolLabels: Record<string, string> = {
  SAW_BLADE: "Disco de sierra",
  DRILL_BIT: "Broca",
  END_MILL: "Fresa de extremo",
  ROUTER_BIT: "Fresa de contorno",
  PUNCH: "Punzón",
  MARKING: "Marcador",
  CUSTOM: "Herramienta declarada",
};
export const coordinateLabels: Record<string, string> = {
  MEMBER_PLAN: "Plano de la pieza",
  BAR_AXIS: "Eje de la barra",
  SHEET_PLAN: "Plano de lámina",
};
export const verdictLabel = (value: Verdict) =>
  ({ PASS: "Verificado", WARN: "Requiere revisión", BLOCK: "Bloqueado" })[value];
export const opLabel = (kind: string) => operationLabels[kind] ?? "Operación sin nombre declarado";
export const faceLabel = (face: string | null) =>
  face
    ? (faceLabels[face] ?? "Sin dato · cara no reconocida")
    : "Sin dato · falta declarar la cara";
export const datumLabel = (datum: string | null) =>
  datum === "member_start"
    ? "Origen en extremo inicial"
    : datum === "member_end"
      ? "Trabajo en extremo final; X desde el inicio"
      : "Sin dato · falta declarar el origen";
export const loadingLabels: Record<string, string> = {
  EXTERIOR_UP: "Exterior hacia arriba",
  EXTERIOR_DOWN: "Exterior hacia abajo",
  EXTERIOR_LEFT: "Exterior hacia la izquierda",
  EXTERIOR_RIGHT: "Exterior hacia la derecha",
};
export const machineTypeLabels: Record<string, string> = {
  END_MILLER: "Fresadora de extremos",
  MACHINING_CENTER: "Centro de mecanizado",
  SAW: "Sierra",
  DECLARED: "Máquina declarada por la planta",
};
const authorityLabels: Record<string, string> = {
  machine_type: "tipo de máquina",
  supported_kinds: "operaciones admitidas",
  supported_faces: "caras admitidas",
  coordinate_systems: "sistema de coordenadas",
  axes: "ejes",
  clamps_declared: "mordazas revisadas",
  max_member_length_mm: "carrera",
  safe_margin_mm: "margen de seguridad",
  authority_source: "fuente técnica",
};
export function findingText(finding: CncFinding): string {
  const d = finding.detail,
    operation = opLabel(d.kind ?? ""),
    machine = d.machine ?? "la máquina";
  const labels: Record<string, string> = {
    coordinate_unsupported: `El sistema de coordenadas no está admitido en ${machine}.`,
    unsupported_kind: `${operation} no está admitido en ${machine}.`,
    face_unsupported: `${faceLabel(d.face ?? null)} no está admitida en ${machine}.`,
    no_compatible_tool: `Herramienta ${d.tool_id ?? "sin declarar"} para ${operation.toLocaleLowerCase("es-CL")} no disponible en ${machine}.`,
    tool_depth_exceeded: "La profundidad supera la capacidad declarada de la herramienta.",
    tool_working_length_exceeded: "La profundidad supera el largo útil de la herramienta.",
    tool_undeclared: "Sin dato · falta declarar la herramienta.",
    tool_source_undeclared: "Sin dato · falta la fuente de la herramienta.",
    tool_capability_undeclared:
      "Sin dato · falta vincular el código de herramienta a sus operaciones.",
    tool_geometry_undeclared:
      "Sin dato · faltan diámetro, largo útil o profundidad máxima de la herramienta.",
    depth_undeclared: "Sin dato · falta profundidad autorizada de la operación.",
    face_undeclared: "Sin dato · falta la cara de trabajo.",
    member_length_undeclared: "Sin dato · falta el largo físico de la pieza.",
    member_coordinate_undeclared: "Sin dato · falta X desde el extremo inicial.",
    member_coordinate_outside: "La coordenada cae fuera del largo de la pieza.",
    member_datum_undeclared: "Sin dato · falta el origen físico de la operación.",
    transverse_coordinate_undeclared:
      "Sin dato · faltan coordenadas de herramienta sobre la sección. Las coordenadas del vano no las reemplazan.",
    section_undeclared: "Sin dato · esta revisión no selló una sección de perfil.",
    section_orientation_undeclared:
      "Sin dato · falta orientación u origen explícito de la sección sellada.",
    profile_setup_undeclared: `Sin dato · falta un montaje de ${d.profile_sku ?? "este perfil"} revisado para la sección sellada.`,
    profile_loading_undeclared:
      "Sin dato · falta orientación mecánica de carga, origen inicial o fuente del montaje. La orientación del dibujo no la reemplaza.",
    end_datum_inconsistent:
      "El extremo declarado no coincide con X y el origen. Revisa la regla antes de generar.",
    depth_invalid: "La profundidad no es positiva o supera el largo de la pieza.",
    machine_authority_missing: `Sin dato · falta ${authorityLabels[d.field ?? ""] ?? "autoridad de máquina"} en ${machine}.`,
    machine_axis_missing: `Falta el eje ${d.axis ?? "longitudinal"} en ${machine}.`,
    machine_format_unsupported: "La salida requiere milímetros y codificación Unicode.",
    postprocessor_undeclared: "Sin dato · no hay un postprocesador declarado y disponible.",
    postprocessor_controller_unsupported: d.controller_family
      ? "No hay un adaptador disponible para ese controlador propietario."
      : "Sin dato · falta declarar el controlador de la máquina.",
    envelope_exceeded: "La pieza supera la carrera declarada de la máquina.",
    clamp_conflict: `La operación coincide con ${d.clamp_label || "una mordaza"}. Revisa la sujeción antes de generar.`,
    margin_violation: "La operación entra en el margen de seguridad declarado.",
    feature_point_only:
      "Solo se conoce el punto de preparación; faltan patrón de agujeros y profundidad.",
  };
  return (
    labels[finding.code] ??
    "Falta resolver una autoridad física. Revisa los detalles técnicos con el jefe de taller."
  );
}
