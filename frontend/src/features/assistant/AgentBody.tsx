import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { ApiError } from "../../api/apiMutator";
import { aiAgent } from "../../api/generated/dekopen";
import type { AiAgentResponse } from "../../api/generated/models/aiAgentResponse";
import type { AiAgentStep } from "../../api/generated/models/aiAgentStep";
import type { AiAgentHistoryRequest } from "../../api/generated/models/aiAgentHistoryRequest";
import { t } from "../../i18n/es-CL";
import type { DesignOp } from "../commands/types";
import { describeDesignOp, designAssistProduct } from "../canvas/designOps";
import type { ProductJson } from "../canvas/productEditing";
import { useDesignOpsBridge } from "./assistantContext";

type Turn = {
  goal: string;
  answer: AiAgentResponse;
  /** The product the ops steps were validated against — a later commit makes
   * them stale, so applying them then is refused. */
  product: { [key: string]: unknown } | null;
  /** Turn indexes whose ops step already committed — re-applying a consumed
   * plan would mint duplicate structural ids against a changed product. */
  appliedOps: Set<number>;
};

function asDesignOps(step: AiAgentStep): DesignOp[] {
  return (step.ops ?? []).filter((item): item is DesignOp => typeof item.op === "string");
}

const SURFACE_LABELS: Record<string, string> = {
  dashboard: "panel",
  projects: "proyectos",
  project: "proyecto",
  position: "vano",
  quotation: "cotización",
  catalog: "catálogo",
  production: "producción",
  work_order: "orden de trabajo",
  clients: "clientes",
  purchasing: "compras",
  settings: "configuración",
};

/** The DEKOPEN agent: a goal turns into a server-side observe → plan loop.
 * The backend executes the queries and validates every step; this panel
 * renders provenance (what it consulted), lets the human apply design ops
 * through the canvas's own commit, and deep-links consequential actions —
 * it never executes them itself. */
