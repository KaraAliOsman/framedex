import { useCallback, useEffect, useState } from "react";
import {
  productionCncMachineCreate,
  productionCncMachineUpdate,
  productionCncToolCreate,
  productionCncToolUpdate,
  productionCncWorkspace,
  productionOrderCncReadiness,
} from "../../api/generated/dekopen";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { decimalInputValue, parseDecimalInput } from "../../decimal";
import { fmtMm, formatDateTime } from "../../format";
import { Button, Field, TextInput } from "../../ui/Controls";
import { DataTable, type TableColumn } from "../../ui/DataTable";
import { ErrorState, LoadingState } from "../../ui/States";
import { StatusBadge } from "../../ui/StatusBadge";
import { actionErrorDetail, CncSelect as Select } from "./cncControls";
import {
  type CncMachine,
  type CncTool,
  type CncMember,
  coordinateLabels,
  faceLabels,
  loadingLabels,
  machineTypeLabels,
  operationLabels,
  toolLabels,
} from "./cncTypes";

type Event = {
  id: string;
  entity_kind: string;
  action: string;
  previous: Record<string, unknown> | null;
  current: Record<string, unknown>;
  actor_label: string | null;
  created_at: string;
};
type Workspace = { tools: CncTool[]; machines: CncMachine[]; history: Event[] };
type Review =
  | { kind: "TOOL"; before: CncTool | null; after: CncTool }
  | { kind: "MACHINE"; before: CncMachine | null; after: CncMachine };
const emptyTool = (): CncTool => ({
  id: "",
  code: "",
  name: "",
  kind: "",
  diameter_mm: null,
  working_length_mm: null,
  max_depth_mm: null,
  compatible_kinds: [],
  active: true,
  authority_source: "",
});
const emptyMachine = (): CncMachine => ({
  id: "",
  code: "",
  name: "",
  machine_type: "",
  manufacturer: "",
  model: "",
  controller_family: "",
  coordinate_systems: [],
  supported_kinds: [],
  supported_faces: [],
  max_member_length_mm: null,
  safe_margin_mm: null,
  clamp_zones: [],
  tool_ids: [],
  postprocessor_id: "",
  postprocessor_version: "",
  axes: [],
  clamps_declared: false,
  authority_source: "",
  profile_setups: [],
  units: "mm",
  encoding: "utf-8",
  active: true,
});
const labels: Record<string, string> = {
  code: "Código",
  name: "Nombre",
  kind: "Tipo de herramienta",
  machine_type: "Tipo de máquina",
  manufacturer: "Fabricante",
  model: "Modelo",
  controller_family: "Controlador",
  coordinate_systems: "Coordenadas",
  supported_kinds: "Operaciones admitidas",
  supported_faces: "Caras admitidas",
  diameter_mm: "Diámetro",
  working_length_mm: "Largo útil",
  max_depth_mm: "Profundidad máxima",
  compatible_kinds: "Operaciones de la herramienta",
  max_member_length_mm: "Carrera longitudinal",
  safe_margin_mm: "Margen de seguridad",
  clamp_zones: "Mordazas",
  tool_ids: "Herramientas vinculadas",
  postprocessor_id: "Postprocesador",
  postprocessor_version: "Versión del postprocesador",
  axes: "Ejes",
  clamps_declared: "Sujeción revisada",
  authority_source: "Fuente técnica",
  profile_setups: "Montajes de perfil",
  units: "Unidad",
  encoding: "Codificación",
  active: "Disponibilidad",
};
const mm = (value: string | null) =>
  value == null || value === "" ? "Sin dato" : fmtMm(value) + " mm";
