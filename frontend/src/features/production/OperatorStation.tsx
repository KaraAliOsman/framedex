import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  productionOperatorStation,
  productionOperatorStationSelect,
  productionStationQueue,
  productionOrderDetail,
  productionOrderTrace,
  productionPieceTrace,
  productionStepTransition,
} from "../../api/generated/dekopen";
import type {
  OperatorStation,
  ProductionOrderDetail,
  ProductionOrderTrace,
  StepTransitionRequestRequest,
} from "../../api/generated/models";
import { useTheme } from "../../theme/ThemeProvider";
import { ApiError } from "../../api/apiMutator";
import { useAssistantSurface } from "../assistant/assistantContext";
import {
  BlockedState,
  DeniedState,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  TechDetails,
  ValidatedForm,
} from "../../ui";
import { domainLabels } from "../../i18n/domainLabels";
import { fmtMm, formatDecimal } from "../../format";
import {
  PLAN_REQUIRED_CODES,
  STEP_STOCK_KINDS,
  cutRoleLabel,
  opFaceLabel,
  opBoundaryLabel,
  opKindLabel,
  opReferenceLabel,
  stationCodeLabel,
} from "./labels";
import { orderPieces, pieceMeasure, WorkOrderShortages } from "./WorkOrderParts";
import { PieceScanner } from "./PieceScanner";
import type { StationQueueGroup } from "./ProductionBoard";

type StationOp = {
  operation_id: string;
  kind: string;
  station?: string;
  u_mm?: string;
  reference?: string;
  face?: string;
  depth_mm?: string;
  member_label?: string;
  host?: string;
  x_mm?: string;
  angle_left_deg?: string;
  angle_right_deg?: string;
  detail?: { boundary?: string };
};
type StationEntry = NonNullable<StationQueueGroup["entries"]>[number];
function refusal(error: unknown): string {
  return error instanceof ApiError
    ? String(
        (error.payload as { error?: { detail?: string } })?.error?.detail ??
          "El paso fue rechazado. Revisa su estado y pide al jefe que resuelva el bloqueo.",
      )
    : "No se pudo conectar con producción. Actualiza la estación e intenta otra vez.";
}