export function AgentBody({
  organizationId,
  surface,
  refs,
}: {
  organizationId: string;
  surface: string;
  refs: Record<string, string>;
}): JSX.Element {
  const navigate = useNavigate();
  const bridge = useDesignOpsBridge();
  const [goal, setGoal] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [thread, setThread] = useState<Turn[]>([]);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  /** One operation key per goal — a retried submit replays the audited loop
   * (each round is suffixed server-side) instead of debiting twice. */
  const operationKey = useRef<{ key: string; goal: string } | null>(null);
  const requestSeq = useRef(0);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  async function run(): Promise<void> {
    const trimmed = goal.trim();
    if (!trimmed || busy) return;
    setBusy(true);
    setMessage("");
    if (!operationKey.current || operationKey.current.goal !== trimmed) {
      operationKey.current = { key: crypto.randomUUID(), goal: trimmed };
    }
    const seq = ++requestSeq.current;
    // The live product rides along only on the position surface — elsewhere
    // ops steps can't be validated and are dropped server-side anyway.
    const product = surface === "position" && bridge ? bridge.product : null;
    const history: AiAgentHistoryRequest[] = thread.slice(-3).flatMap((turn) => [
      { role: "user" as const, content: turn.goal.slice(0, 1900) },
      { role: "agent" as const, content: turn.answer.reply.slice(0, 1900) },
    ]);
    try {
      const response = await aiAgent(
        {
          surface,
          refs,
          goal: trimmed,
          // The ops contract validates the stable-id projection, not the raw
          // product — the same wire shape AssistantPanel sends.
          ...(product ? { product: designAssistProduct(product as ProductJson) } : {}),
          history,
          operation_key: operationKey.current.key,
        },
        { headers: { "X-Organization-ID": organizationId } },
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      if (seq !== requestSeq.current) return;
      setThread((prev) => [
        ...prev,
        { goal: trimmed, answer: response.data, product, appliedOps: new Set() },
      ]);
      setGoal("");
      operationKey.current = null;
    } catch (error) {
      if (seq !== requestSeq.current) return;
      setMessage(
        error instanceof ApiError && typeof error.payload === "object" && error.payload !== null
          ? String(
              (error.payload as { error?: { detail?: unknown } }).error?.detail ?? t("agent.error"),
            )
          : t("agent.error"),
      );
    } finally {
      if (seq === requestSeq.current) setBusy(false);
    }
  }

  function applyOps(turnIndex: number, stepIndex: number, ops: DesignOp[]): void {
    const turn = thread[turnIndex];
    // The bridge must still close over the exact product the ops were
    // validated against — a commit in between made them stale.
    if (!bridge || !turn || turn.product !== bridge.product) return;
    bridge.apply(ops);
    setThread((prev) =>
      prev.map((item, i) =>
        i === turnIndex ? { ...item, appliedOps: new Set(item.appliedOps).add(stepIndex) } : item,
      ),
    );
  }

  return (
    <>
      <div className="ask-dock__thread">
        {thread.length === 0 ? (
          <p className="ask-dock__hint">{t("agent.hint")}</p>
        ) : (
          thread.map((turn, turnIndex) => (
            <div key={turnIndex} className="ask-dock__turn">
              <p className="ask-dock__question">{turn.goal}</p>
              {turn.answer.queries.length ? (
                <ul className="ask-dock__queries">
                  {turn.answer.queries.map((query, i) => (
                    <li key={i}>
                      {query.status === "ok"
                        ? t("agent.queried").replace(
                            "{surface}",
                            SURFACE_LABELS[query.surface] ?? query.surface,
                          )
                        : t("agent.queryFailed").replace(
                            "{surface}",
                            SURFACE_LABELS[query.surface] ?? query.surface,
                          )}
                    </li>
                  ))}
                </ul>
              ) : null}
              <p className="ask-dock__answer">{turn.answer.reply}</p>
              {turn.answer.warnings?.length ? (
                <ul className="ask-dock__warnings">
                  {turn.answer.warnings.map((warning, i) => (
                    <li key={i}>{warning}</li>
                  ))}
                </ul>
              ) : null}
              {turn.answer.rejected?.length ? (
                <ul className="ask-dock__warnings">
                  {turn.answer.rejected.map((item, i) => (
                    <li key={i}>
                      {item.op ?? "—"}: {item.reason}
                    </li>
                  ))}
                </ul>
              ) : null}
              {turn.answer.steps.length ? (
                <div className="ask-dock__actions">
                  {turn.answer.steps.map((step, stepIndex) => {
                    if (step.kind === "navigate" && step.path) {
                      return (
                        <button
                          key={stepIndex}
                          type="button"
                          className="ask-dock__action"
                          onClick={() => navigate(step.path as string)}
                        >
                          {step.label}
                        </button>
                      );
                    }
                    if (step.kind === "prepare" && step.path) {
                      return (
                        <button
                          key={stepIndex}
                          type="button"
                          className="ask-dock__action ask-dock__action--prepare"
                          title={t("agent.prepareHint")}
                          onClick={() => navigate(step.path as string)}
                        >
                          {t("agent.prepare")} {step.label}
                        </button>
                      );
                    }
                    if (step.kind === "ops") {
                      const ops = asDesignOps(step);
                      if (!ops.length) return null;
                      const applied = turn.appliedOps.has(stepIndex);
                      const stale = !bridge || turn.product !== bridge.product;
                      return (
                        <div key={stepIndex} className="ask-dock__ops">
                          <ul>
                            {ops.map((op, i) => (
                              <li key={i}>
                                {turn.product
                                  ? describeDesignOp(
                                      op,
                                      turn.product as ProductJson,
                                      ops.slice(0, i),
                                    )
                                  : op.op}
                              </li>
                            ))}
                          </ul>
                          <button
                            type="button"
                            className="ask-dock__action"
                            disabled={applied || stale || !bridge}
                            title={stale && bridge ? t("assistant.stale") : undefined}
                            onClick={() => applyOps(turnIndex, stepIndex, ops)}
                          >
                            {applied
                              ? t("agent.applied")
                              : t("assistant.apply").replace("{count}", String(ops.length))}
                          </button>
                        </div>
                      );
                    }
                    return null;
                  })}
                </div>
              ) : null}
              <p className="ask-dock__meta">
                {turn.answer.model} · {turn.answer.credits_debited} {t("assistant.credits")}
                {turn.answer.job_id ? (
                  <>
                    {" · "}
                    <button
                      type="button"
                      className="ask-dock__meta-link"
                      onClick={() => navigate(`/assistant?job=${turn.answer.job_id}`)}
                    >
                      {t("aiws.openWorkspace")}
                    </button>
                  </>
                ) : null}
              </p>
            </div>
          ))
        )}
        {busy ? <p className="ask-dock__busy">{t("agent.thinking")}</p> : null}
      </div>
      {message ? <p className="ask-dock__error">{message}</p> : null}
      <form
        className="ask-dock__form"
        onSubmit={(event) => {
          event.preventDefault();
          run().catch(() => undefined);
        }}
      >
        <textarea
          ref={inputRef}
          value={goal}
          maxLength={2000}
          rows={2}
          placeholder={t("agent.placeholder")}
          aria-label={t("agent.placeholder")}
          onChange={(event) => setGoal(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              run().catch(() => undefined);
            }
          }}
          disabled={busy}
        />
        <button type="submit" disabled={busy || !goal.trim()}>
          {t("agent.send")}
        </button>
      </form>
    </>
  );
}
