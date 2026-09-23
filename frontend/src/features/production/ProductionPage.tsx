import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import {
  productionOrderCncExport,
  productionOrderDetail,
  productionOrderDispatch,
  productionOrderInstall,
  productionOrderLabels,
  productionOrderOptimize,
  productionOrderPacking,
  productionOrderRemake,
  productionOrders,
  productionStepTransition,
} from "../../api/generated/dekopen";
import type {
  PackingLabel,
  ProductionOrder,
  ProductionOrderDetail,
  ProductionStep,
} from "../../api/generated/models";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { t } from "../../i18n/es-CL";
import "./production.css";

type WorkOrderMaterials = {
  profile_cuts?: unknown[];
  glasses?: unknown[];
  panels?: unknown[];
  hardware_items?: unknown[];
};

type StepAction = "START" | "COMPLETE" | "BLOCK" | "UNBLOCK" | "NOTE" | "QC_FAIL";

type CutPlacement = {
  piece_id: string;
  length_mm: string;
  unit_index?: number;
  bay_id?: string | null;
  leaf_id?: string | null;
};
type CutBar = {
  bar_index: number;
  commercial_sku: string;
  stock_length_mm: string;
  remainder_mm: string;
  yield_pct: string;
  cuts: CutPlacement[];
};
type PurchaseLine = { commercial_sku: string; qty_bars: number; stock_length_mm: string };
type SheetPurchase = { purchasing_sku: string; qty_sheets: number };
type NestPlacement = {
  piece_id: string;
  x_mm: string;
  y_mm: string;
  width_mm: string;
  height_mm: string;
  rotated: boolean;
  unit_index?: number;
};
type SheetLayout = {
  sheet_index: number;
  purchasing_sku: string;
  sheet_width_mm: string;
  sheet_height_mm: string;
  yield_pct: string;
  placements: NestPlacement[];
};
type UnnestedPiece = {
  kind: string;
  group: string;
  width_mm: string;
  height_mm: string;
  quantity: number;
};
type WorkOrderOptimization = {
  color?: string;
  units?: number;
  optimized_at?: string;
  bars?: { workshop_cut_plan?: CutBar[]; purchase_list?: PurchaseLine[] };
  sheets?: SheetLayout[];
  sheet_purchases?: SheetPurchase[];
  unnested?: UnnestedPiece[];
};

type CncExport = {
  exported_at?: string;
  files?: Record<string, string>;
};

type PackingUnit = {
  unit_index: number;
  label_code: string;
  profiles?: number;
  reinforcements?: number;
  glasses?: number;
  panels?: number;
  hardware?: number;
};
type WorkOrderPacking = {
  generated_at?: string;
  units?: PackingUnit[];
};

const stepStatusKey: Record<string, Parameters<typeof t>[0]> = {
  PENDING: "production.stepPending",
  READY: "production.stepReady",
  IN_PROGRESS: "production.stepInProgress",
  DONE: "production.stepDone",
  BLOCKED: "production.stepBlocked",
};
const orderStatusKey: Record<string, Parameters<typeof t>[0]> = {
  RELEASED: "production.orderReleased",
  IN_PROGRESS: "production.orderInProgress",
  HOLD: "production.orderHold",
  COMPLETED: "production.orderCompleted",
  DISPATCHED: "production.orderDispatched",
  INSTALLED: "production.orderInstalled",
};
const eventKey: Record<string, Parameters<typeof t>[0]> = {
  WO_RELEASED: "production.eventReleased",
  STEP_STARTED: "production.eventStepStarted",
  STEP_COMPLETED: "production.eventStepCompleted",
  STEP_BLOCKED: "production.eventStepBlocked",
  STEP_UNBLOCKED: "production.eventStepUnblocked",
  NOTE: "production.eventNote",
  WO_COMPLETED: "production.eventCompleted",
  WO_HOLD: "production.eventHold",
  WO_OPTIMIZED: "production.eventOptimized",
  QC_FAILED: "production.eventQcFailed",
  WO_REMADE: "production.eventRemade",
  WO_CNC_EXPORTED: "production.eventCncExported",
  WO_PACKED: "production.eventPacked",
  WO_DISPATCHED: "production.eventDispatched",
  WO_INSTALLED: "production.eventInstalled",
};

