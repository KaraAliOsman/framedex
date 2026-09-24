import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import {
  productionOrderCncExport,
  productionOrderOpsExport,
  productionOrderDelivery,
  productionOrderDeliveryConfirm,
  productionOrderDeliveryConfirmation,
  productionOrderDeliverySchedule,
  productionOrderDeliveryTransition,
  productionOrderDetail,
  productionOrderDispatch,
  productionOrderDispatchNote,
  productionOrderDispatchNoteDte,
  productionOrderDispatchNoteDteEmit,
  productionOrderDxfExport,
  productionOrderInstall,
  productionOrderLabels,
  productionOrderOptimize,
  productionOrderPacking,
  productionOrderRemake,
  productionOrders,
  productionStepTransition,
} from "../../api/generated/dekopen";
import type {
  Delivery,
  DeliveryScheduleRequestRequest,
  DeliveryTransitionRequestStatusEnum,
  MethodEnum,
  PackingLabel,
  PaymentKindEnum,
  ProductionOrder,
  ProductionOrderDetail,
  ProductionStep,
} from "../../api/generated/models";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { t } from "../../i18n/es-CL";
import { cutRoleLabel } from "./labels";
import { CutPlanView, type WorkOrderOptimization } from "./CutPlanView";
import {
  GlassSummary,
  glassSummaryCsv,
  type GlassPiece,
  type PolishingEntry,
} from "./GlassSummary";
import SignaturePad, { type SignaturePadHandle } from "./SignaturePad";
import "./production.css";

type WorkOrderMaterials = {
  profile_cuts?: unknown[];
  glasses?: unknown[];
  panels?: unknown[];
  hardware_items?: unknown[];
};

type StepAction = "START" | "COMPLETE" | "BLOCK" | "UNBLOCK" | "NOTE" | "QC_FAIL";

type CncExport = {
  exported_at?: string;
  files?: Record<string, string>;
};
type DxfExport = CncExport;
type OpsExport = CncExport & {
  operation_count?: number;
  counts_by_kind?: Record<string, number>;
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
  WO_DXF_EXPORTED: "production.eventDxfExported",
  WO_PACKED: "production.eventPacked",
  WO_DISPATCHED: "production.eventDispatched",
  WO_INSTALLED: "production.eventInstalled",
  WO_DELIVERY_SCHEDULED: "production.eventDeliveryScheduled",
  WO_DELIVERY_ON_ROUTE: "production.eventDeliveryOnRoute",
  WO_DELIVERY_DELIVERED: "production.eventDeliveryDelivered",
  WO_DELIVERY_CONFIRMED: "production.eventDeliveryConfirmed",
  WO_DELIVERY_FAILED: "production.eventDeliveryFailed",
  WO_REMNANTS_SETTLED: "production.eventRemnantsSettled",
  WO_OPS_EXPORTED: "production.eventOpsExported",
};

