import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import {
  productionOrderDetail,
  productionOrders,
  productionStepTransition,
} from "../../api/generated/dekopen";
import type {
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

type StepAction = "START" | "COMPLETE" | "BLOCK" | "UNBLOCK" | "NOTE";

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
};

function stepActions(step: ProductionStep): StepAction[] {
  switch (step.status) {
    case "READY":
    case "PENDING":
      return ["START", "BLOCK", "NOTE"];
    case "IN_PROGRESS":
      return ["COMPLETE", "BLOCK", "NOTE"];
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
  const mounted = useRef(true);
  useEffect(
    () => () => {
      mounted.current = false;
    },
    [],
  );

  const selectedId = params.get("order") ?? "";

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
    }
  }, []);

  useEffect(() => {
    void loadOrders().catch(() => setMessage(t("production.loadError")));
  }, [loadOrders]);

  useEffect(() => {
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
      stepAction === "NOTE" || stepAction === "BLOCK" ? note || undefined : undefined;
    void action(
      productionStepTransition(stepId, { action: stepAction, note: noteValue ?? null }),
      orderId,
    );
  }

  const canAct = role === "OWNER" || role === "WORKSHOP_MANAGER" || role === "INSTALLER";
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
                    {detail.status !== "COMPLETED" ? (
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
