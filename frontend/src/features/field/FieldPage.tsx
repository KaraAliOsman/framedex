import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  fieldWorkspace,
  fieldSchedule,
  fieldAssetAccess,
  fieldReview,
  purchasingVersionState,
} from "../../api/generated/dekopen";
import type {
  FieldScheduleRequest,
  FieldReviewResponse,
  IncidentKindEnum,
  ResolutionKindEnum,
} from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import {
  DateOnly,
  Dims,
  Money,
  DemoBadge,
  LoadingState,
  ErrorState,
  DeniedState,
  EmptyState,
  BlockedState,
  ValidatedForm,
} from "../../ui";
import { PieceScanner } from "../production/PieceScanner";
import SignaturePad, { type SignaturePadHandle } from "../production/SignaturePad";
import { PositionThumb } from "../projects/PositionThumb";
import {
  detail,
  discardRejected,
  enqueue,
  flush,
  pending,
  readCopy,
  saveCopy,
  type Pending,
} from "./outbox";
import {
  labels,
  type Command,
  type FieldUnit,
  type Incident,
  type Visit,
  type Workspace,
} from "./types";
import "./field.css";

type Send = (visitId: string, body: Omit<Command, "operation_key">) => Promise<void>;
const checkLabels = {
  installed: "Instalada",
  levelled: "Nivelada",
  sealed: "Emitida",
  adjusted: "Regulada",
  clean: "Limpia",
};
const initialChecks = {
  installed: false,
  levelled: false,
  sealed: false,
  adjusted: false,
  clean: false,
};

