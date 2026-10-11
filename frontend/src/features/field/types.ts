import type { FieldVisit, PositionDesign, FieldCommandRequest } from "../../api/generated/models";

export type FieldUnit = {
  position_id: string;
  position_index: number;
  unit_index: number;
  quantity: number;
  location_tag: string;
  design: PositionDesign;
  is_demo: boolean;
  order_id: string | null;
  order_code: string | null;
  label_code: string | null;
  materials: Record<string, unknown[]>;
  mounting_rules: { revision: number; rule: { code: string; name: string; synthetic: boolean } }[];
};
export type FieldEvent = {
  id: string;
  sequence: number;
  kind: string;
  payload_json: Record<string, unknown>;
  pending?: boolean;
};
export type FieldAsset = {
  id: string;
  kind: string;
  position_id: string;
  unit_index: number;
  file_sha256: string;
  payload_json: Record<string, unknown>;
};
export type Visit = Omit<FieldVisit, "context" | "events" | "assets"> & {
  context: {
    project_code: string;
    project_name: string;
    revision_code: string;
    address: string;
    contact_name: string;
    contact_phone: string | null;
    snapshot_sha256: string | null;
    units: FieldUnit[];
  };
  events: FieldEvent[];
  assets: FieldAsset[];
};
export type Incident = {
  id: string;
  code: string;
  visit_id: string;
  position_id: string;
  unit_index: number;
  order_id: string | null;
  kind: string;
  description: string;
  diagnosis: string | null;
  status: string;
  context: Visit["context"];
  evidence: { materials: Record<string, unknown[]>; photo: { id: string } };
  resolution: {
    remake_order_id?: string;
    remake_code?: string;
    purchase_order_id?: string;
    purchase_code?: string;
    service_visit_id?: string;
    service_code?: string;
    corrective_project_id?: string;
    project_code?: string;
  };
  warranty: {
    days: number | null;
    started_on: string | null;
    expires_on: string | null;
    reason: string | null;
    text: string | null;
  };
};
export type ProjectChoice = {
  id: string;
  code: string;
  name: string;
  status: string;
  current_revision: string;
  versions: { id: string; revision_code: string }[];
  positions: FieldUnit[];
  orders: {
    id: string;
    order_code: string;
    project_version_id: string;
    status: string;
    packing: { units?: { unit_index: number; position_id: string; label_code: string }[] };
  }[];
};
export type Workspace = {
  role: string;
  visits: Visit[];
  incidents: Incident[];
  projects: ProjectChoice[];
  assignees: { user_id: string; role: string; display_name: string }[];
};
export type Command = FieldCommandRequest;

export const labels: Record<string, string> = {
  DELIVERY: "Despacho",
  MEASUREMENT: "Medición",
  INSTALLATION: "Instalación",
  SERVICE: "Servicio",
  SCHEDULED: "Agendada",
  ACTIVE: "En obra",
  CLOSED: "Cerrada",
  CANCELLED: "Cancelada",
  OPEN: "Abierta",
  PLANNED: "Solución agendada",
  RESOLVED: "Resuelta",
  DAMAGE: "Daño",
  MEASURE: "Medida incorrecta",
  MISSING: "Faltante",
  ADJUSTMENT: "Regulación",
  WARRANTY: "Garantía",
  OWNER: "Dueño",
  ESTIMATOR: "Estimador",
  WORKSHOP_MANAGER: "Jefe de taller",
  INSTALLER: "Instalador",
  LOAD: "Carga",
  DEPART: "Salida con guía",
  DELIVER: "Entrega firmada",
  CHECK: "Comprobaciones",
  INCIDENT: "Incidencia",
  RECEIVE: "Recepción",
  RESOLVE: "Solución",
  DIAGNOSE: "Diagnóstico",
  CLOSE: "Cierre",
  CANCEL: "Cancelación",
};