function stepActions(step: ProductionStep): StepAction[] {
  switch (step.status) {
    case "READY":
    case "PENDING":
      return ["START", "BLOCK", "NOTE"];
    case "IN_PROGRESS":
      return step.code === "QC"
        ? ["COMPLETE", "QC_FAIL", "BLOCK", "NOTE"]
        : ["COMPLETE", "BLOCK", "NOTE"];
    case "BLOCKED":
      return ["UNBLOCK", "NOTE"];
    case "DONE":
      return ["NOTE"];
    default:
      return ["NOTE"];
  }
}

const actionLabel: Record<StepAction, Parameters<typeof t>[0]> = {
  START: "production.actionStart",
  COMPLETE: "production.actionComplete",
  BLOCK: "production.actionBlock",
  UNBLOCK: "production.actionUnblock",
  NOTE: "production.actionNote",
  QC_FAIL: "production.actionQcFail",
};

export function ProductionPage(): JSX.Element {
  const auth = useAuthSession();
  const role = auth.me?.active_organization?.role ?? "";
  const [params, setParams] = useSearchParams();
  const [orders, setOrders] = useState<ProductionOrder[]>([]);
  const [detail, setDetail] = useState<ProductionOrderDetail | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [note, setNote] = useState("");
  const [optColor, setOptColor] = useState("");
  const [labels, setLabels] = useState<PackingLabel[]>([]);
  const labelsGeneration = useRef(0);
  const selectedIdRef = useRef("");
  const mounted = useRef(true);
  useEffect(
    () => () => {
      mounted.current = false;
    },
    [],
  );

  const selectedId = params.get("order") ?? "";
  selectedIdRef.current = selectedId;

  const loadOrders = useCallback(async () => {
    const response = await productionOrders();
    if (response.status === 200) setOrders(response.data.orders);
  }, []);

  const detailGeneration = useRef(0);

  const loadDetail = useCallback(async (orderId: string) => {
    const generation = ++detailGeneration.current;
    const response = await productionOrderDetail(orderId);
    if (response.status === 200 && generation === detailGeneration.current) {
      setDetail(response.data);
      setLabels([]);
    }
  }, []);

  useEffect(() => {
    void loadOrders().catch(() => setMessage(t("production.loadError")));
  }, [loadOrders]);

  useEffect(() => {
    labelsGeneration.current += 1;
    if (!selectedId) {
      detailGeneration.current += 1;
      setDetail(null);
      return;
    }
    void loadDetail(selectedId).catch(() => setMessage(t("production.loadError")));
  }, [selectedId, loadDetail]);

  async function action(task: Promise<unknown>, orderId: string): Promise<void> {
    setBusy(true);
    setMessage("");
    try {
      await task;
      setNote("");
      await Promise.all([loadDetail(orderId), loadOrders()]);
    } catch {
      if (mounted.current) setMessage(t("production.actionError"));
    } finally {
      if (mounted.current) setBusy(false);
    }
  }

  function transition(stepId: string, stepAction: StepAction, orderId: string): void {
    if (stepAction === "NOTE" && !note.trim()) {
      return;
    }
    const noteValue =
      stepAction === "NOTE" || stepAction === "BLOCK" || stepAction === "QC_FAIL"
        ? note || undefined
        : undefined;
    const body =
      stepAction === "QC_FAIL"
        ? { action: "COMPLETE" as const, qc_result: "FAIL" as const, note: noteValue ?? null }
        : { action: stepAction, note: noteValue ?? null };
    void action(productionStepTransition(stepId, body), orderId);
  }

  function remake(orderId: string): void {
    setBusy(true);
    setMessage("");
    productionOrderRemake(orderId, { note: note || undefined })
      .then(async (response) => {
        if (response.status === 201 && mounted.current) {
          setNote("");
          setParams({ order: response.data.id });
          await loadOrders();
        }
      })
      .catch(() => {
        if (mounted.current) setMessage(t("production.actionError"));
      })
      .finally(() => {
        if (mounted.current) setBusy(false);
      });
  }

  function optimize(orderId: string): void {
    if (!optColor.trim()) return;
    void action(productionOrderOptimize(orderId, { color: optColor.trim() }), orderId);
  }

  function exportCnc(orderId: string): void {
    void action(productionOrderCncExport(orderId), orderId);
  }

  async function showLabels(orderId: string): Promise<void> {
    const generation = ++labelsGeneration.current;
    setLabels([]);
    setBusy(true);
    try {
      const response = await productionOrderLabels(orderId);
      // A selection change bumps the generation, but a response can still
      // land in the gap before the effect runs — check the order too.
      if (generation !== labelsGeneration.current) return;
      if (selectedIdRef.current !== orderId) return;
      if (response.status !== 200) {
        setMessage(t("production.labelsError"));
        return;
      }
      setLabels(response.data.labels);
    } catch {
      if (generation === labelsGeneration.current && selectedIdRef.current === orderId) {
        setMessage(t("production.labelsError"));
      }
    } finally {
      setBusy(false);
    }
  }

  function pack(orderId: string): void {
    void action(productionOrderPacking(orderId), orderId);
  }

  function dispatch(orderId: string): void {
    void action(productionOrderDispatch(orderId, { note: note || undefined }), orderId);
  }

  function install(orderId: string): void {
    void action(productionOrderInstall(orderId, { note: note || undefined }), orderId);
  }

  function downloadCnc(orderCode: string, filename: string, content: string): void {
    const blob = new Blob([content], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${orderCode}-${filename}`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  const canAct = role === "OWNER" || role === "WORKSHOP_MANAGER" || role === "INSTALLER";
  const canWrite = role === "OWNER" || role === "WORKSHOP_MANAGER";
  const canStep = canWrite || role === "INSTALLER";
  if (!canAct) {
    return (
      <section className="production-page">
        <h1>{t("production.title")}</h1>
        <p role="alert">{t("production.denied")}</p>
      </section>
    );
  }

  return (
    <section className="production-page">
      <header>
        <h1>{t("production.title")}</h1>
        <p>{t("production.subtitle")}</p>
      </header>
      {message ? <p role="alert">{message}</p> : null}
      <div className="production-layout">
        <aside className="production-orders" aria-label={t("production.orders")}>
          <h2>{t("production.orders")}</h2>
          {orders.length === 0 ? <p>{t("production.empty")}</p> : null}
          <ul>
            {orders.map((order) => (
              <li key={order.id}>
                <button
                  type="button"
                  className={
                    order.id === selectedId ? "production-order active" : "production-order"
                  }
                  onClick={() => setParams({ order: order.id })}
                >
                  <span className="production-order-code">{order.order_code}</span>
                  <span className={`production-chip status-${order.status.toLowerCase()}`}>
                    {t(orderStatusKey[order.status] ?? "production.orderReleased")}
                  </span>
                  <span className="production-order-progress">
                    {order.steps_done}/{order.steps_total} {t("production.stepsShort")}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </aside>
        <article className="production-detail">
          {detail ? (
            <>
              <header className="production-detail-head">
                <h2>{detail.order_code}</h2>
                <span className={`production-chip status-${detail.status.toLowerCase()}`}>
                  {t(orderStatusKey[detail.status] ?? "production.orderReleased")}
                </span>
                {detail.quantity ? (
                  <span className="production-order-progress">
                    {detail.quantity} {t("production.units")}
                  </span>
                ) : null}
                {canWrite && detail.status === "COMPLETED" ? (
                  <button
                    type="button"
                    className="production-dispatch"
                    disabled={busy}
                    onClick={() => dispatch(detail.id)}
                  >
                    {t("production.dispatchButton")}
                  </button>
                ) : null}
                {canStep && detail.status === "DISPATCHED" ? (
                  <button
                    type="button"
                    className="production-dispatch production-install"
                    disabled={busy}
                    onClick={() => install(detail.id)}
                  >
                    {t("production.installButton")}
                  </button>
                ) : null}
                {canWrite && detail.status === "HOLD" ? (
                  <button
                    type="button"
                    className="production-remake"
                    disabled={busy}
                    onClick={() => remake(detail.id)}
                  >
                    {t("production.remakeButton")}
                  </button>
                ) : null}
              </header>
              {(() => {
                const materials = detail.payload?.materials as WorkOrderMaterials | undefined;
                if (!materials) return null;
                return (
                  <dl className="production-materials">
                    <div>
                      <dt>{t("production.materialCuts")}</dt>
                      <dd>{materials.profile_cuts?.length ?? 0}</dd>
                    </div>
                    <div>
                      <dt>{t("production.materialGlass")}</dt>
                      <dd>{materials.glasses?.length ?? 0}</dd>
                    </div>
                    <div>
                      <dt>{t("production.materialHardware")}</dt>
                      <dd>{materials.hardware_items?.length ?? 0}</dd>
                    </div>
                  </dl>
                );
              })()}
              {(() => {
                const optimization = detail.payload?.optimization as
                  WorkOrderOptimization | undefined;
                const canOptimize = role === "OWNER" || role === "WORKSHOP_MANAGER";
                const cutPlan = optimization?.bars?.workshop_cut_plan ?? [];
                const purchases = optimization?.bars?.purchase_list ?? [];
                const layouts = optimization?.sheets ?? [];
                const unnested = optimization?.unnested ?? [];
                const sheetPurchases = optimization?.sheet_purchases ?? [];
                return (
                  <section
                    className="production-optimize"
                    aria-label={t("production.optimizeTitle")}
                  >
                    <header className="production-optimize-head">
                      <h3>{t("production.optimizeTitle")}</h3>
                      {optimization?.optimized_at ? (
                        <time dateTime={optimization.optimized_at}>
                          {t("production.optimizeRunAt")}:
                          {new Date(optimization.optimized_at).toLocaleString("es-CL")}
                        </time>
                      ) : null}
                    </header>
                    {canOptimize &&
                    detail.status !== "COMPLETED" &&
                    detail.status !== "DISPATCHED" &&
                    detail.status !== "INSTALLED" ? (
                      <div className="production-optimize-controls">
                        <input
                          type="text"
                          value={optColor}
                          onChange={(event) => setOptColor(event.target.value)}
                          placeholder={t("production.optimizeColorPlaceholder")}
                          aria-label={t("production.optimizeColor")}
                        />
                        <button
                          type="button"
                          disabled={busy || !optColor.trim()}
                          onClick={() => optimize(detail.id)}
                        >
                          {t("production.optimizeButton")}
                        </button>
                      </div>
                    ) : null}
                    {(() => {
                      const cncExport = detail.payload?.cnc_export as CncExport | undefined;
                      const files = Object.entries(cncExport?.files ?? {});
                      if (!optimization) return null;
                      return (
                        <div className="production-cnc">
                          {canOptimize &&
                          detail.status !== "COMPLETED" &&
                          detail.status !== "DISPATCHED" &&
                          detail.status !== "INSTALLED" ? (
                            <button
                              type="button"
                              disabled={busy}
                              onClick={() => exportCnc(detail.id)}
                            >
                              {t("production.cncExportButton")}
                            </button>
                          ) : null}
                          {files.map(([filename, content]) => (
                            <button
                              key={filename}
                              type="button"
                              className="production-cnc-file"
                              onClick={() => downloadCnc(detail.order_code, filename, content)}
                            >
                              {filename}
                            </button>
                          ))}
                        </div>
                      );
                    })()}
                    {!optimization ? (
                      <p className="production-optimize-empty">{t("production.optimizeEmpty")}</p>
                    ) : (
                      <>
                        {cutPlan.length ? (
                          <table className="production-plan">
                            <thead>
                              <tr>
                                <th>{t("production.optimizeBar")}</th>
                                <th>{t("production.optimizeSku")}</th>
                                <th>{t("production.optimizeStock")}</th>
                                <th>{t("production.optimizeCuts")}</th>
                                <th>{t("production.optimizeRemainder")}</th>
                                <th>{t("production.optimizeYield")}</th>
                              </tr>
                            </thead>
                            <tbody>
                              {cutPlan.map((bar) => (
                                <tr key={bar.bar_index}>
                                  <td>#{bar.bar_index}</td>
                                  <td>{bar.commercial_sku}</td>
                                  <td>{bar.stock_length_mm} mm</td>
                                  <td>
                                    {bar.cuts
                                      .map(
                                        (cut) =>
                                          `${cut.piece_id} ${cut.length_mm}mm u${cut.unit_index ?? 1}`,
                                      )
                                      .join(" · ")}
                                  </td>
                                  <td>{bar.remainder_mm} mm</td>
                                  <td>{bar.yield_pct}%</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        ) : null}
                        {purchases.length || sheetPurchases.length ? (
                          <p className="production-optimize-purchases">
                            {t("production.optimizePurchases")}:{" "}
                            {purchases
                              .map(
                                (line) =>
                                  `${line.qty_bars} ${t("production.optimizePurchaseUnit")} ${line.commercial_sku}`,
                              )
                              .concat(
                                sheetPurchases.map(
                                  (line) =>
                                    `${line.qty_sheets} ${t("production.optimizePurchaseSheet")} ${line.purchasing_sku}`,
                                ),
                              )
                              .join(" · ")}
                          </p>
                        ) : null}
                        {layouts.length ? (
                          <table className="production-plan">
                            <thead>
                              <tr>
                                <th>{t("production.optimizeSheet")}</th>
                                <th>{t("production.optimizeSku")}</th>
                                <th>{t("production.optimizeSize")}</th>
                                <th>{t("production.optimizePieces")}</th>
                                <th>{t("production.optimizeYield")}</th>
                              </tr>
                            </thead>
                            <tbody>
                              {layouts.map((layout) => (
                                <tr key={`${layout.purchasing_sku}-${layout.sheet_index}`}>
                                  <td>#{layout.sheet_index}</td>
                                  <td>{layout.purchasing_sku}</td>
                                  <td>
                                    {layout.sheet_width_mm}×{layout.sheet_height_mm} mm
                                  </td>
                                  <td>
                                    {layout.placements
                                      .map(
                                        (piece) =>
                                          `${piece.piece_id}${piece.rotated ? ` (${t("production.optimizeRotated")})` : ""}`,
                                      )
                                      .join(" · ")}
                                  </td>
                                  <td>{layout.yield_pct}%</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        ) : null}
                        {unnested.length ? (
                          <p className="production-optimize-unnested" role="alert">
                            {t("production.optimizeUnnested")}:{" "}
                            {unnested
                              .map(
                                (piece) =>
                                  `${piece.kind} ${piece.width_mm}×${piece.height_mm} mm ×${piece.quantity} (${piece.group})`,
                              )
                              .join(" · ")}
                          </p>
                        ) : null}
                      </>
                    )}
                  </section>
                );
              })()}
              {(() => {
                const packing = detail.payload?.packing as WorkOrderPacking | undefined;
                const units = packing?.units ?? [];
                return (
                  <section className="production-packing" aria-label={t("production.packingTitle")}>
                    <header className="production-optimize-head">
                      <h3>{t("production.packingTitle")}</h3>
                      {packing?.generated_at ? (
                        <time dateTime={packing.generated_at}>
                          {new Date(packing.generated_at).toLocaleString("es-CL")}
                        </time>
                      ) : null}
                      {canWrite &&
                      detail.status !== "DISPATCHED" &&
                      detail.status !== "INSTALLED" ? (
                        <button type="button" disabled={busy} onClick={() => pack(detail.id)}>
                          {packing
                            ? t("production.packingRegenerate")
                            : t("production.packingGenerate")}
                        </button>
                      ) : null}
                      {units.length ? (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => void showLabels(detail.id)}
                        >
                          {t("production.labelsShow")}
                        </button>
                      ) : null}
                      {labels.length ? (
                        <button type="button" onClick={() => window.print()}>
                          {t("production.labelsPrint")}
                        </button>
                      ) : null}
                    </header>
                    {labels.length ? (
                      <ul className="production-labels">
                        {labels.map((label) => (
                          <li key={label.label_code} className="production-label">
                            <span className="production-label-code">{label.label_code}</span>
                            <span
                              className="production-label-qr"
                              // Generated server-side by segno from the sealed manifest.
                              dangerouslySetInnerHTML={{ __html: label.qr_svg }}
                            />
                            <span className="production-label-pieces">
                              {t("production.labelsPieces")}: {label.pieces}
                            </span>
                            <span className="production-label-parts">
                              {(
                                [
                                  ["M", label.profiles],
                                  ["R", label.reinforcements],
                                  ["V", label.glasses],
                                  ["P", label.panels],
                                  ["H", label.hardware],
                                ] as Array<[string, number]>
                              )
                                .filter(([, count]) => count > 0)
                                .map(([kind, count]) => `${kind}×${count}`)
                                .join(" · ")}
                            </span>
                          </li>
                        ))}
                      </ul>
                    ) : null}
                    {units.length ? (
                      <table className="production-plan">
                        <thead>
                          <tr>
                            <th>{t("production.packingLabel")}</th>
                            <th>{t("production.packingProfiles")}</th>
                            <th>{t("production.packingReinforcements")}</th>
                            <th>{t("production.packingGlasses")}</th>
                            <th>{t("production.packingPanels")}</th>
                            <th>{t("production.packingHardware")}</th>
                          </tr>
                        </thead>
                        <tbody>
                          {units.map((unit) => (
                            <tr key={unit.unit_index}>
                              <td className="production-label-code">{unit.label_code}</td>
                              <td>{unit.profiles ?? 0}</td>
                              <td>{unit.reinforcements ?? 0}</td>
                              <td>{unit.glasses ?? 0}</td>
                              <td>{unit.panels ?? 0}</td>
                              <td>{unit.hardware ?? 0}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    ) : (
                      <p className="production-optimize-empty">{t("production.packingEmpty")}</p>
                    )}
                  </section>
                );
              })()}
              <ol className="production-steps">
                {detail.steps.map((step) => (
                  <li key={step.id} className={`production-step step-${step.status.toLowerCase()}`}>
                    <div className="production-step-head">
                      <span className="production-step-seq">{step.sequence}</span>
                      <span className="production-step-label">{step.label}</span>
                      {step.work_center_code ? (
                        <span className="production-step-center">{step.work_center_code}</span>
                      ) : null}
                      <span className={`production-chip status-${step.status.toLowerCase()}`}>
                        {t(stepStatusKey[step.status] ?? "production.stepReady")}
                      </span>
                    </div>
                    {step.note ? <p className="production-step-note">{step.note}</p> : null}
                    {detail.status !== "COMPLETED" &&
                    detail.status !== "DISPATCHED" &&
                    detail.status !== "INSTALLED" ? (
                      <div className="production-step-actions">
                        {stepActions(step).map((stepAction) => (
                          <button
                            key={stepAction}
                            type="button"
                            disabled={busy}
                            onClick={() => transition(step.id, stepAction, detail.id)}
                          >
                            {t(actionLabel[stepAction])}
                          </button>
                        ))}
                      </div>
                    ) : null}
                  </li>
                ))}
              </ol>
              <label className="production-note">
                {t("production.noteLabel")}
                <input
                  type="text"
                  value={note}
                  onChange={(event) => setNote(event.target.value)}
                  placeholder={t("production.notePlaceholder")}
                />
              </label>
              <section className="production-events" aria-label={t("production.events")}>
                <h3>{t("production.events")}</h3>
                <ol>
                  {detail.events.map((event) => (
                    <li key={event.id}>
                      <time dateTime={event.created_at}>
                        {new Date(event.created_at).toLocaleString("es-CL")}
                      </time>
                      <span>{t(eventKey[event.event] ?? "production.eventNote")}</span>
                    </li>
                  ))}
                </ol>
              </section>
            </>
          ) : (
            <p className="production-pick">{t("production.pickOrder")}</p>
          )}
        </article>
      </div>
    </section>
  );
}