function Choices({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: Record<string, string>;
  value: string[] | null;
  onChange: (v: string[]) => void;
}) {
  return (
    <fieldset className="cnc-choices">
      <legend>{label}</legend>
      {value === null ? (
        <p className="cnc-person">Sin dato · no se declaró una lista de capacidades.</p>
      ) : null}
      <div>
        {Object.entries(options).map(([key, text]) => (
          <label key={key}>
            <input
              type="checkbox"
              checked={value?.includes(key) ?? false}
              onChange={(e) =>
                onChange(
                  e.target.checked
                    ? [...(value ?? []), key]
                    : (value ?? []).filter((v) => v !== key),
                )
              }
            />
            {text}
          </label>
        ))}
      </div>
    </fieldset>
  );
}
export function CncWorkspace({ orderId }: { orderId: string }) {
  const auth = useAuthSession(),
    role = auth.me?.active_organization?.role ?? "",
    canWrite = role === "OWNER" || role === "WORKSHOP_MANAGER";
  const [data, setData] = useState<Workspace | null>(null),
    [members, setMembers] = useState<CncMember[]>([]);
  const [error, setError] = useState<string | null>(null),
    [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(false);
  const [tool, setTool] = useState<CncTool | null>(null),
    [machine, setMachine] = useState<CncMachine | null>(null);
  const [review, setReview] = useState<Review | null>(null),
    [confirmed, setConfirmed] = useState(false),
    [notice, setNotice] = useState("");
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await productionCncWorkspace();
      setData(r.data as Workspace);
      setError(null);
      try {
        const r = await productionOrderCncReadiness(orderId);
        setMembers((r.data as { members: CncMember[] }).members);
      } catch {
        setMembers([]);
      }
    } catch (err) {
      setError(
        actionErrorDetail(err, "No se pudo cargar la autoridad de la planta. Vuelve a intentar."),
      );
    } finally {
      setLoading(false);
    }
  }, [orderId]);
  useEffect(() => {
    setTool(null);
    setMachine(null);
    setReview(null);
    void load();
  }, [load]);
  const profiles = [
    ...new Map(
      members
        .filter((m) => m.workshop_sku && m.preview.section_fingerprint)
        .map((m) => [m.workshop_sku!, m]),
    ).values(),
  ];
  function editTool(patch: Partial<CncTool>) {
    if (tool) setTool({ ...tool, ...patch });
    setReview(null);
    setConfirmed(false);
  }
  function editMachine(patch: Partial<CncMachine>) {
    if (machine) setMachine({ ...machine, ...patch });
    setReview(null);
    setConfirmed(false);
  }
  function valueText(key: string, value: unknown): string {
    if (value == null || value === "") return "Sin dato";
    if (key.endsWith("_mm")) return mm(String(value));
    if (key === "active") return value ? "Activa" : "Retirada";
    if (typeof value === "boolean") return value ? "Sí" : "No";
    if (key === "kind") return toolLabels[String(value)] ?? "Tipo sin declarar";
    if (key === "machine_type") return machineTypeLabels[String(value)] ?? "Tipo sin declarar";
    if (key === "controller_family")
      return value === "NEUTRAL" ? "Intercambio neutro" : "Propietario: " + String(value);
    if (key === "postprocessor_id")
      return value === "neutral-ops-v1"
        ? "Intercambio neutro disponible"
        : "Adaptador sin implementar";
    if (key === "encoding") return value === "utf-8" ? "Unicode" : "Codificación sin soporte";
    if (Array.isArray(value)) {
      if (!value.length) return "Ninguna declarada";
      if (key === "clamp_zones")
        return (value as CncMachine["clamp_zones"])
          .map((z) => (z.label || "Mordaza") + " · " + mm(z.start_mm) + " a " + mm(z.end_mm))
          .join("; ");
      if (key === "profile_setups")
        return (value as CncMachine["profile_setups"])
          .map(
            (s) =>
              s.profile_sku +
              " · " +
              (loadingLabels[s.loading_orientation] ?? "Sin dato") +
              " · origen inicial · " +
              s.source +
              " · sección sellada vinculada",
          )
          .join("; ");
      return value
        .map((v) =>
          key === "tool_ids"
            ? (data?.tools.find((t) => t.id === v)?.code ?? "Herramienta sin dato")
            : (operationLabels[String(v)] ??
              faceLabels[String(v)] ??
              coordinateLabels[String(v)] ??
              String(v)),
        )
        .join(" · ");
    }
    return String(value);
  }
  function changed(before: object | null, after: object) {
    const a = after as Record<string, unknown>,
      b = before as Record<string, unknown> | null;
    return Object.keys(labels).filter(
      (k) => k in a && JSON.stringify(b?.[k]) !== JSON.stringify(a[k]),
    );
  }
  function diff(before: object | null, after: object) {
    const a = after as Record<string, unknown>,
      b = before as Record<string, unknown> | null;
    return (
      <dl>
        {changed(before, after).map((k) => (
          <div key={k}>
            <dt>{labels[k]}</dt>
            <dd className={k.endsWith("_mm") ? "cnc-number" : ""}>
              {valueText(k, b?.[k])} → {valueText(k, a[k])}
            </dd>
          </div>
        ))}
      </dl>
    );
  }
  function prepare() {
    setError(null);
    setConfirmed(false);
    try {
      if (tool) {
        if (!tool.code.trim() || !tool.name.trim() || !tool.kind)
          throw new Error("Completa código, nombre y tipo de herramienta.");
        const after = { ...tool };
        for (const k of ["diameter_mm", "working_length_mm", "max_depth_mm"] as const) {
          const v = tool[k],
            parsed = v == null || v === "" ? null : parseDecimalInput(v, 4);
          if (v && (parsed === null || parsed.startsWith("-") || /^0(?:\.0+)?$/.test(parsed)))
            throw new Error("Revisa " + labels[k] + ": usa milímetros positivos o deja Sin dato.");
          after[k] = parsed;
        }
        setReview({
          kind: "TOOL",
          before: data?.tools.find((t) => t.id === tool.id) ?? null,
          after,
        });
      } else if (machine) {
        if (!machine.code.trim() || !machine.name.trim())
          throw new Error("Completa código y nombre de máquina.");
        const after = { ...machine };
        for (const k of ["max_member_length_mm", "safe_margin_mm"] as const) {
          const v = machine[k],
            parsed = v == null || v === "" ? null : parseDecimalInput(v, 4);
          if (
            v &&
            (parsed === null ||
              parsed.startsWith("-") ||
              (k === "max_member_length_mm" && /^0(?:\.0+)?$/.test(parsed)))
          )
            throw new Error("Revisa " + labels[k] + ": usa milímetros válidos o deja Sin dato.");
          after[k] = parsed;
        }
        after.clamp_zones = after.clamp_zones.map((z) => {
          const start = parseDecimalInput(z.start_mm, 4),
            end = parseDecimalInput(z.end_mm, 4);
          if (start === null || end === null || start.startsWith("-") || end.startsWith("-"))
            throw new Error("Completa inicio y fin de cada mordaza en milímetros.");
          return { ...z, start_mm: start, end_mm: end };
        });
        if (after.profile_setups.some((s) => !s.loading_orientation || !s.source.trim()))
          throw new Error(
            "Cada montaje necesita orientación de carga y fuente técnica. Retíralo si aún no tiene autoridad.",
          );
        setReview({
          kind: "MACHINE",
          before: data?.machines.find((m) => m.id === machine.id) ?? null,
          after,
        });
      }
    } catch (err) {
      setError(actionErrorDetail(err, "Revisa los datos declarados."));
    }
  }
  async function save() {
    if (!review || !confirmed) return;
    setBusy(true);
    try {
      if (review.kind === "TOOL") {
        const { id, authority_revision, ...body } = review.after;
        if (id)
          await productionCncToolUpdate(id, { ...body, expected_revision: authority_revision });
        else await productionCncToolCreate(body);
      } else {
        const { id, authority_revision, ...body } = review.after;
        if (id)
          await productionCncMachineUpdate(id, { ...body, expected_revision: authority_revision });
        else await productionCncMachineCreate(body);
      }
      setNotice(
        review.after.code + " guardada con historial. Los programas volverán a verificarse.",
      );
      setTool(null);
      setMachine(null);
      setReview(null);
      setConfirmed(false);
      await load();
      window.dispatchEvent(new window.Event("dekopen:cnc-authority"));
    } catch (err) {
      setError(
        actionErrorDetail(
          err,
          "No se pudo guardar la autoridad. Revisa los datos y vuelve a intentar.",
        ),
      );
    } finally {
      setBusy(false);
    }
  }
  function restore(event: Event) {
    if (!event.previous) return;
    const id = String(event.current.id);
    if (event.entity_kind === "TOOL") {
      const current = data?.tools.find((t) => t.id === id);
      if (!current) return;
      const next = { ...current };
      for (const key of Object.keys(emptyTool()))
        if (key !== "id" && key in event.previous)
          (next as unknown as Record<string, unknown>)[key] = event.previous[key];
      for (const key of ["diameter_mm", "working_length_mm", "max_depth_mm"] as const)
        next[key] = next[key] == null ? null : decimalInputValue(next[key]);
      setMachine(null);
      setTool(next);
    } else {
      const current = data?.machines.find((m) => m.id === id);
      if (!current) return;
      const next = { ...current };
      for (const key of Object.keys(emptyMachine()))
        if (key !== "id" && key in event.previous)
          (next as unknown as Record<string, unknown>)[key] = event.previous[key];
      for (const key of ["max_member_length_mm", "safe_margin_mm"] as const)
        next[key] = next[key] == null ? null : decimalInputValue(next[key]);
      setTool(null);
      setMachine(next);
    }
    setReview(null);
    setConfirmed(false);
  }
  const toolColumns: TableColumn<CncTool>[] = [
    {
      id: "code",
      label: "Herramienta",
      value: (t) => t.code,
      render: (t) => (
        <>
          <strong className="cnc-number">{t.code}</strong>
          <p>
            {t.name} · {toolLabels[t.kind] ?? "Sin dato · tipo"}
          </p>
        </>
      ),
    },
    {
      id: "authority",
      label: "Autoridad declarada",
      value: (t) =>
        t.name + " " + (t.compatible_kinds ?? []).map((k) => operationLabels[k]).join(" "),
      render: (t) => (
        <>
          <p>{valueText("compatible_kinds", t.compatible_kinds)}</p>
          <p className="cnc-number">
            Diámetro {mm(t.diameter_mm)} · útil {mm(t.working_length_mm)} · profundidad{" "}
            {mm(t.max_depth_mm)}
          </p>
          <small>Fuente: {t.authority_source || "Sin dato · falta fuente"}</small>
        </>
      ),
    },
    {
      id: "active",
      label: "Disponibilidad",
      value: (t) => (t.active ? "Activa" : "Retirada"),
      render: (t) => (
        <>
          <StatusBadge tone={t.active ? "neutral" : "person"}>
            {t.active ? "Activa" : "Retirada"}
          </StatusBadge>
          {canWrite ? (
            <Button
              disabled={busy}
              onClick={() => {
                setMachine(null);
                setTool({ ...t });
                setReview(null);
              }}
            >
              Revisar {t.code}
            </Button>
          ) : null}
        </>
      ),
    },
  ];
  const machineColumns: TableColumn<CncMachine>[] = [
    {
      id: "code",
      label: "Máquina",
      value: (m) => m.code,
      render: (m) => (
        <>
          <strong className="cnc-number">{m.code}</strong>
          <p>
            {m.name} · {machineTypeLabels[m.machine_type] ?? "Sin dato · tipo"}
          </p>
        </>
      ),
    },
    {
      id: "authority",
      label: "Capacidad y sujeción",
      value: (m) => m.name,
      render: (m) => (
        <>
          <p className="cnc-number">
            Ejes {m.axes?.join(" · ") || "Sin dato"} · carrera {mm(m.max_member_length_mm)}
          </p>
          <p>
            {m.clamps_declared ? "Sujeción revisada" : "Sin dato · falta revisar mordazas"} ·{" "}
            {valueText("tool_ids", m.tool_ids)}
          </p>
          <p>
            {m.profile_setups.length
              ? m.profile_setups
                  .map(
                    (s) =>
                      s.profile_sku + ": " + (loadingLabels[s.loading_orientation] ?? "Sin dato"),
                  )
                  .join("; ")
              : "Sin dato · falta montaje por perfil"}
          </p>
          <small>Fuente: {m.authority_source || "Sin dato · falta fuente"}</small>
        </>
      ),
    },
    {
      id: "active",
      label: "Disponibilidad",
      value: (m) => (m.active ? "Activa" : "Retirada"),
      render: (m) => (
        <>
          <StatusBadge tone={m.active ? "neutral" : "person"}>
            {m.active ? "Activa" : "Retirada"}
          </StatusBadge>
          {canWrite ? (
            <Button
              disabled={busy}
              onClick={() => {
                setTool(null);
                setMachine({ ...m });
                setReview(null);
              }}
            >
              Revisar {m.code}
            </Button>
          ) : null}
        </>
      ),
    },
  ];
  return (
    <details className="cnc-workspace" id="cnc-authorities" data-region="autoridad-cnc">
      <summary>Máquinas y herramientas de la planta</summary>
      <div className="cnc-authority-body">
        <header className="cnc-heading">
          <p>
            El código de herramienta se vincula a la operación. Cada perfil necesita un montaje
            revisado para su sección sellada.
          </p>
          <Button disabled={busy} onClick={() => void load()}>
            Actualizar autoridad
          </Button>
        </header>
        {error ? (
          <ErrorState title="Revisa la autoridad" body={error} onRetry={() => void load()} />
        ) : null}
        {notice ? <p role="status">{notice}</p> : null}
        {!canWrite ? (
          <p className="cnc-permission">
            Puedes leer la autoridad. El dueño o jefe de taller declara, retira y reactiva máquinas
            y herramientas.
          </p>
        ) : null}
        {loading && !data ? (
          <LoadingState label="Cargando autoridad de la planta" />
        ) : data ? (
          <>
            <section data-region="herramientas">
              <header className="cnc-heading">
                <h4>Herramientas y operaciones</h4>
                {canWrite && !tool && !machine ? (
                  <Button onClick={() => setTool(emptyTool())}>Declarar herramienta</Button>
                ) : null}
              </header>
              <DataTable
                label="herramientas"
                rows={data.tools}
                columns={toolColumns}
                rowKey={(t) => t.id}
                emptyReason="Declara código y capacidad física; no se presume compatibilidad."
              />
            </section>
            <section data-region="maquinas">
              <header className="cnc-heading">
                <h4>Máquinas</h4>
                {canWrite && !tool && !machine ? (
                  <Button onClick={() => setMachine(emptyMachine())}>Declarar máquina</Button>
                ) : null}
              </header>
              <DataTable
                label="máquinas"
                rows={data.machines}
                columns={machineColumns}
                rowKey={(m) => m.id}
                emptyReason="Declara tipo, carrera, ejes, herramientas y mordazas; después revisa el montaje del perfil."
              />
            </section>
          </>
        ) : null}
        {canWrite && (tool || machine) ? (
          <form
            className="cnc-form"
            noValidate
            onSubmit={(e) => {
              e.preventDefault();
              prepare();
            }}
            data-region="declaracion-autoridad"
          >
            <fieldset className="cnc-form-lock" disabled={busy}>
              <h4>
                {tool ? "Declaración de herramienta" : "Declaración de máquina"} ·{" "}
                {tool?.code || machine?.code || "Nueva"}
              </h4>
              <div className="cnc-form-fields">
                {(["code", "name", "authority_source"] as const).map((k) => (
                  <Field key={k} label={labels[k]!}>
                    <TextInput
                      disabled={busy}
                      value={(tool ?? machine)![k]}
                      onChange={(e) =>
                        tool
                          ? editTool({ [k]: e.target.value })
                          : editMachine({ [k]: e.target.value })
                      }
                    />
                  </Field>
                ))}
              </div>
              {tool ? (
                <>
                  <Field label="Tipo de herramienta">
                    <Select value={tool.kind} onChange={(e) => editTool({ kind: e.target.value })}>
                      <option value="">Sin dato · elige el tipo</option>
                      {Object.entries(toolLabels).map(([k, l]) => (
                        <option value={k} key={k}>
                          {l}
                        </option>
                      ))}
                    </Select>
                  </Field>
                  <div className="cnc-form-fields">
                    {(["diameter_mm", "working_length_mm", "max_depth_mm"] as const).map((k) => (
                      <Field
                        key={k}
                        label={labels[k] + " · mm"}
                        help="Vacío significa Sin dato y bloquea la generación."
                      >
                        <TextInput
                          inputMode="decimal"
                          value={tool[k] ?? ""}
                          onChange={(e) => editTool({ [k]: e.target.value })}
                        />
                      </Field>
                    ))}
                  </div>
                  <Choices
                    label="Código de herramienta ↔ operaciones admitidas"
                    options={operationLabels}
                    value={tool.compatible_kinds}
                    onChange={(v) => editTool({ compatible_kinds: v })}
                  />
                </>
              ) : null}
              {machine ? (
                <>
                  <div className="cnc-form-fields">
                    <Field label="Tipo de máquina">
                      <Select
                        value={machine.machine_type}
                        onChange={(e) => editMachine({ machine_type: e.target.value })}
                      >
                        <option value="">Sin dato · elige el tipo</option>
                        {Object.entries(machineTypeLabels).map(([k, l]) => (
                          <option value={k} key={k}>
                            {l}
                          </option>
                        ))}
                      </Select>
                    </Field>
                    {(["manufacturer", "model", "postprocessor_version"] as const).map((k) => (
                      <Field key={k} label={labels[k]!}>
                        <TextInput
                          value={machine[k]}
                          onChange={(e) => editMachine({ [k]: e.target.value })}
                        />
                      </Field>
                    ))}
                    <Field label="Familia de controlador">
                      <Select
                        value={machine.controller_family}
                        onChange={(e) => editMachine({ controller_family: e.target.value })}
                      >
                        <option value="">Sin dato · elige la familia</option>
                        <option value="NEUTRAL">Intercambio neutro</option>
                        {machine.controller_family && machine.controller_family !== "NEUTRAL" ? (
                          <option value={machine.controller_family}>
                            Propietario sin adaptador disponible
                          </option>
                        ) : null}
                      </Select>
                    </Field>
                    <Field label="Postprocesador">
                      <Select
                        value={machine.postprocessor_id}
                        onChange={(e) => editMachine({ postprocessor_id: e.target.value })}
                      >
                        <option value="">Sin dato · no disponible</option>
                        <option value="neutral-ops-v1">Intercambio neutro revisado</option>
                        {machine.postprocessor_id &&
                        machine.postprocessor_id !== "neutral-ops-v1" ? (
                          <option value={machine.postprocessor_id}>
                            Adaptador declarado sin implementar
                          </option>
                        ) : null}
                      </Select>
                    </Field>
                    {(["max_member_length_mm", "safe_margin_mm"] as const).map((k) => (
                      <Field key={k} label={labels[k] + " · mm"}>
                        <TextInput
                          inputMode="decimal"
                          value={machine[k] ?? ""}
                          onChange={(e) => editMachine({ [k]: e.target.value })}
                        />
                      </Field>
                    ))}
                  </div>
                  <p>
                    Este adaptador requiere declarar el controlador de intercambio neutro. Un
                    controlador propietario queda bloqueado. Unidad: milímetros · codificación:
                    Unicode.
                  </p>
                  <Choices
                    label="Ejes declarados"
                    options={{
                      X: "X · longitudinal",
                      Y: "Y · transversal",
                      Z: "Z · profundidad",
                      A: "A · rotación",
                      B: "B · rotación",
                      C: "C · rotación",
                    }}
                    value={machine.axes}
                    onChange={(v) => editMachine({ axes: v })}
                  />
                  <Choices
                    label="Sistemas de coordenadas"
                    options={coordinateLabels}
                    value={machine.coordinate_systems}
                    onChange={(v) => editMachine({ coordinate_systems: v })}
                  />
                  <Choices
                    label="Operaciones admitidas"
                    options={operationLabels}
                    value={machine.supported_kinds}
                    onChange={(v) => editMachine({ supported_kinds: v })}
                  />
                  <Choices
                    label="Caras admitidas"
                    options={faceLabels}
                    value={machine.supported_faces}
                    onChange={(v) => editMachine({ supported_faces: v })}
                  />
                  <Choices
                    label="Herramientas vinculadas"
                    options={Object.fromEntries(
                      (data?.tools ?? []).map((t) => [
                        t.id,
                        t.code + " · " + t.name + (t.active ? "" : " · retirada"),
                      ]),
                    )}
                    value={machine.tool_ids}
                    onChange={(v) => editMachine({ tool_ids: v })}
                  />
                  <section>
                    <h5>Mordazas · X desde el origen inicial</h5>
                    {machine.clamp_zones.map((z, i) => (
                      <div className="cnc-form-fields" key={i}>
                        {(["label", "start_mm", "end_mm"] as const).map((k) => (
                          <Field
                            key={k}
                            label={
                              { label: "Nombre", start_mm: "Inicio · mm", end_mm: "Fin · mm" }[k]
                            }
                          >
                            <TextInput
                              value={z[k]}
                              onChange={(e) =>
                                editMachine({
                                  clamp_zones: machine.clamp_zones.map((z, j) =>
                                    j === i ? { ...z, [k]: e.target.value } : z,
                                  ),
                                })
                              }
                            />
                          </Field>
                        ))}
                        <Button
                          onClick={() =>
                            editMachine({
                              clamp_zones: machine.clamp_zones.filter((_, j) => j !== i),
                            })
                          }
                        >
                          Retirar mordaza {i + 1}
                        </Button>
                      </div>
                    ))}
                    <Button
                      onClick={() =>
                        editMachine({
                          clamp_zones: [
                            ...machine.clamp_zones,
                            { label: "", start_mm: "", end_mm: "" },
                          ],
                        })
                      }
                    >
                      Agregar mordaza
                    </Button>
                    <label className="cnc-confirm">
                      <input
                        type="checkbox"
                        checked={machine.clamps_declared}
                        onChange={(e) => editMachine({ clamps_declared: e.target.checked })}
                      />
                      Revisé toda la sujeción. Una lista vacía declara que no hay mordazas sobre el
                      eje y necesita fuente técnica.
                    </label>
                  </section>
                  <section>
                    <h5>Montaje por perfil y sección sellada</h5>
                    {machine.profile_setups.map((s, i) => (
                      <div key={s.profile_sku} className="cnc-setup">
                        <strong className="cnc-number">{s.profile_sku}</strong>
                        <p>
                          {profiles.some(
                            (p) =>
                              p.workshop_sku === s.profile_sku &&
                              p.preview.section_fingerprint === s.section_fingerprint,
                          )
                            ? "Vinculado a la sección sellada de esta OT"
                            : "Vinculado a otra sección sellada; revisa la pieza"}{" "}
                          · origen longitudinal en extremo inicial.
                        </p>
                        <div className="cnc-form-fields">
                          <Field label="Orientación mecánica de carga">
                            <Select
                              value={s.loading_orientation}
                              onChange={(e) =>
                                editMachine({
                                  profile_setups: machine.profile_setups.map((s, j) =>
                                    i === j ? { ...s, loading_orientation: e.target.value } : s,
                                  ),
                                })
                              }
                            >
                              <option value="">Sin dato · elige la orientación</option>
                              {Object.entries(loadingLabels).map(([k, l]) => (
                                <option key={k} value={k}>
                                  {l}
                                </option>
                              ))}
                            </Select>
                          </Field>
                          <Field label="Fuente del montaje revisado">
                            <TextInput
                              value={s.source}
                              onChange={(e) =>
                                editMachine({
                                  profile_setups: machine.profile_setups.map((s, j) =>
                                    i === j ? { ...s, source: e.target.value } : s,
                                  ),
                                })
                              }
                            />
                          </Field>
                          <Button
                            onClick={() =>
                              editMachine({
                                profile_setups: machine.profile_setups.filter((_, j) => i !== j),
                              })
                            }
                          >
                            Retirar montaje de {s.profile_sku}
                          </Button>
                        </div>
                      </div>
                    ))}
                    <Field
                      label="Agregar un perfil de esta OT"
                      help="Solo se ofrecen secciones selladas; un histórico sin sección requiere una revisión nueva."
                    >
                      <Select
                        value=""
                        onChange={(e) => {
                          const p = profiles.find((p) => p.workshop_sku === e.target.value);
                          if (p)
                            editMachine({
                              profile_setups: [
                                ...machine.profile_setups.filter(
                                  (s) => s.profile_sku !== p.workshop_sku,
                                ),
                                {
                                  profile_sku: p.workshop_sku!,
                                  section_fingerprint: p.preview.section_fingerprint!,
                                  loading_orientation: "",
                                  axial_datum: "MEMBER_START",
                                  source: "",
                                },
                              ],
                            });
                        }}
                      >
                        <option value="">Elige un perfil con sección sellada</option>
                        {profiles.map((p) => (
                          <option key={p.workshop_sku} value={p.workshop_sku!}>
                            {p.workshop_sku}
                            {p.preview.section?.synthetic ? " · DEMO" : ""}
                          </option>
                        ))}
                      </Select>
                    </Field>
                  </section>
                </>
              ) : null}
              {tool?.id || machine?.id ? (
                <label className="cnc-confirm">
                  <input
                    type="checkbox"
                    checked={(tool ?? machine)!.active}
                    onChange={(e) =>
                      tool
                        ? editTool({ active: e.target.checked })
                        : editMachine({ active: e.target.checked })
                    }
                  />
                  Disponible en la planta. Retirar conserva el historial y revalida cada programa.
                </label>
              ) : null}
              <div className="cnc-file-actions">
                <Button type="submit" disabled={busy}>
                  Revisar cambios
                </Button>
                <Button
                  disabled={busy}
                  onClick={() => {
                    setTool(null);
                    setMachine(null);
                    setReview(null);
                  }}
                >
                  Cancelar declaración
                </Button>
              </div>
            </fieldset>
          </form>
        ) : null}
        {review ? (
          <section className="cnc-review" data-region="confirmacion-autoridad">
            <h4>Revisar antes de guardar · {review.after.code}</h4>
            {diff(review.before, review.after)}
            <p>
              Los cambios quedan auditados y pueden reemplazar programas. El historial permite
              preparar una restauración para revisar antes de guardarla.
            </p>
            <label className="cnc-confirm">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
              />
              Revisé el cambio y su fuente. Confirmo guardar esta declaración.
            </label>
            <Button variant="primary" disabled={!confirmed || busy} onClick={() => void save()}>
              Guardar declaración revisada
            </Button>
          </section>
        ) : null}
        <section data-region="historial-autoridad">
          <h4>Historial de autoridad</h4>
          <p>Últimas 100 declaraciones; los datos anteriores se conservan.</p>
          {data?.history.length ? (
            <ol className="cnc-history">
              {data.history.map((event) => (
                <li key={event.id}>
                  <strong>
                    {(
                      {
                        CREATE: "Declarada",
                        UPDATE: "Actualizada",
                        RETIRE: "Retirada",
                        REACTIVATE: "Reactivada",
                      } as Record<string, string>
                    )[event.action] ?? "Cambio de autoridad"}{" "}
                    · {String(event.current.code)} · {String(event.current.name)}
                  </strong>
                  <p>
                    <span className="cnc-number">{formatDateTime(event.created_at)}</span> ·{" "}
                    {event.actor_label || "Servicio de datos"}
                  </p>
                  <details>
                    <summary>Ver cambio declarado</summary>
                    {diff(event.previous, event.current)}
                    {canWrite && event.previous ? (
                      <Button disabled={busy} onClick={() => restore(event)}>
                        Preparar restauración para revisar
                      </Button>
                    ) : null}
                  </details>
                </li>
              ))}
            </ol>
          ) : (
            <p>Aún no hay cambios registrados desde la activación del historial.</p>
          )}
        </section>
      </div>
    </details>
  );
}