function useConnection(): boolean {
  const [online, setOnline] = useState(navigator.onLine);
  useEffect(() => {
    const update = () => setOnline(navigator.onLine);
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);
  return online;
}

export function FieldPage({ office = false }: { office?: boolean }): JSX.Element {
  const Surface = office ? "section" : "main";
  const auth = useAuthSession();
  const current = useRef(auth);
  current.current = auth;
  const online = useConnection();
  const localMode = !online || auth.networkUnavailable === true;
  const [params, setParams] = useSearchParams();
  const [data, setData] = useState<Workspace>();
  const [queue, setQueue] = useState<Pending[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [denied, setDenied] = useState(false);
  const [copy, setCopy] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const actor = auth.session?.user.id;
  const org =
    auth.me?.active_organization?.id ??
    (actor ? localStorage.getItem(`dekopen.active_org.${actor}`) : null);
  const generation = useRef(0);
  const isLive = useCallback(
    () =>
      current.current.status === "ready" &&
      current.current.session?.user.id === actor &&
      current.current.me?.active_organization?.id === org,
    [actor, org],
  );
  const load = useCallback(async () => {
    if (!actor || !org) return;
    const turn = ++generation.current;
    setError("");
    try {
      if (!navigator.onLine || localMode) {
        const saved = await readCopy({ actor, org });
        if (turn !== generation.current) return;
        if (!saved)
          throw new Error(
            "Este teléfono no tiene una agenda guardada. Conéctate una vez y abre Terreno.",
          );
        setData(saved.workspace);
        setCopy(true);
      } else {
        if (!isLive()) return;
        const response = await fieldWorkspace({ headers: { "X-Organization-ID": org } });
        if (turn !== generation.current || !isLive()) return;
        const workspace = response.data as unknown as Workspace;
        await saveCopy({ actor, org }, workspace);
        setData(workspace);
        setCopy(false);
        setDenied(false);
      }
      const waiting = await pending({ actor, org });
      if (turn === generation.current) setQueue(waiting);
    } catch (caught) {
      if (turn === generation.current) {
        setError(detail(caught));
        setDenied(caught instanceof ApiError && caught.status === 403);
      }
    } finally {
      if (turn === generation.current) setLoading(false);
    }
  }, [actor, org, isLive, localMode]);
  const sync = useCallback(async () => {
    if (!actor || !org || !online) return;
    if (!isLive() || current.current.networkUnavailable) {
      await current.current.refreshContext();
      return;
    }
    setBusy(true);
    try {
      await flush({ actor, org }, isLive, load);
      await load();
      const remaining = await pending({ actor, org });
      setQueue(remaining);
      setNotice(
        remaining.length
          ? "Guardado en este teléfono · pendiente de sincronizar."
          : "Registros sincronizados con acceso vigente.",
      );
    } catch (caught) {
      setError(detail(caught));
      setQueue(await pending({ actor, org }));
    } finally {
      setBusy(false);
    }
  }, [actor, org, online, isLive, load]);
  useEffect(() => {
    setData(undefined);
    setQueue([]);
    setLoading(true);
    if (actor && org && (auth.status === "ready" || localMode)) void load();
    else if (auth.status !== "loading" && auth.status !== "resolving") setLoading(false);
    return () => {
      generation.current++;
    };
  }, [actor, org, auth.status, localMode, load]);
  useEffect(() => {
    if (actor && org && online && !localMode && isLive())
      void pending({ actor, org }).then((waiting) => {
        if (waiting.length && isLive()) void sync();
      });
  }, [actor, org, online, localMode, isLive, sync]);
  useEffect(() => {
    if (!import.meta.env.DEV && "serviceWorker" in navigator)
      void navigator.serviceWorker
        .register("/field-worker.js", { scope: "/" })
        .catch(() =>
          setNotice(
            "No se pudo preparar la recarga sin conexión. Conserva esta pestaña abierta y reintenta con señal.",
          ),
        );
  }, []);
  const send: Send = async (visitId, body) => {
    if (!actor || !org) throw new Error("Falta identificar esta sesión de terreno.");
    setError("");
    setNotice("");
    try {
      await enqueue({ actor, org }, visitId, { ...body, operation_key: crypto.randomUUID() });
      setQueue(await pending({ actor, org }));
      setNotice("Guardado en este teléfono · pendiente de sincronizar.");
      if (online && isLive()) await sync();
    } catch (caught) {
      setError(detail(caught));
      throw caught;
    }
  };
  const selected = data?.visits.find((v) => v.id === params.get("visit"));
  const fieldActorRole = data?.role ?? "";
  if (auth.status === "anonymous")
    return <DeniedState reason="Inicia sesión para abrir tu copia privada de terreno." />;
  if (loading || auth.status === "loading")
    return (
      <Surface className="field-page" data-density={office ? "office" : "workshop"}>
        <LoadingState label="Cargando tu ruta de obra" />
      </Surface>
    );
  if (denied || (!localMode && auth.status !== "ready"))
    return (
      <Surface className="field-page" data-density={office ? "office" : "workshop"}>
        <DeniedState reason="Tu acceso a terreno no está vigente. Pide al dueño o jefe de taller una asignación activa." />
      </Surface>
    );
  return (
    <Surface
      className={`field-page ${office ? "field-office" : ""}`}
      data-density={office ? "office" : "workshop"}
    >
      <header>
        <div>
          <h1>{office ? "Despacho y postventa" : "Terreno"}</h1>
          <p>
            {selected
              ? `${selected.code} · ${selected.context.project_name}`
              : office
                ? "Agenda entregas e instalaciones y sigue la postventa de cada obra."
                : "Tu ruta, tus posiciones y sus comprobantes"}
          </p>
        </div>
        <div className="field-tools">
          {!office ? <Link to="/dashboard">Hoy</Link> : null}
          <button
            type="button"
            className="ui-button"
            disabled={busy || !online}
            onClick={() => void sync()}
          >
            Sincronizar
          </button>
        </div>
      </header>
      <nav className="field-nav" aria-label="Trabajo en obra">
        <div className="ui-segmented">
          <button type="button" aria-pressed={!params.get("view")} onClick={() => setParams({})}>
            Agenda
          </button>
          {office && (
            <button
              type="button"
              aria-pressed={params.get("view") === "plan"}
              onClick={() => setParams({ view: "plan" })}
            >
              Planificar
            </button>
          )}
          <button
            type="button"
            aria-pressed={params.get("view") === "cases"}
            onClick={() => setParams({ view: "cases" })}
          >
            Postventa
          </button>
        </div>
        {!office && online && data?.role !== "INSTALLER" && (
          <Link to="/dispatch">Planificar salidas</Link>
        )}
      </nav>
      {(copy || !online) && (
        <p className="field-copy" role="status">
          Copia local · sin conexión. Los registros quedan pendientes hasta verificar tu acceso en
          el servidor.
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      {error && (
        <ErrorState
          title="No se pudo completar el registro"
          body={error}
          onRetry={() => void load()}
        />
      )}
      {queue.length > 0 && (
        <section aria-label="Registros pendientes" className="field-pending">
          <h2>Guardados en el teléfono</h2>
          {queue.map((p) => (
            <div key={p.key}>
              <p>
                {labels[p.command.kind]} · {p.failure ?? "Pendiente de sincronizar"}
              </p>
              {p.failureStatus && [400, 403, 404, 409, 422].includes(p.failureStatus) && (
                <details>
                  <summary>Resolver registro rechazado</summary>
                  <p>
                    Reintenta la misma operación si recuperaste el acceso. Si los datos eran
                    incorrectos, descarta este pendiente y registra los datos corregidos. La
                    evidencia del servidor se conserva.
                  </p>
                  <button
                    type="button"
                    className="secondary-action"
                    disabled={busy}
                    onClick={() => {
                      if (actor && org)
                        void discardRejected({ actor, org }, p.key)
                          .then(load)
                          .catch((caught) => setError(detail(caught)));
                    }}
                  >
                    Confirmar descarte del pendiente rechazado
                  </button>
                </details>
              )}
            </div>
          ))}
          <p>
            No son comprobantes aplicados. Mantén tu sesión para reintentar con la misma operación.
          </p>
        </section>
      )}
      {!data && !error && (
        <EmptyState
          title="No hay agenda guardada"
          body="Conéctate y abre Terreno para preparar el teléfono."
          action={
            <button type="button" onClick={() => void load()}>
              Cargar agenda
            </button>
          }
        />
      )}
      {data &&
        params.get("view") === "plan" &&
        (online ? (
          <Planner data={data} refresh={load} />
        ) : (
          <BlockedState
            reason="La planificación requiere acceso vigente. Conéctate para verificar las OTs y responsables."
            action={
              <button type="button" onClick={() => void load()}>
                Verificar conexión
              </button>
            }
          />
        ))}
      {data && params.get("view") === "cases" && (
        <Cases
          data={data}
          send={send}
          online={online}
          refresh={load}
          open={(id) => setParams({ visit: id })}
        />
      )}
      {data && selected && (
        <VisitDetail
          visit={selected}
          pending={queue.filter((p) => p.visitId === selected.id)}
          send={send}
          online={online}
          role={fieldActorRole}
          refresh={load}
        />
      )}
      {data && !selected && !params.get("view") && (
        <Agenda data={data} open={(id) => setParams({ visit: id })} office={office} />
      )}
    </Surface>
  );
}

function Agenda({
  data,
  open,
  office,
}: {
  data: Workspace;
  open: (id: string) => void;
  office: boolean;
}): JSX.Element {
  const [day, setDay] = useState("");
  const [team, setTeam] = useState("");
  const visits = data.visits.filter(
    (v) => (!day || v.planned_on === day) && (!team || v.team === team),
  );
  return (
    <section aria-label="Agenda de visitas">
      <div className="field-tools">
        <label>
          Fecha
          <input type="date" value={day} onChange={(e) => setDay(e.target.value)} />
        </label>
        <label>
          Equipo
          <select value={team} onChange={(e) => setTeam(e.target.value)}>
            <option value="">Todos tus equipos</option>
            {[...new Set(data.visits.map((v) => v.team))].map((t) => (
              <option key={t}>{t}</option>
            ))}
          </select>
        </label>
      </div>
      {visits.length === 0 ? (
        <EmptyState
          title="Sin visitas para esta selección"
          body={
            office
              ? "Agenda una obra con unidades reales y un responsable."
              : "El encargado aún no te ha asignado visitas. Pide tu ruta de obra."
          }
          action={
            <button
              type="button"
              onClick={() => {
                setDay("");
                setTeam("");
              }}
            >
              Ver toda la agenda
            </button>
          }
        />
      ) : (
        <div className="field-agenda">
          {visits.map((v) => (
            <article className="field-visit-row" key={v.id}>
              <div>
                <p className="ui-value">
                  {v.code} · <DateOnly value={v.planned_on} />
                </p>
                <h2>
                  {v.context.project_name ||
                    v.context.project_code ||
                    "Obra sin identificar · abre la visita"}
                </h2>
                <p>
                  {labels[v.kind]} · {labels[v.status]}
                </p>
                <p>{v.context.address}</p>
                <p>
                  {v.team} · {v.vehicle || "Vehículo pendiente · decláralo en la planificación"}
                </p>
              </div>
              <button type="button" className="secondary-action" onClick={() => open(v.id)}>
                Abrir obra
              </button>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function Planner({
  data,
  refresh,
}: {
  data: Workspace;
  refresh: () => Promise<void>;
}): JSX.Element {
  const [projectId, setProjectId] = useState("");
  const [versionId, setVersionId] = useState("");
  const [kind, setKind] = useState<FieldScheduleRequest["kind"]>("DELIVERY");
  const [assigned, setAssigned] = useState("");
  const [day, setDay] = useState("");
  const [team, setTeam] = useState("");
  const [vehicle, setVehicle] = useState("");
  const [address, setAddress] = useState("");
  const [units, setUnits] = useState<FieldScheduleRequest["units"]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const operation = useRef<string>();
  const project = data.projects.find((p) => p.id === projectId);
  const choices = project
    ? kind === "MEASUREMENT"
      ? project.positions.map((p) => ({
          position_id: p.position_id,
          unit_index: 1,
          label: `P${p.position_index} · ${p.location_tag}`,
          order_id: null,
        }))
      : project.orders
          .filter((o) => o.project_version_id === versionId)
          .flatMap((o) =>
            (o.packing.units ?? []).map((u) => ({
              ...u,
              order_id: o.id,
              label: `${u.label_code} · ${o.order_code}`,
            })),
          )
    : [];
  async function submit(): Promise<void> {
    setError("");
    setBusy(true);
    try {
      if (!projectId || !assigned || !day || !team.trim() || units.length === 0)
        throw new Error("Elige obra, responsable, fecha, equipo y al menos una unidad.");
      operation.current ??= crypto.randomUUID();
      await fieldSchedule({
        operation_key: operation.current,
        project_id: projectId,
        project_version_id: versionId || null,
        kind,
        assigned_to: assigned,
        planned_on: day,
        team,
        vehicle,
        address: address || undefined,
        units,
      });
      operation.current = undefined;
      setUnits([]);
      await refresh();
    } catch (caught) {
      setError(detail(caught));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="field-plan">
      <h2>Planifica la salida</h2>
      <ValidatedForm
        className="field-form"
        onSubmit={(e) => {
          e.preventDefault();
          void submit();
        }}
      >
        <label>
          Trabajo
          <select
            aria-label="Trabajo"
            value={kind}
            onChange={(e) => {
              setKind(e.target.value as typeof kind);
              setUnits([]);
              operation.current = undefined;
            }}
          >
            {["DELIVERY", "MEASUREMENT", "INSTALLATION", "SERVICE"]
              .filter((k) => data.role !== "ESTIMATOR" || k === "MEASUREMENT")
              .map((k) => (
                <option value={k} key={k}>
                  {labels[k]}
                </option>
              ))}
          </select>
        </label>
        <label>
          Obra
          <select
            aria-label="Obra"
            value={projectId}
            onChange={(e) => {
              setProjectId(e.target.value);
              setVersionId("");
              setUnits([]);
              operation.current = undefined;
            }}
          >
            <option value="">Elige una obra</option>
            {data.projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.code} · {p.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Revisión
          <select
            aria-label="Revisión"
            value={versionId}
            onChange={(e) => {
              setVersionId(e.target.value);
              setUnits([]);
              operation.current = undefined;
            }}
          >
            <option value="">
              {kind === "MEASUREMENT"
                ? "Borrador actual (si no ha sido emitido)"
                : "Elige una revisión emitida"}
            </option>
            {project?.versions.map((v) => (
              <option key={v.id} value={v.id}>
                {v.revision_code.replace("REV-", "Revisión ")}
              </option>
            ))}
          </select>
        </label>
        <label>
          Responsable
          <select
            aria-label="Responsable"
            value={assigned}
            onChange={(e) => {
              setAssigned(e.target.value);
              operation.current = undefined;
            }}
          >
            <option value="">Elige una persona</option>
            {data.assignees.map((p) => (
              <option key={p.user_id} value={p.user_id}>
                {p.display_name} · {labels[p.role]}
              </option>
            ))}
          </select>
        </label>
        <label>
          Día
          <input
            type="date"
            value={day}
            onChange={(e) => {
              setDay(e.target.value);
              operation.current = undefined;
            }}
          />
        </label>
        <label>
          Equipo
          <input
            value={team}
            onChange={(e) => {
              setTeam(e.target.value);
              operation.current = undefined;
            }}
            maxLength={120}
          />
        </label>
        <label>
          Vehículo
          <input
            value={vehicle}
            onChange={(e) => {
              setVehicle(e.target.value);
              operation.current = undefined;
            }}
            maxLength={120}
          />
        </label>
        <label>
          Dirección de obra
          <input
            value={address}
            onChange={(e) => {
              setAddress(e.target.value);
              operation.current = undefined;
            }}
            placeholder="Usar la dirección de la revisión emitida"
            maxLength={1000}
          />
        </label>
        <fieldset className="field-checks">
          <legend>
            {kind === "MEASUREMENT" ? "Posiciones por medir" : "Bultos reales de la revisión"}
          </legend>
          {kind === "SERVICE" && (
            <p>Una unidad por servicio: su trabajo, foto y firma quedan juntos.</p>
          )}
          {choices.length === 0 && (
            <p>Sin unidades disponibles · completa Embalaje o elige otra revisión.</p>
          )}
          {choices.map((c) => {
            const checked = units.some(
              (u) => u.position_id === c.position_id && u.unit_index === c.unit_index,
            );
            return (
              <label key={`${c.position_id}:${c.unit_index}`}>
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => {
                    operation.current = undefined;
                    setUnits(
                      checked
                        ? units.filter(
                            (u) => u.position_id !== c.position_id || u.unit_index !== c.unit_index,
                          )
                        : [
                            ...(kind === "SERVICE" ? [] : units),
                            {
                              position_id: c.position_id,
                              unit_index: c.unit_index,
                              order_id: c.order_id,
                            },
                          ],
                    );
                  }}
                />
                {c.label}
              </label>
            );
          })}
        </fieldset>
        {error && <p role="alert">{error}</p>}
        <button className="primary-action" type="submit" disabled={busy}>
          {busy ? "Agendando…" : "Agendar salida"}
        </button>
      </ValidatedForm>
    </section>
  );
}

async function preparePhoto(file: File): Promise<{ raw: string; url: string }> {
  if (!["image/jpeg", "image/png"].includes(file.type))
    throw new Error("Elige una foto PNG o JPEG.");
  if (file.size > 12_000_000)
    throw new Error("La foto supera 12 MB. Toma otra con menor resolución.");
  const bitmap = await createImageBitmap(file);
  try {
    const ratio = Math.min(1, 1600 / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(bitmap.width * ratio);
    canvas.height = Math.round(bitmap.height * ratio);
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("No se pudo preparar la foto.");
    ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    const url = canvas.toDataURL("image/jpeg", 0.82);
    const raw = url.split(",")[1]!;
    if (raw.length > 2_000_000)
      throw new Error("La foto preparada excede el límite. Toma otra foto.");
    return { raw, url };
  } finally {
    bitmap.close();
  }
}

function Photo({ change }: { change: (value: string) => void }): JSX.Element {
  const [preview, setPreview] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <div>
      <label>
        Foto de esta posición
        <input
          type="file"
          accept="image/jpeg,image/png"
          capture="environment"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (!file) return;
            setBusy(true);
            setError("");
            void preparePhoto(file)
              .then((p) => {
                setPreview(p.url);
                change(p.raw);
              })
              .catch((caught) => {
                change("");
                setPreview("");
                setError(detail(caught));
              })
              .finally(() => setBusy(false));
          }}
        />
      </label>
      {busy && <p role="status">Preparando foto…</p>}
      {preview && (
        <img
          className="field-preview-photo"
          src={preview}
          alt="Evidencia de esta posición en obra"
        />
      )}
      {error && <p role="alert">{error}</p>}
    </div>
  );
}

function VisitDetail({
  visit,
  pending: waiting,
  send,
  online,
  role,
  refresh,
}: {
  visit: Visit;
  pending: Pending[];
  send: Send;
  online: boolean;
  role: string;
  refresh: () => Promise<void>;
}): JSX.Element {
  const [index, setIndex] = useState(0);
  const unit = (visit.context.units[index] ?? visit.context.units[0])!;
  const [scan, setScan] = useState("");
  const [scanNotice, setScanNotice] = useState("");
  const scannedSelection = useRef("");
  const [photo, setPhoto] = useState("");
  const [checks, setChecks] = useState({ ...initialChecks });
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const events = [
    ...visit.events,
    ...waiting.map((p) => ({
      id: p.key,
      sequence: 0,
      kind: p.command.kind,
      payload_json: p.command as unknown as Record<string, unknown>,
      pending: true,
    })),
  ];
  const last = events
    .filter(
      (e) =>
        e.kind === "CHECK" &&
        e.payload_json.position_id === unit.position_id &&
        e.payload_json.unit_index === unit.unit_index,
    )
    .at(-1);
  useEffect(() => {
    setScan(scannedSelection.current);
    scannedSelection.current = "";
    setPhoto("");
    setChecks({ ...initialChecks });
    setNote("");
    setError("");
  }, [unit.position_id, unit.unit_index, visit.id]);
  async function save(kind: Command["kind"]): Promise<void> {
    setBusy(true);
    setError("");
    try {
      await send(visit.id, {
        kind,
        position_id: unit.position_id,
        unit_index: unit.unit_index,
        scan,
        photo_b64: photo || undefined,
        checks: kind === "CHECK" ? checks : undefined,
        note,
      });
      setPhoto("");
    } catch (caught) {
      setError(detail(caught));
    } finally {
      setBusy(false);
    }
  }
  function scanned(text: string): void {
    // Local address selection is a convenience; backend validates its identity.
    let code = text;
    try {
      const url = new URL(text, window.location.origin);
      code = url.searchParams.get("piece") ?? text;
    } catch {
      /* Manual code */
    }
    const selected = visit.context.units.findIndex(
      (u) =>
        text === u.label_code ||
        text.includes(`|${u.label_code}|`) ||
        code.startsWith(
          `P${String(u.position_index).padStart(2, "0")}-U${String(u.unit_index).padStart(2, "0")}`,
        ),
    );
    if (selected >= 0 && selected !== index) {
      scannedSelection.current = text;
      setIndex(selected);
    }
    setScan(text);
    setScanNotice("Etiqueta seleccionada · se verificará con la revisión al sincronizar.");
  }
  return (
    <section>
      <h2>
        {visit.context.project_code} · {labels[visit.kind]} · {labels[visit.status]}
      </h2>
      <p>{visit.context.address}</p>
      <div className="field-tools">
        <a
          href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(visit.context.address)}`}
          target="_blank"
          rel="noreferrer"
        >
          Abrir mapas
        </a>
        {visit.context.contact_phone && (
          <a href={`tel:${visit.context.contact_phone}`}>Llamar al contacto</a>
        )}
      </div>
      <p>
        {visit.team} · <DateOnly value={visit.planned_on} />
      </p>
      <nav className="field-tools" aria-label="Posición en obra">
        {visit.context.units.map((u, at) => (
          <button
            key={`${u.position_id}:${u.unit_index}`}
            type="button"
            className="secondary-action"
            aria-pressed={at === index}
            onClick={() => setIndex(at)}
          >
            P{String(u.position_index).padStart(2, "0")} · U{String(u.unit_index).padStart(2, "0")}
          </button>
        ))}
      </nav>
      <article className="field-unit" key={`${unit.position_id}:${unit.unit_index}`}>
        <p className="field-unit-code">
          P{String(unit.position_index).padStart(2, "0")} · U
          {String(unit.unit_index).padStart(2, "0")}
        </p>
        <p>
          {unit.location_tag} · {visit.context.revision_code.replace("REV-", "Revisión ")}
        </p>
        {unit.is_demo && <DemoBadge />}
        <div className="field-drawing">
          <PositionThumb design={unit.design} />
          <p>
            Vista interior ·{" "}
            <Dims w={unit.design.nominal_width_mm} h={unit.design.nominal_height_mm} />
          </p>
        </div>
        <p className="ui-value">{unit.order_code || "Sin OT · medición previa a fabricación"}</p>
        {unit.order_id && (
          <PieceScanner value={scan} onChange={setScan} onScan={scanned} busy={busy} />
        )}
        {scanNotice && <p role="status">{scanNotice}</p>}
        {last && (
          <p role="status">
            {last.pending
              ? "Comprobaciones guardadas en el teléfono · pendientes"
              : "Comprobaciones acreditadas en la visita"}
          </p>
        )}
        {visit.status !== "CLOSED" &&
          visit.status !== "CANCELLED" &&
          visit.kind === "INSTALLATION" && (
            <ValidatedForm
              className="field-form"
              onSubmit={(e) => {
                e.preventDefault();
                void save("CHECK");
              }}
            >
              <fieldset className="field-checks">
                <legend>Comprueba la posición</legend>
                {Object.entries(checkLabels).map(([key, label]) => (
                  <label key={key}>
                    <input
                      type="checkbox"
                      checked={checks[key as keyof typeof checks]}
                      onChange={(e) => setChecks({ ...checks, [key]: e.target.checked })}
                    />
                    {label}
                  </label>
                ))}
              </fieldset>
              <Photo change={setPhoto} />
              <label>
                Observaciones
                <input value={note} onChange={(e) => setNote(e.target.value)} maxLength={2000} />
              </label>
              <button className="primary-action" type="submit" disabled={busy || !scan || !photo}>
                {busy ? "Guardando…" : "Guardar comprobaciones y foto"}
              </button>
            </ValidatedForm>
          )}
        {visit.kind === "DELIVERY" &&
          visit.status !== "CLOSED" &&
          visit.status !== "CANCELLED" &&
          !visit.events.some((e) => e.kind === "DEPART") && (
            <div className="field-tools">
              <button
                type="button"
                className="primary-action"
                disabled={busy || !scan}
                onClick={() => void save("LOAD")}
              >
                Confirmar bulto cargado
              </button>
              <p>
                La guía conserva exactamente los bultos del viaje. El encargado confirma la salida y
                el cliente firma la entrega aquí.
              </p>
            </div>
          )}
        {visit.status !== "CANCELLED" && visit.kind !== "DELIVERY" && (
          <details>
            <summary>Medir y rectificar el vano</summary>
            <Survey unit={unit} visit={visit} photo={photo} setPhoto={setPhoto} send={send} />
          </details>
        )}
        <details>
          <summary>Reportar incidencia o postventa</summary>
          <IncidentForm visit={visit} unit={unit} scan={scan} send={send} />
        </details>
        <details>
          <summary>Materiales de esta ventana</summary>
          <Materials value={unit.materials} />
          {online && unit.order_id && (
            <Link to={`/production?order=${unit.order_id}`}>Ver trazabilidad de la OT</Link>
          )}
        </details>
      </article>
      {visit.kind === "DELIVERY" &&
        visit.status !== "CLOSED" &&
        visit.status !== "CANCELLED" &&
        !visit.events.some((e) => e.kind === "DEPART") &&
        (role === "OWNER" || role === "WORKSHOP_MANAGER") && (
          <button
            type="button"
            className="primary-action"
            disabled={busy || !online}
            onClick={() => void send(visit.id, { kind: "DEPART", confirmed: true })}
          >
            Confirmar carga, emitir guía y salir
          </button>
        )}
      {(visit.kind === "INSTALLATION" ||
        visit.kind === "SERVICE" ||
        (visit.kind === "DELIVERY" && visit.events.some((e) => e.kind === "DEPART"))) &&
        visit.status !== "CLOSED" &&
        visit.status !== "CANCELLED" && (
          <details>
            <summary>Recepción del cliente</summary>
            <Reception visit={visit} send={send} />
          </details>
        )}
      {visit.assets
        .filter((a) => a.kind === "ACT")
        .map((a) => (
          <section key={a.id}>
            <p>Acta emitida · inmutable</p>
            <AssetButton assetId={a.id} online={online} label="Abrir acta PDF" />
          </section>
        ))}
      {(role === "OWNER" || role === "ESTIMATOR") &&
        online &&
        visit.events.some((e) => e.kind === "MEASURE") && (
          <Review visit={visit} refresh={refresh} />
        )}
      {(role === "OWNER" || role === "WORKSHOP_MANAGER") &&
        visit.status !== "CLOSED" &&
        visit.status !== "CANCELLED" && (
          <details>
            <summary>Cancelar esta visita</summary>
            <p>La visita se cancelará y su evidencia se conservará.</p>
            <button
              type="button"
              className="secondary-action"
              onClick={() => {
                void send(visit.id, {
                  kind: "CANCEL",
                  note: "Cancelación explícita del encargado",
                }).catch((caught) => setError(detail(caught)));
              }}
            >
              Confirmar cancelación
            </button>
          </details>
        )}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}

function Survey({
  unit,
  visit,
  photo,
  setPhoto,
  send,
}: {
  unit: FieldUnit;
  visit: Visit;
  photo: string;
  setPhoto: (v: string) => void;
  send: Send;
}): JSX.Element {
  const [widths, setWidths] = useState(["", "", ""]);
  const [heights, setHeights] = useState(["", "", ""]);
  const [wall, setWall] = useState("MASONRY");
  const [rule, setRule] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const modules = (unit.design.parametric_tree as { assembly?: { modules: { id: string }[] } })
    .assembly?.modules;
  const [module, setModule] = useState(modules?.[0]?.id ?? "");
  const [measured, setMeasured] = useState<Record<string, object>>({});
  function currentSurvey(): object {
    const authority = unit.mounting_rules.find((r) => `${r.rule.code}:${r.revision}` === rule);
    if (!authority || [...widths, ...heights].some((v) => !/^\d+(?:[.,]\d{1,2})?$/.test(v)))
      throw new Error("Completa tres medidas por eje y el montaje con origen de este marco.");
    return {
      module_id: module || null,
      rule_code: authority.rule.code,
      rule_revision: authority.revision,
      widths_mm: widths.map((v) => v.replace(",", ".")),
      heights_mm: heights.map((v) => v.replace(",", ".")),
      wall,
      origin: "SITE",
    };
  }
  async function submit(): Promise<void> {
    setBusy(true);
    setError("");
    try {
      const authority = unit.mounting_rules.find((r) => `${r.rule.code}:${r.revision}` === rule);
      if (
        !authority ||
        !photo ||
        [...widths, ...heights].some((v) => !/^\d+(?:[.,]\d{1,2})?$/.test(v))
      )
        throw new Error(
          "Completa tres medidas por eje, montaje con origen y foto de esta posición.",
        );
      const all = { ...measured, [module || "single"]: currentSurvey() };
      if (modules && modules.some((m) => !all[m.id]))
        throw new Error(
          "Guarda la medición de todos los marcos del conjunto antes de enviarla a revisión.",
        );
      await send(visit.id, {
        kind: "MEASURE",
        position_id: unit.position_id,
        unit_index: unit.unit_index,
        photo_b64: photo,
        measurements: Object.values(all),
        note: "Medición tomada en obra; pendiente de revisión del estimador",
      });
    } catch (caught) {
      setError(detail(caught));
    } finally {
      setBusy(false);
    }
  }
  return (
    <ValidatedForm
      className="field-form"
      onSubmit={(e) => {
        e.preventDefault();
        void submit();
      }}
    >
      {modules && (
        <label>
          Marco del conjunto
          <select
            value={module}
            onChange={(e) => {
              setModule(e.target.value);
              setWidths(["", "", ""]);
              setHeights(["", "", ""]);
            }}
          >
            {modules.map((m, i) => (
              <option value={m.id} key={m.id}>
                Marco {i + 1}
              </option>
            ))}
          </select>
        </label>
      )}
      <fieldset>
        <legend>Ancho del vano · mm</legend>
        <div className="field-survey">
          {["Arriba", "Centro", "Abajo"].map((label, i) => (
            <label key={label}>
              {label}
              <input
                inputMode="decimal"
                value={widths[i]}
                onChange={(e) => setWidths(widths.map((v, at) => (at === i ? e.target.value : v)))}
              />
            </label>
          ))}
        </div>
      </fieldset>
      <fieldset>
        <legend>Alto del vano · mm</legend>
        <div className="field-survey">
          {["Izquierda", "Centro", "Derecha"].map((label, i) => (
            <label key={label}>
              {label}
              <input
                inputMode="decimal"
                value={heights[i]}
                onChange={(e) =>
                  setHeights(heights.map((v, at) => (at === i ? e.target.value : v)))
                }
              />
            </label>
          ))}
        </div>
      </fieldset>
      <label>
        Muro
        <select value={wall} onChange={(e) => setWall(e.target.value)}>
          {[
            ["MASONRY", "Albañilería"],
            ["CONCRETE", "Hormigón"],
            ["PARTITION", "Tabique"],
            ["WOOD", "Madera"],
          ].map(([value, label]) => (
            <option value={value} key={value}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <label>
        Montaje con origen
        <select value={rule} onChange={(e) => setRule(e.target.value)}>
          <option value="">Elige la regla de la serie</option>
          {unit.mounting_rules.map((r) => (
            <option key={`${r.rule.code}:${r.revision}`} value={`${r.rule.code}:${r.revision}`}>
              {r.rule.name} · revisión {r.revision}
              {r.rule.synthetic ? " · DEMO" : ""}
            </option>
          ))}
        </select>
      </label>
      {unit.mounting_rules.length === 0 && (
        <p>
          Falta completar · la serie no tiene una regla de montaje. El jefe de taller debe
          declararla en Vano y montaje.
        </p>
      )}
      <Photo change={setPhoto} />
      {modules && (
        <div>
          <button
            type="button"
            className="secondary-action"
            onClick={() => {
              try {
                setMeasured({ ...measured, [module]: currentSurvey() });
                setError("");
              } catch (caught) {
                setError(detail(caught));
              }
            }}
          >
            Guardar medidas de este marco
          </button>
          <p>
            {modules
              .map((m, i) => `Marco ${i + 1}: ${measured[m.id] ? "medido" : "pendiente"}`)
              .join(" · ")}
          </p>
        </div>
      )}
      {error && <p role="alert">{error}</p>}
      <button type="submit" className="primary-action" disabled={busy}>
        Guardar medición para revisión
      </button>
    </ValidatedForm>
  );
}

function IncidentForm({
  visit,
  unit,
  scan,
  send,
}: {
  visit: Visit;
  unit: FieldUnit;
  scan: string;
  send: Send;
}): JSX.Element {
  const [kind, setKind] = useState<IncidentKindEnum>("DAMAGE");
  const [note, setNote] = useState("");
  const [photo, setPhoto] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(): Promise<void> {
    setBusy(true);
    setError("");
    try {
      if (!note.trim() || !photo)
        throw new Error("Describe la incidencia y toma una foto de esta posición.");
      await send(visit.id, {
        kind: "INCIDENT",
        position_id: unit.position_id,
        unit_index: unit.unit_index,
        scan: scan || undefined,
        incident_kind: kind,
        note,
        photo_b64: photo,
      });
      setNote("");
      setPhoto("");
    } catch (caught) {
      setError(detail(caught));
    } finally {
      setBusy(false);
    }
  }
  return (
    <ValidatedForm
      className="field-form"
      onSubmit={(e) => {
        e.preventDefault();
        void submit();
      }}
    >
      <label>
        Tipo
        <select
          aria-label="Tipo"
          value={kind}
          onChange={(e) => setKind(e.target.value as IncidentKindEnum)}
        >
          {["DAMAGE", "MEASURE", "MISSING", "ADJUSTMENT", "WARRANTY", "SERVICE"].map((k) => (
            <option key={k} value={k}>
              {labels[k]}
            </option>
          ))}
        </select>
      </label>
      <label>
        Qué ocurrió
        <textarea value={note} onChange={(e) => setNote(e.target.value)} maxLength={2000} />
      </label>
      <Photo change={setPhoto} />
      {error && <p role="alert">{error}</p>}
      <button type="submit" className="primary-action" disabled={busy}>
        Guardar incidencia con trazabilidad
      </button>
    </ValidatedForm>
  );
}

function Reception({ visit, send }: { visit: Visit; send: Send }): JSX.Element {
  const signature = useRef<SignaturePadHandle>(null);
  const [name, setName] = useState("");
  const [rut, setRut] = useState("");
  const [note, setNote] = useState("");
  const [photo, setPhoto] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(): Promise<void> {
    setBusy(true);
    setError("");
    try {
      const png = signature.current?.dataURL();
      if (!name.trim() || !rut.trim() || !png || !confirmed)
        throw new Error("Complete su nombre, RUT y firma; revise las unidades antes de confirmar.");
      await send(visit.id, {
        kind: visit.kind === "DELIVERY" ? "DELIVER" : "RECEIVE",
        receiver_name: name,
        receiver_rut: rut,
        signature_b64: png.split(",")[1],
        confirmed,
        note,
        photo_b64: photo || undefined,
      });
    } catch (caught) {
      setError(detail(caught));
    } finally {
      setBusy(false);
    }
  }
  return (
    <ValidatedForm
      className="field-form"
      onSubmit={(e) => {
        e.preventDefault();
        void submit();
      }}
    >
      <p>
        Usted recibe las unidades de esta visita. Las observaciones e incidencias se conservarán en
        el acta.
      </p>
      <label>
        Nombre de quien recibe
        <input value={name} onChange={(e) => setName(e.target.value)} maxLength={255} />
      </label>
      <label>
        RUT
        <input value={rut} onChange={(e) => setRut(e.target.value)} maxLength={30} />
      </label>
      <label>
        Observaciones
        <textarea value={note} onChange={(e) => setNote(e.target.value)} maxLength={2000} />
      </label>
      {visit.kind === "SERVICE" && <Photo change={setPhoto} />}
      <div className="field-signature" data-theme="light">
        <SignaturePad ref={signature} />
      </div>
      <button
        type="button"
        className="secondary-action"
        disabled={!name.trim()}
        onClick={() => signature.current?.renderTyped(name)}
      >
        Firmar con mi nombre
      </button>
      <label className="field-checks">
        <input
          type="checkbox"
          checked={confirmed}
          onChange={(e) => setConfirmed(e.target.checked)}
        />
        Confirmo que revisé las unidades y autorizo emitir esta recepción.
      </label>
      {error && <p role="alert">{error}</p>}
      <button type="submit" className="primary-action" disabled={busy}>
        {busy ? "Guardando recepción…" : "Firmar y emitir recepción"}
      </button>
    </ValidatedForm>
  );
}

function Materials({ value }: { value: Record<string, unknown[]> }): JSX.Element {
  const names: Record<string, string> = {
    profile_cuts: "Perfiles",
    reinforcements: "Refuerzos",
    glasses: "Vidrios",
    panels: "Paneles",
    hardware_items: "Herrajes",
    fittings: "Accesorios",
  };
  return (
    <div>
      {Object.entries(value)
        .filter(([, items]) => items.length > 0)
        .map(([kind, items]) => (
          <section key={kind}>
            <h2>{names[kind] ?? "Materiales"}</h2>
            {items.map((raw, i) => {
              const item = raw as Record<string, unknown>;
              return (
                <p key={i}>
                  {String(
                    item.commercial_sku ??
                      item.workshop_sku ??
                      item.article_code ??
                      item.code ??
                      item.name ??
                      "Material sin nombre · revisar la OT",
                  )}
                </p>
              );
            })}
          </section>
        ))}
    </div>
  );
}

function AssetButton({
  assetId,
  online,
  label,
}: {
  assetId: string;
  online: boolean;
  label: string;
}): JSX.Element {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <div>
      <button
        type="button"
        className="secondary-action"
        disabled={!online || busy}
        onClick={() => {
          setBusy(true);
          setError("");
          void fieldAssetAccess(assetId)
            .then((r) => {
              if (r.status === 200) window.open(r.data.signed_url, "_blank", "noopener");
            })
            .catch((caught) => setError(detail(caught)))
            .finally(() => setBusy(false));
        }}
      >
        {label}
      </button>
      {!online && <p>El acceso privado se verifica al recuperar conexión.</p>}
      {error && <p role="alert">{error}</p>}
    </div>
  );
}

function Review({ visit, refresh }: { visit: Visit; refresh: () => Promise<void> }): JSX.Element {
  const [selected, setSelected] = useState("");
  const [reason, setReason] = useState("");
  const [proposal, setProposal] = useState<FieldReviewResponse>();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function review(confirmed: boolean): Promise<void> {
    setBusy(true);
    setError("");
    try {
      const r = await fieldReview(visit.id, {
        measurement_event_id: selected,
        reason,
        confirmed,
        proposal_token: confirmed ? proposal?.proposal_token : undefined,
      });
      if (r.status === 200) {
        setProposal(r.data);
        if (r.data.applied) await refresh();
      }
    } catch (caught) {
      setError(detail(caught));
    } finally {
      setBusy(false);
    }
  }
  const change = proposal?.price_change as
    | {
        before_net?: string;
        after_net?: string;
        delta_net?: string;
        currency?: string;
        reason?: string;
      }
    | undefined;
  return (
    <details>
      <summary>Revisar rectificación · estimador</summary>
      <ValidatedForm
        className="field-form"
        onSubmit={(e) => {
          e.preventDefault();
          void review(false);
        }}
      >
        <label>
          Medición
          <select
            value={selected}
            onChange={(e) => {
              setSelected(e.target.value);
              setProposal(undefined);
            }}
          >
            <option value="">Elige la evidencia de obra</option>
            {visit.events
              .filter((e) => e.kind === "MEASURE")
              .map((e) => (
                <option value={e.id} key={e.id}>
                  Medición {e.sequence} · unidad {String(e.payload_json.unit_index)}
                </option>
              ))}
          </select>
        </label>
        <label>
          Motivo
          <input
            value={reason}
            onChange={(e) => {
              setReason(e.target.value);
              setProposal(undefined);
            }}
            maxLength={1000}
          />
        </label>
        <button type="submit" className="secondary-action" disabled={busy || !reason || !selected}>
          Calcular fabricación y diferencia
        </button>
      </ValidatedForm>
      {proposal && (
        <section>
          <p>
            {proposal.scope ??
              "La revisión emitida se conserva; la rectificación abre su sucesora."}
          </p>
          {change?.reason ? (
            <p>Falta completar · {change.reason}</p>
          ) : (
            <p>
              Antes <Money value={change?.before_net} currency={change?.currency} /> · Después{" "}
              <Money value={change?.after_net} currency={change?.currency} /> · Δ{" "}
              <Money value={change?.delta_net} currency={change?.currency} />
            </p>
          )}
          {proposal.applied ? (
            <Link to={`/projects/${proposal.project_id}`}>
              Abrir {proposal.project_code} · revisión pendiente de liberación
            </Link>
          ) : (
            <button
              type="button"
              className="primary-action"
              disabled={busy}
              onClick={() => void review(true)}
            >
              Confirmar borrador rectificado
            </button>
          )}
        </section>
      )}
      {error && <p role="alert">{error}</p>}
    </details>
  );
}

function Cases({
  data,
  send,
  online,
  refresh,
  open,
}: {
  data: Workspace;
  send: Send;
  online: boolean;
  refresh: () => Promise<void>;
  open: (id: string) => void;
}): JSX.Element {
  const [params] = useSearchParams();
  const exactCase = params.get("case");
  const [filter, setFilter] = useState(exactCase ? "" : "OPEN");
  const cases = data.incidents.filter(
    (c) => (!exactCase || c.id === exactCase) && (!filter || c.status === filter),
  );
  return (
    <section>
      <h2>Postventa con trazabilidad</h2>
      <label>
        Estado
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="">Todos</option>
          {["OPEN", "PLANNED", "CLOSED"].map((k) => (
            <option value={k} key={k}>
              {labels[k]}
            </option>
          ))}
        </select>
      </label>
      {cases.length === 0 ? (
        <EmptyState
          title="Sin incidencias en este estado"
          body="Cada reporte de obra conserva posición, unidad y materiales de su revisión."
          action={
            <button type="button" onClick={() => setFilter("")}>
              Ver todo el historial
            </button>
          }
        />
      ) : (
        cases.map((c) => (
          <Case
            key={c.id}
            incident={c}
            data={data}
            send={send}
            online={online}
            refresh={refresh}
            open={open}
          />
        ))
      )}
    </section>
  );
}

function Case({
  incident: c,
  data,
  send,
  online,
  open,
}: {
  incident: Incident;
  data: Workspace;
  send: Send;
  online: boolean;
  refresh: () => Promise<void>;
  open: (id: string) => void;
}): JSX.Element {
  const [note, setNote] = useState(c.diagnosis ?? "");
  const [action, setAction] = useState<ResolutionKindEnum>(
    c.kind === "DAMAGE" ? "REMAKE" : c.kind === "MISSING" ? "PURCHASE" : "SERVICE",
  );
  const [day, setDay] = useState("");
  const [assigned, setAssigned] = useState("");
  const [requirement, setRequirement] = useState("");
  const [quantity, setQuantity] = useState("");
  const [requirements, setRequirements] = useState<{ id: string; label: string }[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const supervisor = ["OWNER", "WORKSHOP_MANAGER"].includes(data.role);
  const visit = data.visits.find((v) => v.id === c.visit_id);
  async function solve(kind: Command["kind"]): Promise<void> {
    setBusy(true);
    setError("");
    try {
      if (!note.trim()) throw new Error("Declara el diagnóstico o el motivo del cierre.");
      await send(c.visit_id, {
        kind,
        incident_id: c.id,
        note,
        resolution_kind: kind === "RESOLVE" ? action : undefined,
        confirmed: kind === "RESOLVE",
        planned_on: action === "SERVICE" ? day || undefined : undefined,
        assigned_to: action === "SERVICE" ? assigned || undefined : undefined,
        requirement_id: action === "PURCHASE" ? requirement || undefined : undefined,
        quantity: action === "PURCHASE" ? Number(quantity) || undefined : undefined,
      });
    } catch (caught) {
      setError(detail(caught));
    } finally {
      setBusy(false);
    }
  }
  async function loadRequirements(): Promise<void> {
    if (!visit?.project_version_id) return;
    try {
      const r = await purchasingVersionState(visit.project_version_id);
      const raw = r.data as unknown as {
        requirements: { id: string; purchasing_sku: string; source_position_ids: string[] }[];
      };
      setRequirements(
        (raw.requirements ?? [])
          .filter((r) => r.source_position_ids.includes(c.position_id))
          .map((r) => ({ id: r.id, label: r.purchasing_sku })),
      );
    } catch (caught) {
      setError(detail(caught));
    }
  }
  return (
    <article className="field-case">
      <h2>
        {c.code} · {labels[c.kind]} · {labels[c.status]}
      </h2>
      <p>
        {c.context.project_name} · {c.context.project_code} · {c.context.contact_name}
      </p>
      <p>{c.description}</p>
      <button type="button" className="secondary-action" onClick={() => open(c.visit_id)}>
        Abrir ventana y visita de origen
      </button>
      {c.evidence.photo?.id ? (
        <AssetButton assetId={c.evidence.photo.id} online={online} label="Abrir foto contextual" />
      ) : (
        <p>Sin fotografía en este registro. Abre la visita de origen para revisar su evidencia.</p>
      )}
      <p>
        Garantía:{" "}
        {c.warranty.expires_on ? (
          <>
            <DateOnly value={c.warranty.started_on} /> a <DateOnly value={c.warranty.expires_on} />
          </>
        ) : (
          c.warranty.reason
        )}
      </p>
      {c.warranty.text && <p>{c.warranty.text}</p>}
      <details>
        <summary>Perfiles, vidrios y herrajes de origen</summary>
        {c.evidence.materials ? (
          <Materials value={c.evidence.materials} />
        ) : (
          <p>
            Sin materiales en este registro. Abre la revisión de origen para consultar su despiece.
          </p>
        )}
      </details>
      {c.resolution.remake_order_id && (
        <Link to={`/production?order=${c.resolution.remake_order_id}`}>
          Abrir {c.resolution.remake_code}
        </Link>
      )}
      {c.resolution.purchase_order_id && (
        <Link to="/purchasing">Abrir compra {c.resolution.purchase_code}</Link>
      )}
      {c.resolution.service_visit_id && (
        <button
          type="button"
          className="secondary-action"
          onClick={() => open(c.resolution.service_visit_id!)}
        >
          Abrir servicio {c.resolution.service_code}
        </button>
      )}
      {c.resolution.corrective_project_id && (
        <Link to={`/projects/${c.resolution.corrective_project_id}`}>
          Abrir corrección {c.resolution.project_code}
        </Link>
      )}
      {c.status !== "CLOSED" && (
        <details>
          <summary>Diagnóstico y solución</summary>
          <ValidatedForm
            className="field-form"
            onSubmit={(e) => {
              e.preventDefault();
              void solve("DIAGNOSE");
            }}
          >
            <label>
              Diagnóstico
              <textarea value={note} onChange={(e) => setNote(e.target.value)} maxLength={2000} />
            </label>
            <button type="submit" className="secondary-action" disabled={busy}>
              Guardar diagnóstico
            </button>
          </ValidatedForm>
          {c.kind === "MEASURE" && c.status === "OPEN" && (
            <p>
              Registra la medición en la visita y pide al estimador revisar su fabricación y precio.
              La OT anterior se conserva.
            </p>
          )}
          {supervisor && c.status === "OPEN" && c.kind !== "MEASURE" && (
            <ValidatedForm
              className="field-form"
              onSubmit={(e) => {
                e.preventDefault();
                void solve("RESOLVE");
              }}
            >
              <label>
                Solución
                <select
                  value={action}
                  onChange={(e) => setAction(e.target.value as ResolutionKindEnum)}
                >
                  {(c.kind === "DAMAGE"
                    ? ["REMAKE", "SERVICE"]
                    : c.kind === "MISSING"
                      ? ["PURCHASE", "SERVICE"]
                      : ["SERVICE"]
                  ).map((k) => (
                    <option key={k} value={k}>
                      {k === "REMAKE"
                        ? "Reponer una unidad"
                        : k === "PURCHASE"
                          ? "Comprar material faltante"
                          : "Agendar servicio"}
                    </option>
                  ))}
                </select>
              </label>
              {action === "SERVICE" && (
                <>
                  <label>
                    Día de visita
                    <input type="date" value={day} onChange={(e) => setDay(e.target.value)} />
                  </label>
                  <label>
                    Responsable
                    <select value={assigned} onChange={(e) => setAssigned(e.target.value)}>
                      <option value="">Elige una persona</option>
                      {data.assignees.map((p) => (
                        <option key={p.user_id} value={p.user_id}>
                          {p.display_name} · {labels[p.role]}
                        </option>
                      ))}
                    </select>
                  </label>
                </>
              )}
              {action === "PURCHASE" && (
                <>
                  <button
                    type="button"
                    className="secondary-action"
                    disabled={!online}
                    onClick={() => void loadRequirements()}
                  >
                    Ver requerimientos emitidos
                  </button>
                  <label>
                    Material faltante
                    <select value={requirement} onChange={(e) => setRequirement(e.target.value)}>
                      <option value="">Elige el requerimiento de esta posición</option>
                      {requirements.map((r) => (
                        <option value={r.id} key={r.id}>
                          {r.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Cantidad física confirmada
                    <input
                      inputMode="numeric"
                      value={quantity}
                      onChange={(e) => setQuantity(e.target.value)}
                    />
                  </label>
                  <p>
                    La compra conserva la asignación del proveedor elegible. No modifica pedidos
                    anteriores; el precio lo completa la oficina.
                  </p>
                </>
              )}
              <p>
                {action === "REMAKE"
                  ? "Se creará una OT nueva de una unidad, con plan nuevo y datos conservados."
                  : "Se conservará la evidencia de la incidencia y su solución."}
              </p>
              <button type="submit" className="primary-action" disabled={busy}>
                Confirmar solución
              </button>
            </ValidatedForm>
          )}
          {c.status === "PLANNED" && (
            <button
              type="button"
              className="secondary-action"
              disabled={busy}
              onClick={() => void solve("CLOSE")}
            >
              Cerrar con diagnóstico y evidencia cumplida
            </button>
          )}
          {error && <p role="alert">{error}</p>}
        </details>
      )}
    </article>
  );
}