export function OperatorStationPage() {
  const { theme } = useTheme();
  const [params, setParams] = useSearchParams();
  const [preference, setPreference] = useState<OperatorStation | null>(null);
  const [queue, setQueue] = useState<StationEntry[]>([]);
  const [queueGeneration, setQueueGeneration] = useState(0);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [denied, setDenied] = useState(false);
  const [message, setMessage] = useState("");
  const [detail, setDetail] = useState<ProductionOrderDetail | null>(null);
  const [trace, setTrace] = useState<ProductionOrderTrace | null>(null);
  const [scan, setScan] = useState(params.get("piece") ?? "");
  const [focusPiece, setFocusPiece] = useState("");
  const [checked, setChecked] = useState<string[]>([]);
  const [opsDone, setOpsDone] = useState<string[]>([]);
  const [panel, setPanel] = useState<"block" | "note" | "quality" | null>(null);
  const [reason, setReason] = useState("Falta material");
  const [note, setNote] = useState("");
  const [check, setCheck] = useState("");
  const [expected, setExpected] = useState("");
  const [actual, setActual] = useState("");
  const [result, setResult] = useState<"PASS" | "FAIL">("PASS");
  const [blockOnFail, setBlockOnFail] = useState(false);
  const generation = useRef(0);
  const selection = params.get("order") ?? "";
  const chosen =
    queue.find((e) => e.order_id === selection || e.order_code === selection) ??
    (!selection ? queue[0] : undefined);
  const selectedId = chosen?.order_id;
  useAssistantSurface(
    detail ? "work_order" : null,
    detail ? { work_order_id: detail.id } : undefined,
  );
  const reload = useCallback(async (signal?: AbortSignal) => {
    setError("");
    setDenied(false);
    try {
      const [p, q] = await Promise.all([
        productionOperatorStation({ signal }),
        productionStationQueue({ signal }),
      ]);
      if (signal?.aborted) return;
      if (p.status !== 200 || q.status !== 200) throw new Error("station");
      setPreference(p.data);
      setQueue((q.data.stations as StationQueueGroup[]).flatMap((g) => g.entries ?? []));
      setQueueGeneration((value) => value + 1);
    } catch (e) {
      if (signal?.aborted) return;
      setDenied(e instanceof ApiError && e.status === 403);
      setError(refusal(e));
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    void reload(controller.signal);
    return () => controller.abort();
  }, [reload]);
  const loadSelected = useCallback(async (id: string, signal?: AbortSignal) => {
    const current = ++generation.current;
    setError("");
    setDenied(false);
    setDetail(null);
    setTrace(null);
    setOpsDone([]);
    setChecked([]);
    setPanel(null);
    try {
      const [d, t] = await Promise.all([
        productionOrderDetail(id, { signal }),
        productionOrderTrace(id, { signal }),
      ]);
      if (signal?.aborted || current !== generation.current) return;
      if (d.status !== 200 || t.status !== 200) throw new Error("order");
      setDetail(d.data);
      setTrace(t.data);
    } catch (e) {
      if (!signal?.aborted && current === generation.current) {
        setDenied(e instanceof ApiError && e.status === 403);
        setError(refusal(e));
      }
    }
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    if (selectedId) void loadSelected(selectedId, controller.signal);
    else {
      ++generation.current;
      setDetail(null);
      setTrace(null);
    }
    return () => controller.abort();
  }, [selectedId, queueGeneration, loadSelected]);
  const pieces = useMemo(() => (detail ? orderPieces(detail) : []), [detail]);
  const piece =
    pieces.find((p) =>
      focusPiece
        ? p.code === focusPiece || p.id === focusPiece
        : p.identity === params.get("identity"),
    ) ?? pieces[0];
  const step = detail?.steps.find((s) => s.id === chosen?.step_id);
  const next = detail?.steps.find((s) => step && s.sequence > step.sequence);
  const ops = ((trace?.operations?.items as StationOp[] | undefined) ?? []).filter(
    (op) => op.station === step?.code,
  );
  const evidenceRequired = !!step && PLAN_REQUIRED_CODES.has(step.code);
  const planRequired =
    !!step && (PLAN_REQUIRED_CODES.has(step.code) || !!STEP_STOCK_KINDS[step.code]);
  const optimization = detail?.payload?.optimization as
    { invalidated?: boolean; optimized_at?: string } | undefined;
  const planMissing = planRequired && (!optimization || optimization.invalidated);
  const canComplete =
    step?.status === "IN_PROGRESS" &&
    step.code !== "QC" &&
    (!evidenceRequired || ops.every((op) => opsDone.includes(op.operation_id)));
  async function chooseStation(code: string) {
    if (!code) return;
    setBusy(true);
    setMessage("");
    try {
      await productionOperatorStationSelect({ station_code: code });
      const url = new URLSearchParams();
      setParams(url);
      setFocusPiece("");
      await reload();
    } catch (e) {
      setMessage(refusal(e));
    } finally {
      setBusy(false);
    }
  }
  const scanPiece = useCallback(
    async (value: string) => {
      if (!value.trim()) return;
      setBusy(true);
      setMessage("");
      try {
        const response = await productionPieceTrace(encodeURIComponent(value.trim()));
        if (response.status !== 200) throw new Error("scan");
        const matches = response.data.matches as {
          work_order?: { id?: string };
          location?: { piece?: { code?: string } };
        }[];
        const candidates = matches.filter((m) =>
          queue.some((e) => e.order_id === m.work_order?.id),
        );
        if (candidates.length !== 1) {
          setMessage(
            candidates.length > 1
              ? "Esta etiqueta coincide con varias OT. Selecciona la OT y escanea su QR completo."
              : "Esta pieza no está en la cola de tu estación. El escaneo conserva tu puesto; elige otra estación para trabajar allí.",
          );
          return;
        }
        const hit = candidates[0]!;
        setScan(hit.location?.piece?.code ?? "");
        const nextParams = new URLSearchParams(params);
        nextParams.set("order", hit.work_order!.id!);
        nextParams.set("piece", value.trim());
        if (hit.location?.piece?.code) setFocusPiece(hit.location.piece.code);
        setParams(nextParams);
      } catch (e) {
        setMessage(
          e instanceof ApiError && e.status === 404
            ? "No se encontró la etiqueta. Revisa el código o escanea el QR completo."
            : refusal(e),
        );
      } finally {
        setBusy(false);
      }
    },
    [params, queue, setParams],
  );
  const deepScan = useRef("");
  useEffect(() => {
    const value = params.get("piece");
    if (value && preference?.selected_code && queue.length && deepScan.current !== value) {
      deepScan.current = value;
      void scanPiece(params.has("identity") ? `/production?${params.toString()}` : value);
    }
  }, [params, preference, queue, scanPiece]);
  async function act(body: StepTransitionRequestRequest) {
    if (!step || !detail) return;
    setBusy(true);
    setMessage("");
    try {
      await productionStepTransition(step.id, body);
      setMessage(
        body.action === "COMPLETE"
          ? "Paso completado. La OT avanzó a la siguiente estación."
          : body.action === "BLOCK" || body.block_on_fail
            ? "OT bloqueada. El jefe recibió el aviso."
            : "Registro guardado.",
      );
      await reload();
      if (body.action === "COMPLETE") {
        setParams(new URLSearchParams());
      }
      setPanel(null);
      setNote("");
    } catch (e) {
      setMessage(refusal(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section
      className="production-page production-operator"
      data-density="workshop"
      data-theme={window.localStorage.getItem("dekopen.theme") ? theme : "dark"}
    >
      <PageHeader title="Mi estación" context="Escanea una pieza y sigue su ruta de fabricación." />
      {loading ? (
        <LoadingState label="Cargando tu estación" />
      ) : denied ? (
        <DeniedState reason={error} />
      ) : error ? (
        <ErrorState
          title="No se pudo cargar la estación"
          body={error}
          onRetry={() => {
            void reload();
            if (selectedId) void loadSelected(selectedId);
          }}
        />
      ) : (
        <>
          <div className="production-station-choice">
            <label>
              Tu puesto
              <select
                aria-label="Tu puesto"
                value={preference?.selected_code ?? ""}
                disabled={busy}
                onChange={(e) => void chooseStation(e.target.value)}
              >
                <option value="">Elige la estación donde trabajas</option>
                {preference?.stations.map((s) => (
                  <option key={s.code} value={s.code}>
                    {s.label}
                  </option>
                ))}
              </select>
            </label>
            <button type="button" disabled={busy} onClick={() => void reload()}>
              Actualizar estación
            </button>
          </div>
          <PieceScanner
            value={scan}
            onChange={setScan}
            onScan={(v) => void scanPiece(v)}
            busy={busy}
          />
          {message ? (
            <p role="status" className="production-station-message">
              {message}
            </p>
          ) : null}
          {!preference?.stations.length ? (
            <BlockedState
              action={
                <button type="button" disabled={busy} onClick={() => void reload()}>
                  Actualizar estación
                </button>
              }
              reason="No hay puestos activos. El jefe de taller debe habilitar las estaciones en Ajustes."
            />
          ) : preference.selected_code === null ? (
            <EmptyState
              title="Elige tu puesto para empezar"
              body="La cola muestra solo las OT cuyo siguiente paso corresponde a esta estación."
            />
          ) : queue.length === 0 ? (
            <EmptyState
              title="Tu estación no tiene OT pendientes"
              body="Las OT aparecerán aquí cuando termine el paso anterior."
              action={<button onClick={() => void reload()}>Actualizar estación</button>}
            />
          ) : (
            <>
              <nav className="production-operator-queue" aria-label="Cola de tu estación">
                <label>
                  OT de tu estación
                  <select
                    aria-label="OT de tu estación"
                    value={selectedId ?? ""}
                    onChange={(event) => {
                      setFocusPiece("");
                      const url = new URLSearchParams();
                      url.set("order", event.target.value);
                      setParams(url);
                    }}
                  >
                    {selection && !chosen ? (
                      <option value="">Elige una OT disponible</option>
                    ) : null}
                    {queue.map((entry) => (
                      <option key={entry.step_id} value={entry.order_id}>
                        {entry.order_code} · {domainLabels[entry.status ?? ""] ?? "Sin dato"}
                      </option>
                    ))}
                  </select>
                </label>
              </nav>
              {selection && !chosen ? (
                <BlockedState
                  action={
                    <button type="button" disabled={busy} onClick={() => void reload()}>
                      Actualizar estación
                    </button>
                  }
                  reason="Esta OT no está en la cola de tu estación. Elige una OT disponible o cambia de puesto explícitamente."
                />
              ) : detail === null ? (
                <LoadingState label="Cargando la pieza y su ruta" />
              ) : step ? (
                <article className="production-station-task" aria-label="Siguiente">
                  <header>
                    <span>
                      {detail.order_code} · {stationCodeLabel(step.code)}
                    </span>
                    <span className="ui-value">
                      {detail.steps_done}/{detail.steps_total} pasos
                    </span>
                  </header>
                  <h2 className="production-piece-code">
                    {piece?.code ?? detail.making?.code ?? "Sin dato · escanea una etiqueta"}
                  </h2>
                  <p className="production-piece-measure ui-value">
                    {piece
                      ? pieceMeasure(piece)
                      : detail.making?.width_mm && detail.making.height_mm
                        ? `${fmtMm(detail.making.width_mm)} × ${fmtMm(detail.making.height_mm)} mm`
                        : "Sin dato · faltan medidas selladas"}
                  </p>
                  <p>
                    {piece ? cutRoleLabel(piece.role) + " · " : ""}
                    {detail.making?.location_tag ?? "Sin dato · destino no declarado"}
                    {piece?.unit ? ` · Unidad ${formatDecimal(piece.unit)}` : ""}
                  </p>
                  <p>
                    Siguiente:{" "}
                    {next
                      ? stationCodeLabel(next.code)
                      : "Ruta terminada · el jefe prepara el despacho"}
                  </p>
                  <WorkOrderShortages detail={detail} />
                  {step.status === "BLOCKED" ? (
                    <BlockedState
                      action={
                        <button type="button" disabled={busy} onClick={() => void reload()}>
                          Actualizar estación
                        </button>
                      }
                      reason={step.note ?? "El jefe debe revisar el bloqueo antes de continuar."}
                    />
                  ) : null}
                  {planMissing ? (
                    <BlockedState
                      action={
                        <button type="button" disabled={busy} onClick={() => void reload()}>
                          Actualizar estación
                        </button>
                      }
                      reason="Falta un plan de corte vigente. El jefe debe optimizar esta OT antes de iniciar."
                    />
                  ) : null}
                  <div
                    className="production-station-actions"
                    role="group"
                    aria-label="Acciones del paso"
                  >
                    {step.status === "READY" || step.status === "PENDING" ? (
                      <button
                        data-variant="primary"
                        disabled={busy || planMissing}
                        onClick={() => void act({ action: "START" })}
                      >
                        Iniciar
                      </button>
                    ) : null}
                    {step.status === "IN_PROGRESS" && step.code !== "QC" ? (
                      <button
                        data-variant="primary"
                        disabled={busy || !canComplete}
                        onClick={() =>
                          void act({
                            action: "COMPLETE",
                            ...(evidenceRequired ? { ops_done: opsDone } : {}),
                          })
                        }
                      >
                        Completar
                      </button>
                    ) : null}
                    {step.code === "QC" ? (
                      <button disabled={busy} onClick={() => setPanel("quality")}>
                        Registrar medición
                      </button>
                    ) : null}
                    {step.status !== "BLOCKED" ? (
                      <button
                        disabled={busy}
                        onClick={() => {
                          setPanel("block");
                          setNote("");
                        }}
                      >
                        Bloquear
                      </button>
                    ) : null}
                    <button
                      disabled={busy}
                      onClick={() => {
                        setPanel("note");
                        setNote("");
                      }}
                    >
                      Nota
                    </button>
                  </div>
                  {step.code === "QC" ? (
                    <p>
                      El control final lo firma el jefe de taller. Puedes registrar mediciones y
                      solicitar su revisión.
                    </p>
                  ) : null}
                  {panel ? (
                    <ValidatedForm
                      className="production-station-form"
                      onSubmit={(e) => {
                        e.preventDefault();
                        if (panel === "quality") {
                          if (!check.trim()) return;
                          void act({
                            action: "QC_CHECK",
                            qc_check: {
                              check,
                              expected,
                              actual,
                              item_code: piece?.code ?? "",
                              result,
                            },
                            block_on_fail: result === "FAIL" && blockOnFail,
                          });
                        } else {
                          const text =
                            panel === "block" && reason !== "Otro"
                              ? [reason, note].filter(Boolean).join(" · ")
                              : note;
                          if (!text.trim()) {
                            setMessage("Escribe el motivo para que el jefe sepa cómo resolverlo.");
                            return;
                          }
                          void act({ action: panel === "block" ? "BLOCK" : "NOTE", note: text });
                        }
                      }}
                    >
                      {panel === "block" ? (
                        <label>
                          Motivo
                          <select
                            aria-label="Motivo"
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
                          >
                            {[
                              "Falta material",
                              "Pieza dañada",
                              "Medida fuera de tolerancia",
                              "Equipo detenido",
                              "Falta autoridad técnica",
                              "Otro",
                            ].map((r) => (
                              <option key={r}>{r}</option>
                            ))}
                          </select>
                        </label>
                      ) : null}
                      {panel === "quality" ? (
                        <>
                          <label>
                            Qué verificaste
                            <input value={check} onChange={(e) => setCheck(e.target.value)} />
                          </label>
                          <label>
                            Esperado según ficha
                            <input value={expected} onChange={(e) => setExpected(e.target.value)} />
                          </label>
                          <label>
                            Medición real
                            <input value={actual} onChange={(e) => setActual(e.target.value)} />
                          </label>
                          <label>
                            Resultado
                            <select
                              aria-label="Resultado"
                              value={result}
                              onChange={(e) => setResult(e.target.value as "PASS" | "FAIL")}
                            >
                              <option value="PASS">Conforme</option>
                              <option value="FAIL">Fuera de especificación</option>
                            </select>
                          </label>
                          {result === "FAIL" ? (
                            <label className="production-touch-check">
                              <input
                                type="checkbox"
                                checked={blockOnFail}
                                onChange={(e) => setBlockOnFail(e.target.checked)}
                              />
                              Bloquear la OT y avisar al jefe
                            </label>
                          ) : null}
                        </>
                      ) : (
                        <label>
                          {panel === "block" ? "Detalle del bloqueo" : "Nota para el taller"}
                          <textarea value={note} onChange={(e) => setNote(e.target.value)} />
                        </label>
                      )}
                      <button type="submit" disabled={busy}>
                        {panel === "quality" && blockOnFail && result === "FAIL"
                          ? "Guardar y bloquear"
                          : "Guardar"}
                      </button>
                      <button type="button" onClick={() => setPanel(null)}>
                        Cancelar
                      </button>
                    </ValidatedForm>
                  ) : null}
                  {ops.length ? (
                    <details className="production-touch-operations">
                      <summary>Operaciones de tu estación · {formatDecimal(ops.length)}</summary>
                      <ul className="production-touch-list">
                        {ops.map((op) => (
                          <li key={op.operation_id}>
                            <label className="production-touch-check">
                              <input
                                type="checkbox"
                                checked={opsDone.includes(op.operation_id)}
                                disabled={step.status === "BLOCKED"}
                                onChange={(e) =>
                                  setOpsDone((ids) =>
                                    e.target.checked
                                      ? [...ids, op.operation_id]
                                      : ids.filter((id) => id !== op.operation_id),
                                  )
                                }
                              />
                              <span>
                                {op.member_label ? `${op.member_label} · ` : ""}
                                {op.detail?.boundary
                                  ? opBoundaryLabel(op.detail.boundary)
                                  : opKindLabel(op.kind)}
                                {op.host?.startsWith("bar:") ? ` · Barra ${op.host.slice(4)}` : ""}
                                {op.x_mm ? ` · ${fmtMm(op.x_mm)} mm desde el borde de barra` : ""}
                                {op.u_mm
                                  ? ` · ${fmtMm(op.u_mm)} mm desde ${opReferenceLabel(op.reference)}`
                                  : ""}
                                {op.face ? ` · ${opFaceLabel(op.face)}` : ""}
                                {op.depth_mm ? ` · profundidad ${fmtMm(op.depth_mm)} mm` : ""}
                                {op.angle_left_deg ? ` · ángulo ${fmtMm(op.angle_left_deg)}°` : ""}
                              </span>
                            </label>
                          </li>
                        ))}
                      </ul>
                    </details>
                  ) : null}
                  {pieces.length ? (
                    <details className="production-touch-pieces">
                      <summary>Piezas de la OT · {formatDecimal(pieces.length)}</summary>
                      <ul className="production-touch-list">
                        {pieces.map((p) => (
                          <li key={p.id}>
                            <label className="production-touch-check">
                              <input
                                type="checkbox"
                                checked={checked.includes(p.id)}
                                onChange={(e) =>
                                  setChecked((ids) =>
                                    e.target.checked
                                      ? [...ids, p.id]
                                      : ids.filter((id) => id !== p.id),
                                  )
                                }
                              />
                              <button
                                type="button"
                                aria-pressed={p.id === piece?.id}
                                onClick={() => setFocusPiece(p.id)}
                              >
                                {p.code} · {pieceMeasure(p)}
                              </button>
                            </label>
                          </li>
                        ))}
                      </ul>
                    </details>
                  ) : null}
                  <TechDetails diagnostic={JSON.stringify({ step, trace }, null, 2)} />
                </article>
              ) : null}
            </>
          )}
        </>
      )}
    </section>
  );
}