const deliveryStatusKey: Record<string, Parameters<typeof t>[0]> = {
  SCHEDULED: "production.deliveryStatusScheduled",
  ON_ROUTE: "production.deliveryStatusOnRoute",
  DELIVERED: "production.deliveryStatusDelivered",
  FAILED: "production.deliveryStatusFailed",
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
  const [optStrategy, setOptStrategy] = useState("auto");
  const [labels, setLabels] = useState<PackingLabel[]>([]);
  const [delivery, setDelivery] = useState<Delivery | null>(null);
  const [deliveryForm, setDeliveryForm] = useState<DeliveryScheduleRequestRequest | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmName, setConfirmName] = useState("");
  const [confirmRut, setConfirmRut] = useState("");
  const [collectPayment, setCollectPayment] = useState(false);
  const [collectAmount, setCollectAmount] = useState("");
  const [collectMethod, setCollectMethod] = useState<MethodEnum>("CASH");
  const [collectKind, setCollectKind] = useState<PaymentKindEnum>("SALDO");
  const [sigDrawn, setSigDrawn] = useState(false);
  const sigRef = useRef<SignaturePadHandle | null>(null);
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
  /** Triage queue — deep-linkable: /production?status=HOLD lands on the held
   * orders (dashboard attention items point here). */
  const statusFilter = params.get("status") ?? "";
  const filteredOrders = statusFilter
    ? orders.filter((order) => order.status === statusFilter)
    : orders;

  const loadOrders = useCallback(async () => {
    const response = await productionOrders();
    if (response.status === 200) setOrders(response.data.orders);
  }, []);

  const detailGeneration = useRef(0);

  const loadDetail = useCallback(async (orderId: string) => {
    const generation = ++detailGeneration.current;
    const [response, deliveryResponse] = await Promise.all([
      productionOrderDetail(orderId),
      productionOrderDelivery(orderId),
    ]);
    if (generation === detailGeneration.current) {
      if (response.status === 200) {
        setDetail(response.data);
        setLabels([]);
      }
      setDelivery(deliveryResponse.status === 200 ? deliveryResponse.data.delivery : null);
      setDeliveryForm(null);
      setConfirmOpen(false);
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
      setDelivery(null);
      setDeliveryForm(null);
      setConfirmOpen(false);
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
    void action(
      productionOrderOptimize(orderId, {
        color: optColor.trim(),
        strategy: optStrategy as "fast" | "deep" | "auto",
      }),
      orderId,
    );
  }

  function exportCnc(orderId: string): void {
    void action(productionOrderCncExport(orderId), orderId);
  }

  function exportDxf(orderId: string): void {
    void action(productionOrderDxfExport(orderId), orderId);
  }

  function exportOperations(orderId: string): void {
    void action(productionOrderOpsExport(orderId), orderId);
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

  async function saveDelivery(orderId: string): Promise<void> {
    if (!deliveryForm) return;
    setBusy(true);
    try {
      const response = await productionOrderDeliverySchedule(orderId, deliveryForm);
      if (response.status === 200) {
        await loadDetail(orderId);
      } else {
        setMessage(t("production.deliveryError"));
      }
    } catch {
      setMessage(t("production.deliveryError"));
    } finally {
      setBusy(false);
    }
  }

  async function transitionDelivery(
    orderId: string,
    status: DeliveryTransitionRequestStatusEnum,
  ): Promise<void> {
    setBusy(true);
    try {
      const response = await productionOrderDeliveryTransition(orderId, { status });
      if (response.status === 200) {
        await loadDetail(orderId);
      } else {
        setMessage(t("production.deliveryError"));
      }
    } catch {
      setMessage(t("production.deliveryError"));
    } finally {
      setBusy(false);
    }
  }

  function openDeliveryForm(existing: Delivery | null): void {
    setDeliveryForm({
      scheduled_date: existing?.scheduled_date ?? "",
      time_window: (existing?.time_window as DeliveryScheduleRequestRequest["time_window"]) ?? "AM",
      address: existing?.address ?? "",
      contact_name: existing?.contact_name ?? "",
      contact_phone: existing?.contact_phone ?? "",
      installer_name: existing?.installer_name ?? "",
      notes: existing?.notes ?? "",
    });
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

  function openConfirmForm(): void {
    setConfirmName(delivery?.contact_name ?? "");
    setConfirmRut("");
    setCollectPayment(false);
    setCollectAmount("");
    setCollectMethod("CASH");
    setCollectKind("SALDO");
    setSigDrawn(false);
    setConfirmOpen(true);
  }

  async function submitConfirmation(orderId: string): Promise<void> {
    const dataUrl = sigRef.current?.dataURL();
    if (!dataUrl || !confirmName.trim()) return;
    setBusy(true);
    try {
      const response = await productionOrderDeliveryConfirm(orderId, {
        receiver_name: confirmName.trim(),
        receiver_rut: confirmRut.trim() || undefined,
        signature_png: dataUrl.split(",")[1] ?? "",
        payment: collectPayment
          ? {
              amount: collectAmount,
              method: collectMethod,
              kind: collectKind,
            }
          : null,
      });
      if (response.status === 201 || response.status === 200) {
        await loadDetail(orderId);
      } else {
        setMessage(t("production.deliveryConfirmError"));
      }
    } catch {
      setMessage(t("production.deliveryConfirmError"));
    } finally {
      setBusy(false);
    }
  }

  async function openConfirmation(orderId: string): Promise<void> {
    const tab = window.open("", "_blank");
    if (!tab) {
      setMessage(t("production.dispatchNoteError"));
      return;
    }
    try {
      const response = await productionOrderDeliveryConfirmation(orderId);
      if (response.status !== 200) throw new Error("confirmation_error");
      tab.opener = null;
      tab.location.href = response.data.signed_url;
    } catch {
      tab.close();
      setMessage(t("production.dispatchNoteError"));
    }
  }

  async function emitDispatchNoteDte(orderId: string): Promise<void> {
    setBusy(true);
    setMessage("");
    try {
      const response = await productionOrderDispatchNoteDteEmit(orderId, {
        ind_traslado: 1,
      });
      if (response.status === 201) {
        await loadDetail(orderId);
      } else {
        setMessage(t("production.dteEmitError"));
      }
    } catch {
      setMessage(t("production.dteEmitError"));
    } finally {
      setBusy(false);
    }
  }

  async function openDispatchNoteDte(orderId: string): Promise<void> {
    const tab = window.open("", "_blank");
    if (!tab) {
      setMessage(t("production.dteOpenError"));
      return;
    }
    try {
      const response = await productionOrderDispatchNoteDte(orderId);
      if (response.status !== 200) throw new Error("dte_error");
      tab.opener = null;
      tab.location.href = response.data.signed_url;
    } catch {
      tab.close();
      setMessage(t("production.dteOpenError"));
    }
  }

  async function openDispatchNote(orderId: string): Promise<void> {
    const tab = window.open("", "_blank");
    if (!tab) {
      setMessage(t("production.dispatchNoteError"));
      return;
    }
    try {
      const response = await productionOrderDispatchNote(orderId);
      if (response.status !== 200) throw new Error("dispatch_note_error");
      tab.opener = null;
      tab.location.href = response.data.signed_url;
    } catch {
      tab.close();
      setMessage(t("production.dispatchNoteError"));
    }
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
          <div
            className="production-filters"
            role="group"
            aria-label={t("production.statusFilter")}
          >
            {["", "RELEASED", "IN_PROGRESS", "HOLD", "COMPLETED", "DISPATCHED", "INSTALLED"].map(
              (status) => (
                <button
                  key={status || "all"}
                  type="button"
                  className={`production-filter${statusFilter === status ? " is-active" : ""}`}
                  aria-pressed={statusFilter === status}
                  onClick={() => {
                    const next = new URLSearchParams(params);
                    if (status) next.set("status", status);
                    else next.delete("status");
                    setParams(next);
                  }}
                >
                  {status === ""
                    ? t("production.statusAll")
                    : t(orderStatusKey[status] ?? "production.orderReleased")}
                </button>
              ),
            )}
          </div>
          {orders.length === 0 ? <p>{t("production.empty")}</p> : null}
          {statusFilter && orders.length > 0 && filteredOrders.length === 0 ? (
            <p>{t("production.emptyFilter")}</p>
          ) : null}
          <ul>
            {filteredOrders.map((order) => (
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
                {canStep &&
                detail.status === "DISPATCHED" &&
                (!delivery || delivery.status === "DELIVERED") ? (
                  <button
                    type="button"
                    className="production-dispatch production-install"
                    disabled={busy}
                    onClick={() => install(detail.id)}
                  >
                    {t("production.installButton")}
                  </button>
                ) : null}
                {detail.dispatch_note_code ? (
                  <button
                    type="button"
                    className="production-dispatch production-note"
                    onClick={() => void openDispatchNote(detail.id)}
                  >
                    {detail.dispatch_note_code}
                  </button>
                ) : null}
                {detail.dispatch_note_dte ? (
                  <button
                    type="button"
                    className="production-dispatch production-note-dte"
                    title={`${t("production.dteStatus")} · folio ${detail.dispatch_note_dte.folio}`}
                    onClick={() => void openDispatchNoteDte(detail.id)}
                  >
                    {`${t("production.dteStatus")} · ${detail.dispatch_note_dte.folio}`}
                  </button>
                ) : canWrite && detail.dispatch_note_code ? (
                  <button
                    type="button"
                    className="production-dispatch"
                    disabled={busy}
                    onClick={() => void emitDispatchNoteDte(detail.id)}
                  >
                    {t("production.dteEmit")}
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
                const materials = detail.payload?.materials as WorkOrderMaterials | undefined;
                const glasses = (materials?.glasses ?? []) as GlassPiece[];
                if (!glasses.length) return null;
                const polishing = (detail.payload?.glass_polishing ?? []) as PolishingEntry[];
                const quantity = Math.max(1, Number(detail.quantity) || 1);
                return (
                  <GlassSummary
                    glasses={glasses}
                    polishing={polishing}
                    quantity={quantity}
                    onExport={(groups) =>
                      downloadCnc(detail.order_code, `glass.csv`, glassSummaryCsv(groups, quantity))
                    }
                  />
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
                        <select
                          value={optStrategy}
                          onChange={(event) => setOptStrategy(event.target.value)}
                          aria-label={t("production.optimizeStrategy")}
                        >
                          <option value="auto">{t("production.optimizeStrategyAuto")}</option>
                          <option value="fast">{t("production.optimizeStrategyFast")}</option>
                          <option value="deep">{t("production.optimizeStrategyDeep")}</option>
                        </select>
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
                      const dxfExport = detail.payload?.dxf_export as DxfExport | undefined;
                      const opsExport = detail.payload?.operations_export as OpsExport | undefined;
                      const files = Object.entries(cncExport?.files ?? {});
                      const dxfFiles = Object.entries(dxfExport?.files ?? {});
                      const opsFiles = Object.entries(opsExport?.files ?? {});
                      if (!optimization) return null;
                      return (
                        <div className="production-cnc">
                          {canOptimize &&
                          detail.status !== "COMPLETED" &&
                          detail.status !== "DISPATCHED" &&
                          detail.status !== "INSTALLED" ? (
                            <>
                              <button
                                type="button"
                                disabled={busy}
                                onClick={() => exportCnc(detail.id)}
                              >
                                {t("production.cncExportButton")}
                              </button>
                              <button
                                type="button"
                                disabled={busy}
                                onClick={() => exportDxf(detail.id)}
                              >
                                {t("production.dxfExportButton")}
                              </button>
                              <button
                                type="button"
                                disabled={busy}
                                onClick={() => exportOperations(detail.id)}
                              >
                                {t("production.opsExportButton")}
                              </button>
                            </>
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
                          {dxfFiles.map(([filename, content]) => (
                            <button
                              key={filename}
                              type="button"
                              className="production-cnc-file"
                              onClick={() => downloadCnc(detail.order_code, filename, content)}
                            >
                              {filename}
                            </button>
                          ))}
                          {opsExport?.operation_count ? (
                            <span className="production-ops-count">
                              {opsExport.operation_count} {t("production.opsOperationsCount")}
                            </span>
                          ) : null}
                          {opsFiles.map(([filename, content]) => (
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
                        {cutPlan.length || layouts.length ? (
                          <CutPlanView
                            key={optimization.optimized_at ?? "optimization"}
                            optimization={optimization}
                          />
                        ) : null}
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
                                  <td>
                                    {bar.commercial_sku}
                                    {bar.source === "REMNANT" ? (
                                      <span className="production-remnant-tag">
                                        {" "}
                                        {t("production.optimizeRemnantBar")}
                                      </span>
                                    ) : null}
                                  </td>
                                  <td>{bar.stock_length_mm} mm</td>
                                  <td>
                                    {bar.cuts
                                      .map(
                                        (cut) =>
                                          `${cutRoleLabel(cut.role)} ${cut.length_mm}mm u${cut.unit_index ?? 1}`,
                                      )
                                      .join(" · ")}
                                  </td>
                                  <td>
                                    {bar.remainder_mm} mm
                                    {bar.remainder_reusable ? (
                                      <span className="production-remnant-tag">
                                        {" "}
                                        {t("production.optimizeRemnantReusable")}
                                      </span>
                                    ) : null}
                                  </td>
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
                        {(() => {
                          const reservations = optimization?.stock_reservations ?? [];
                          const unmappedSkus = optimization?.unmapped_stock_skus ?? [];
                          if (!reservations.length && !unmappedSkus.length) return null;
                          return (
                            <section
                              className="production-stock-reserve"
                              aria-label={t("production.stockReserveTitle")}
                            >
                              <h4>{t("production.stockReserveTitle")}</h4>
                              {reservations.length ? (
                                <table className="production-plan">
                                  <thead>
                                    <tr>
                                      <th>{t("production.stockKind")}</th>
                                      <th>{t("production.stockSku")}</th>
                                      <th>{t("production.stockOnHand")}</th>
                                      <th>{t("production.stockNeeded")}</th>
                                      <th>{t("production.stockReserved")}</th>
                                      <th>{t("production.stockShort")}</th>
                                      <th>{t("production.stockConsumed")}</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {reservations.map((row, index) => (
                                      <tr key={`${row.kind ?? ""}-${row.sku ?? ""}-${index}`}>
                                        <td>{row.name ?? row.sku ?? "—"}</td>
                                        <td>
                                          {row.sku ?? "—"} · {row.unit ?? ""}
                                        </td>
                                        <td>{row.on_hand ?? "0"}</td>
                                        <td>{row.needed ?? "0"}</td>
                                        <td>{row.reserved ?? "0"}</td>
                                        <td>
                                          {row.short && row.short !== "0" ? (
                                            <strong className="production-stock-short">
                                              {row.short}
                                            </strong>
                                          ) : (
                                            "0"
                                          )}
                                        </td>
                                        <td>
                                          {row.consumed_at
                                            ? new Date(row.consumed_at).toLocaleDateString("es-CL")
                                            : "—"}
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              ) : null}
                              {unmappedSkus.length ? (
                                <p className="production-stock-unmapped">
                                  {t("production.stockUnmapped")}: {unmappedSkus.join(" · ")}
                                </p>
                              ) : null}
                            </section>
                          );
                        })()}
                        {(() => {
                          const remnantLedger = optimization?.remnants;
                          const consumed = remnantLedger?.consumed ?? [];
                          const producedCount =
                            (remnantLedger?.produced_bars?.length ?? 0) +
                            (remnantLedger?.produced_sheets?.length ?? 0);
                          const metrics = optimization?.bars?.metrics;
                          const comparison = optimization?.bars?.strategy_comparison;
                          const comparisonEntries = comparison
                            ? (["fast", "deep"] as const)
                                .filter((key) => comparison[key])
                                .map((key) => ({ key, metrics: comparison[key] }))
                            : [];
                          const unplaced = optimization?.bars?.unplaced ?? [];
                          return (
                            <>
                              {consumed.length || producedCount ? (
                                <p className="production-optimize-remnants">
                                  {consumed.length ? (
                                    <span>
                                      {t("production.optimizeRemnantsUsed")}: {consumed.length}
                                    </span>
                                  ) : null}
                                  {producedCount ? (
                                    <span>
                                      {t("production.optimizeRemnantsProduced")}: {producedCount}
                                    </span>
                                  ) : null}
                                </p>
                              ) : null}
                              {metrics ? (
                                <p className="production-optimize-metrics">
                                  {t("production.optimizeMetrics")}:{" "}
                                  {[
                                    `${metrics.bars ?? 0} barras`,
                                    `${metrics.purchased_bars ?? 0} compra`,
                                    `${metrics.remnant_bars ?? 0} remanentes`,
                                    `${metrics.process_waste_mm ?? "0"} mm desperdicio`,
                                    `${metrics.reusable_remnant_mm ?? "0"} mm reutilizable`,
                                    `${metrics.cuts ?? 0} cortes`,
                                  ].join(" · ")}
                                </p>
                              ) : null}
                              {comparisonEntries.length > 1 ? (
                                <p className="production-optimize-metrics">
                                  {t("production.optimizeComparison")}:{" "}
                                  {comparisonEntries
                                    .map(
                                      ({ key, metrics: m }) =>
                                        `${key}${comparison?.chosen === key ? "*" : ""}: ${m?.purchased_bars ?? 0} barras · ${m?.process_waste_mm ?? "0"} mm`,
                                    )
                                    .join("  |  ")}
                                </p>
                              ) : null}
                              {unplaced.length ? (
                                <p className="production-optimize-unnested" role="alert">
                                  {t("production.optimizeUnplaced")}:{" "}
                                  {unplaced
                                    .map(
                                      (entry) =>
                                        `${entry.piece?.piece_id ?? "?"} (${entry.reason ?? ""})`,
                                    )
                                    .join(" · ")}
                                </p>
                              ) : null}
                            </>
                          );
                        })()}
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
                                    {layout.source === "REMNANT" ? (
                                      <span className="production-remnant-tag">
                                        {t("production.optimizeRemnantBar")}{" "}
                                      </span>
                                    ) : null}
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
              {(() => {
                const canSchedule =
                  canWrite && (detail.status === "COMPLETED" || detail.status === "DISPATCHED");
                return (
                  <section
                    className="production-delivery"
                    aria-label={t("production.deliveryTitle")}
                  >
                    <header className="production-optimize-head">
                      <h3>{t("production.deliveryTitle")}</h3>
                      {delivery ? (
                        <span
                          className={`production-chip delivery-${delivery.status.toLowerCase()}`}
                        >
                          {t(
                            deliveryStatusKey[delivery.status] ??
                              "production.deliveryStatusScheduled",
                          )}
                        </span>
                      ) : null}
                      {!delivery && canSchedule && deliveryForm === null ? (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => openDeliveryForm(null)}
                        >
                          {t("production.deliverySchedule")}
                        </button>
                      ) : null}
                      {canWrite && delivery && delivery.status !== "DELIVERED" ? (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => openDeliveryForm(delivery)}
                        >
                          {t("production.deliveryReschedule")}
                        </button>
                      ) : null}
                      {canStep &&
                      delivery?.status === "SCHEDULED" &&
                      detail.status === "DISPATCHED" ? (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => void transitionDelivery(detail.id, "ON_ROUTE")}
                        >
                          {t("production.deliveryOnRoute")}
                        </button>
                      ) : null}
                      {canStep && delivery?.status === "ON_ROUTE" && !delivery.confirmation ? (
                        <>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => void transitionDelivery(detail.id, "DELIVERED")}
                          >
                            {t("production.deliveryDelivered")}
                          </button>
                          <button
                            type="button"
                            className="production-chip-danger"
                            disabled={busy}
                            onClick={() => void transitionDelivery(detail.id, "FAILED")}
                          >
                            {t("production.deliveryFailed")}
                          </button>
                        </>
                      ) : null}
                      {canStep &&
                      delivery &&
                      (delivery.status === "ON_ROUTE" || delivery.status === "DELIVERED") &&
                      !delivery.confirmation &&
                      !confirmOpen ? (
                        <button type="button" disabled={busy} onClick={openConfirmForm}>
                          {t("production.deliveryConfirm")}
                        </button>
                      ) : null}
                      {delivery?.confirmation ? (
                        <button
                          type="button"
                          className="production-chip delivery-delivered"
                          onClick={() => void openConfirmation(detail.id)}
                        >
                          {delivery.confirmation.confirmation_code}
                        </button>
                      ) : null}
                    </header>
                    {delivery ? (
                      <dl className="production-delivery-facts">
                        <div>
                          <dt>{t("production.deliveryDate")}</dt>
                          <dd>
                            {delivery.scheduled_date} · {delivery.time_window}
                          </dd>
                        </div>
                        <div>
                          <dt>{t("production.deliveryAddress")}</dt>
                          <dd>{delivery.address}</dd>
                        </div>
                        {delivery.contact_name || delivery.contact_phone ? (
                          <div>
                            <dt>{t("production.deliveryContact")}</dt>
                            <dd>
                              {[delivery.contact_name, delivery.contact_phone]
                                .filter(Boolean)
                                .join(" · ")}
                            </dd>
                          </div>
                        ) : null}
                        {delivery.installer_name ? (
                          <div>
                            <dt>{t("production.deliveryInstaller")}</dt>
                            <dd>{delivery.installer_name}</dd>
                          </div>
                        ) : null}
                        {delivery.notes ? (
                          <div>
                            <dt>{t("production.deliveryNotes")}</dt>
                            <dd>{delivery.notes}</dd>
                          </div>
                        ) : null}
                      </dl>
                    ) : null}
                    {confirmOpen && canStep && delivery ? (
                      <form
                        className="production-delivery-form production-confirm-form"
                        onSubmit={(event) => {
                          event.preventDefault();
                          void submitConfirmation(detail.id);
                        }}
                      >
                        <label>
                          {t("production.deliveryReceiver")}
                          <input
                            type="text"
                            required
                            maxLength={200}
                            value={confirmName}
                            onChange={(event) => setConfirmName(event.target.value)}
                          />
                        </label>
                        <label>
                          {t("production.deliveryReceiverRut")}
                          <input
                            type="text"
                            maxLength={30}
                            value={confirmRut}
                            onChange={(event) => setConfirmRut(event.target.value)}
                          />
                        </label>
                        <div className="production-delivery-wide">
                          {t("production.deliverySignature")}
                          <SignaturePad ref={sigRef} onDraw={setSigDrawn} />
                        </div>
                        <label className="production-confirm-collect">
                          <input
                            type="checkbox"
                            checked={collectPayment}
                            onChange={(event) => setCollectPayment(event.target.checked)}
                          />
                          {t("production.deliveryCollect")}
                        </label>
                        {collectPayment ? (
                          <>
                            <label>
                              {t("production.deliveryCollectAmount")}
                              <input
                                type="number"
                                min="1"
                                step="1"
                                required
                                value={collectAmount}
                                onChange={(event) => setCollectAmount(event.target.value)}
                              />
                            </label>
                            <label>
                              {t("projects.paymentMethod")}
                              <select
                                value={collectMethod}
                                onChange={(event) =>
                                  setCollectMethod(event.target.value as MethodEnum)
                                }
                              >
                                <option value="CASH">{t("projects.paymentMethodCash")}</option>
                                <option value="TRANSFER">
                                  {t("projects.paymentMethodTransfer")}
                                </option>
                                <option value="CARD">{t("projects.paymentMethodCard")}</option>
                                <option value="CHECK">{t("projects.paymentMethodCheck")}</option>
                                <option value="OTHER">{t("projects.paymentMethodOther")}</option>
                              </select>
                            </label>
                            <label>
                              {t("projects.paymentKind")}
                              <select
                                value={collectKind}
                                onChange={(event) =>
                                  setCollectKind(event.target.value as PaymentKindEnum)
                                }
                              >
                                <option value="ANTICIPO">
                                  {t("projects.paymentKindAnticipo")}
                                </option>
                                <option value="PARCIAL">{t("projects.paymentKindParcial")}</option>
                                <option value="SALDO">{t("projects.paymentKindSaldo")}</option>
                              </select>
                            </label>
                          </>
                        ) : null}
                        <div className="production-delivery-actions">
                          <button type="submit" disabled={busy || !sigDrawn || !confirmName.trim()}>
                            {t("production.deliveryConfirmSubmit")}
                          </button>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => sigRef.current?.clear()}
                          >
                            {t("production.deliverySignatureClear")}
                          </button>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => setConfirmOpen(false)}
                          >
                            {t("production.deliveryCancel")}
                          </button>
                        </div>
                      </form>
                    ) : null}
                    {!delivery && deliveryForm === null ? (
                      <p className="production-optimize-empty">{t("production.deliveryEmpty")}</p>
                    ) : null}
                    {deliveryForm !== null && canWrite ? (
                      <form
                        className="production-delivery-form"
                        onSubmit={(event) => {
                          event.preventDefault();
                          void saveDelivery(detail.id);
                        }}
                      >
                        <label>
                          {t("production.deliveryDate")}
                          <input
                            type="date"
                            required
                            value={deliveryForm.scheduled_date}
                            onChange={(event) =>
                              setDeliveryForm({
                                ...deliveryForm,
                                scheduled_date: event.target.value,
                              })
                            }
                          />
                        </label>
                        <label>
                          {t("production.deliveryWindow")}
                          <select
                            value={deliveryForm.time_window ?? "AM"}
                            onChange={(event) =>
                              setDeliveryForm({
                                ...deliveryForm,
                                time_window: event.target
                                  .value as DeliveryScheduleRequestRequest["time_window"],
                              })
                            }
                          >
                            <option value="AM">AM</option>
                            <option value="PM">PM</option>
                            <option value="JORNADA">JORNADA</option>
                          </select>
                        </label>
                        <label className="production-delivery-wide">
                          {t("production.deliveryAddress")}
                          <input
                            required
                            value={deliveryForm.address}
                            onChange={(event) =>
                              setDeliveryForm({
                                ...deliveryForm,
                                address: event.target.value,
                              })
                            }
                          />
                        </label>
                        <label>
                          {t("production.deliveryContact")}
                          <input
                            value={deliveryForm.contact_name ?? ""}
                            onChange={(event) =>
                              setDeliveryForm({
                                ...deliveryForm,
                                contact_name: event.target.value,
                              })
                            }
                          />
                        </label>
                        <label>
                          {t("production.deliveryPhone")}
                          <input
                            value={deliveryForm.contact_phone ?? ""}
                            onChange={(event) =>
                              setDeliveryForm({
                                ...deliveryForm,
                                contact_phone: event.target.value,
                              })
                            }
                          />
                        </label>
                        <label>
                          {t("production.deliveryInstaller")}
                          <input
                            value={deliveryForm.installer_name ?? ""}
                            onChange={(event) =>
                              setDeliveryForm({
                                ...deliveryForm,
                                installer_name: event.target.value,
                              })
                            }
                          />
                        </label>
                        <label className="production-delivery-wide">
                          {t("production.deliveryNotes")}
                          <input
                            value={deliveryForm.notes ?? ""}
                            onChange={(event) =>
                              setDeliveryForm({
                                ...deliveryForm,
                                notes: event.target.value,
                              })
                            }
                          />
                        </label>
                        <div className="production-delivery-actions">
                          <button type="submit" disabled={busy}>
                            {t("production.deliverySave")}
                          </button>
                          <button type="button" onClick={() => setDeliveryForm(null)}>
                            {t("production.deliveryCancel")}
                          </button>
                        </div>
                      </form>
                    ) : null}
                  </section>
                );
              })()}
              {(() => {
                const nextStep = detail.steps.find(
                  (step) => step.status !== "DONE" && stepActions(step).length > 0,
                );
                if (
                  !nextStep ||
                  detail.status === "COMPLETED" ||
                  detail.status === "DISPATCHED" ||
                  detail.status === "INSTALLED"
                )
                  return null;
                return (
                  <div
                    className="production-next"
                    role="group"
                    aria-label={t("production.nextStep")}
                  >
                    <span className="production-next-label">
                      {t("production.nextStep")}: <strong>{nextStep.label}</strong>
                      {nextStep.work_center_code ? ` · ${nextStep.work_center_code}` : ""}
                    </span>
                    <span className="production-step-actions">
                      {stepActions(nextStep).map((stepAction) => (
                        <button
                          key={stepAction}
                          type="button"
                          disabled={busy}
                          onClick={() => transition(nextStep.id, stepAction, detail.id)}
                        >
                          {t(actionLabel[stepAction])}
                        </button>
                      ))}
                    </span>
                  </div>
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
