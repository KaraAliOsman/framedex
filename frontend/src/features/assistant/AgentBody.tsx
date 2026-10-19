import { ValidatedForm } from "../../ui/FormValidation";
import { Icon } from "../../ui/Icon";
import { AI_PHASES } from "./providerLabels";
import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { ApiError } from "../../api/apiMutator";
import {
  aiAgent,
  aiJobApprove,
  aiJobCancel,
  aiJobMessageCreate,
  aiJobOutcomeCreate,
  aiJobRetrieve,
  aiJobRetry,
  aiThreadTimeline,
} from "../../api/generated/dekopen";
import type { AiTimelineEntry } from "../../api/generated/models/aiTimelineEntry";
import type { AiAgentStep } from "../../api/generated/models/aiAgentStep";
import type { AiJobDetail } from "../../api/generated/models/aiJobDetail";
import { t } from "../../i18n/es-CL";
import { jobErrorKey } from "../jobs/jobError";
import type { DesignOperation } from "../../api/generated/models";
import { describeDesignOp, designAssistProduct, productFingerprint } from "../canvas/designOps";
import type { ProductJson } from "../canvas/productEditing";
import { useDesignOpsBridge } from "./assistantContext";
import { BatchOpsStep } from "./BatchOpsStep";
import { ProjectOpsStep } from "./ProjectOpsStep";
import { DocumentLayoutStep } from "./DocumentLayoutStep";
import { SimulationPreview } from "./SimulationPreview";
import { RejectedOperations } from "./RejectedOperations";
import { publishAssistantJob, presenceState } from "./useAssistantPresence";
import { Companion } from "./Companion";
import { assistantText, SURFACE_LABELS } from "./surfaces";
import { AttachmentTray, SentAttachments, type ComposerAttachment } from "./Attachments";
import { Receipt } from "./Receipt";
import type { AutonomyPolicy, InteractionMode } from "./copilotPrefs";

/** The durable worker can leave the job running far longer than a request
 * timeout — the dock polls the job record and renders the stored result
 * once the round settles. */
const LIVE_STATES = new Set(["QUEUED", "PLANNING", "RUNNING"]);
const TERMINAL_STATES = new Set(["FAILED", "CANCELED"]);
const STATE_LABEL: Record<string, string> = {
  QUEUED: "agent.state.queued",
  PLANNING: "agent.state.planning",
  RUNNING: "agent.state.running",
  WAITING_FOR_USER: "agent.state.waiting_for_user",
  WAITING_FOR_APPROVAL: "agent.state.waiting_for_approval",
} as const;
const POLL_MS = 1500;
const POLL_BACKOFF_MAX_MS = 15_000;
const POLL_FAIL_BANNER_AT = 3;

/** One turn in the dock thread — rebuilt from the job's durable transcript
 * so a reopened dock (or a job started elsewhere) shows the same work. */
type Turn = {
  goal: string;
  /** The server marks replayed goals — a retry is not a retyped message. */
  replay: boolean;
  /** The transcript's agent entry; null while the round is pending or on a
   * failed round (errorCode then carries the classified code). */
  result: TranscriptAgentTurn | null;
  errorCode: string | null;
  /** The product the ops steps were validated against — captured at
   * send-time; turns resumed from storage lose it and carry the durable
   * product_sig fingerprint instead (server-persisted on the user turn). */
  product: { [key: string]: unknown } | null;
  /** Fingerprint of the product this round's ops were validated against —
   * survives reload via the transcript so a restored apply still refuses
   * onto a changed design. */
  productSig: string | null;
  /** Position of this turn's agent/error entry inside the job transcript —
   * outcomes are keyed on that index, not the thread's. */
  transcriptIndex: number;
  appliedOps: Set<number>;
  declinedOps: Set<number>;
  /** Sealed on the user turn: mode, effective policy and attachments. */
  mode?: InteractionMode;
  attachments?: SealedAttachment[];
};

export type SealedAttachment = {
  id: string;
  file_name: string;
  kind: string;
  status?: string;
  file_sha256?: string;
};

interface TranscriptAgentTurn {
  clarify?: { question: string; options: { label: string; value: string }[] } | null;
  role?: string;
  text?: string;
  replay?: boolean;
  product_sig?: string;
  reply?: string;
  queries?: { surface?: string; tool?: string; status?: string }[];
  claims?: { text?: string; evidence?: string[] }[];
  questions?: string[];
  steps?: AiAgentStep[];
  warnings?: string[];
  rejected?: { op?: string; reason?: string }[];
  artifacts?: unknown[];
  code?: string;
  interaction_mode?: InteractionMode;
  attachments?: SealedAttachment[];
}

/** Transcript → thread: user entries pair with the agent/error entry that
 * answers them; a trailing user entry is a round still in flight. */
function threadFromJob(job: AiJobDetail): Turn[] {
  const turns: Turn[] = [];
  let pending: {
    text: string;
    replay: boolean;
    sig: string | null;
    mode?: InteractionMode;
    attachments?: SealedAttachment[];
  } | null = null;
  const entries = (job.transcript ?? []) as TranscriptAgentTurn[];
  for (const [index, entry] of entries.entries()) {
    if (!entry || typeof entry !== "object") continue;
    if (entry.role === "user") {
      pending = {
        text: String(entry.text ?? ""),
        replay: Boolean(entry.replay),
        sig: typeof entry.product_sig === "string" ? entry.product_sig : null,
        mode: entry.interaction_mode,
        attachments: Array.isArray(entry.attachments) ? entry.attachments : undefined,
      };
    } else if (entry.role === "agent") {
      turns.push({
        goal: pending?.text ?? "",
        replay: pending?.replay ?? false,
        result: entry,
        errorCode: null,
        product: null,
        productSig: pending?.sig ?? null,
        transcriptIndex: index,
        appliedOps: new Set(),
        declinedOps: new Set(),
        mode: pending?.mode,
        attachments: pending?.attachments,
      });
      pending = null;
    } else if (entry.role === "error") {
      turns.push({
        goal: pending?.text ?? "",
        replay: pending?.replay ?? false,
        result: null,
        errorCode: typeof entry.code === "string" ? entry.code : null,
        product: null,
        productSig: pending?.sig ?? null,
        transcriptIndex: index,
        appliedOps: new Set(),
        declinedOps: new Set(),
        mode: pending?.mode,
        attachments: pending?.attachments,
      });
      pending = null;
    }
  }
  if (pending) {
    turns.push({
      goal: pending.text,
      replay: pending.replay,
      result: null,
      errorCode: null,
      product: null,
      productSig: pending.sig,
      transcriptIndex: entries.length - 1,
      appliedOps: new Set(),
      declinedOps: new Set(),
      mode: pending.mode,
      attachments: pending.attachments,
    });
  }
  // Jobs settled before transcript turns carried the result shape still
  // hold the aggregate in `result` — surface it as the last turn rather
  // than rendering an empty conversation.
  // A first round still queued/running has no transcript yet (the worker
  // writes it at the end): show the sent request instead of an empty thread.
  if (!turns.length && !job.result && job.goal && LIVE_STATES.has(job.state)) {
    turns.push({
      goal: job.goal,
      replay: false,
      result: null,
      errorCode: null,
      product: null,
      productSig: null,
      transcriptIndex: 0,
      appliedOps: new Set(),
      declinedOps: new Set(),
      mode: (job.interaction_mode as InteractionMode | null | undefined) ?? undefined,
    });
  }
  if (!turns.some((turn) => turn.result !== null) && job.result) {
    turns.push({
      goal: job.goal ?? "",
      replay: false,
      result: job.result as TranscriptAgentTurn,
      errorCode: null,
      product: null,
      productSig: null,
      transcriptIndex: entries.length - 1,
      appliedOps: new Set(),
      declinedOps: new Set(),
    });
  }
  return turns;
}

function asDesignOps(step: AiAgentStep): DesignOperation[] {
  return (step.ops ?? []).map((item) => ({ ...item }));
}

export { SURFACE_LABELS };

/** The DEKOPEN agent: a goal turns into a server-side observe → plan loop.
 * The backend executes the queries and validates every step; this panel
 * renders provenance (what it consulted), lets the human apply design ops
 * through the canvas's own commit, and deep-links consequential actions —
 * it never executes them itself. */
export function AgentBody({
  organizationId,
  userId,
  surface,
  refs,
  onJobState,
  onComposing,
  threadId,
  onThread,
  interactionMode,
  autonomy,
  onInteractionMode,
  prefill,
  contextLabel,
  onClearContext,
}: {
  organizationId: string;
  userId?: string | null;
  /** Read context of the next send (route + selection). It never re-keys
   * the conversation: the thread is the identity. */
  surface: string;
  refs: Record<string, string>;
  /** The conversation this body shows; null = a new one opens on send. */
  threadId: string | null;
  onThread?: (threadId: string) => void;
  interactionMode: InteractionMode;
  autonomy: AutonomyPolicy;
  onInteractionMode?: (mode: InteractionMode) => void;
  /** A delegation from a manual surface: prefilled text the person sends. */
  prefill?: { text: string; nonce: number } | null;
  contextLabel?: string | null;
  onClearContext?: () => void;
  /** Lifts the bound job's lifecycle up to the dock header orb. */
  onJobState?: (state: string | null) => void;
  /** Lifts composition state — while a goal is typed the orb reads INPUT. */
  onComposing?: (composing: boolean) => void;
}): JSX.Element {
  const navigate = useNavigate();
  const bridge = useDesignOpsBridge();
  const queryClient = useQueryClient();
  const undos = useRef(new Map<string, () => boolean>());
  const [undone, setUndone] = useState(new Set<string>());
  const [goal, setGoal] = useState("");
  const [busy, setBusy] = useState(false);
  const [attachments, setAttachments] = useState<ComposerAttachment[]>([]);
  /** Earlier entries of this thread (older jobs and legacy chat turns). */
  const [earlier, setEarlier] = useState<AiTimelineEntry[]>([]);
  const [earlierCursor, setEarlierCursor] = useState<string | null>(null);
  /** The thread id this body just received from its own send — adopting it
   * must not reset the live conversation. */
  const adoptedThread = useRef<string | null>(null);
  /** The job this dock is bound to — found by continuity on mount, created
   * by the next send when none applies. */
  const [job, setJob] = useState<AiJobDetail | null>(null);
  useEffect(() => {
    onJobState?.(job?.state ?? null);
    if (job) publishAssistantJob(queryClient, { organizationId, userId, surface, refs }, job);
  }, [job, onJobState, queryClient, organizationId, userId, surface, refs]);
  useEffect(() => {
    onComposing?.(!!goal.trim());
  }, [goal, onComposing]);
  const [message, setMessage] = useState("");
  const [thread, setThread] = useState<Turn[]>([]);
  /** Instructions typed while a run is live — the backend can't interleave
   * a second run, so they queue client-side and post once the job settles. */
  const [pending, setPending] = useState<string[]>([]);
  const pendingRef = useRef<string[]>([]);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  /** One operation key per goal — a retried submit replays the audited loop
   * (each round is suffixed server-side) instead of debiting twice. */
  const operationKey = useRef<{ key: string; goal: string } | null>(null);
  /** The request just sent, shown until the worker writes its turn. */
  const sentTurn = useRef<Turn | null>(null);
  const requestSeq = useRef(0);
  const pollTimer = useRef<number | null>(null);
  const pollFailures = useRef(0);
  /** Persistent poll loss — the live run is probably still working, the dock
   * just can't see it right now. */
  const [offline, setOffline] = useState(false);
  const headers = { headers: { "X-Organization-ID": organizationId } };

  function clearPoll(): void {
    if (pollTimer.current !== null) {
      window.clearTimeout(pollTimer.current);
      pollTimer.current = null;
    }
  }

  /** Poll the bound job until it settles — the transcript thread refreshes
   * on every tick so a live round visibly accumulates work. `product` is
   * this session's sent snapshot — ops turns rebind it so the stale-plan
   * guard keeps refusing after a commit swaps the live product. */
  function watch(
    jobId: string,
    seq: number,
    product: { [key: string]: unknown } | null = null,
  ): void {
    clearPoll();
    const tick = async (): Promise<void> => {
      if (seq !== requestSeq.current) return;
      try {
        const detail = await aiJobRetrieve(jobId, headers);
        if (seq !== requestSeq.current) return;
        if (detail.status !== 200) {
          // The job vanished or the role lost access — stop watching rather
          // than spin a dead poll.
          setBusy(false);
          return;
        }
        const next = detail.data;
        setJob(next);
        pollFailures.current = 0;
        setOffline(false);
        const built = threadFromJob(next);
        if (product) {
          for (const turn of built) {
            // Restored turns (productSig set) keep their durable fingerprint —
            // backfilling the live product onto them would let stale ops
            // apply onto a changed design.
            if (
              turn.product === null &&
              turn.productSig === null &&
              turn.result?.steps?.some((step) => step.kind === "ops")
            ) {
              turn.product = product;
            }
          }
        }
        // Until the worker writes the new user turn, keep showing it.
        const last = built.at(-1);
        if (
          sentTurn.current &&
          LIVE_STATES.has(next.state) &&
          (!last || last.result !== null || last.errorCode !== null)
        ) {
          built.push({ ...sentTurn.current, transcriptIndex: (last?.transcriptIndex ?? -1) + 1 });
        }
        if (!LIVE_STATES.has(next.state)) sentTurn.current = null;
        setThread(built);
        if (LIVE_STATES.has(next.state)) {
          pollTimer.current = window.setTimeout(() => void tick(), POLL_MS);
        } else {
          setBusy(false);
          // Changes the round saved itself (Omitir todo) must show at once
          // in Mesa and Estudio — the same work, re-read from the server.
          if (next.receipt?.objects.some((item) => item.status === "applied"))
            void queryClient.invalidateQueries();
          // Queued instructions flush in the job-state effect — it runs
          // after this render commits, even if one queued mid-settle.
        }
      } catch {
        if (seq !== requestSeq.current) return;
        // A transient poll failure is not a job failure — back off
        // exponentially (2× to a 15s cap) and surface the offline state
        // once it is clearly persistent, not a single blip.
        pollFailures.current += 1;
        if (pollFailures.current >= POLL_FAIL_BANNER_AT) setOffline(true);
        const delay = Math.min(POLL_BACKOFF_MAX_MS, POLL_MS * 2 ** pollFailures.current);
        pollTimer.current = window.setTimeout(() => void tick(), delay);
      }
    };
    void tick();
  }

  /** Continuity is the thread: reopening the popup, navigating or choosing
   * another sheet keeps the same conversation. Loading it is a pure read —
   * the timeline and the job record, never a model call. */
  useEffect(() => {
    if (threadId !== null && threadId === adoptedThread.current) return;
    adoptedThread.current = threadId;
    const seq = ++requestSeq.current;
    setThread([]);
    setJob(null);
    setEarlier([]);
    setEarlierCursor(null);
    setMessage("");
    setBusy(false);
    pendingRef.current = [];
    setPending([]);
    operationKey.current = null;
    if (!threadId) return;
    let cancelled = false;
    void (async () => {
      try {
        const timeline = await aiThreadTimeline(threadId, undefined, headers);
        if (cancelled || seq !== requestSeq.current || timeline.status !== 200) return;
        const [latest, ...older] = timeline.data.items;
        setEarlier(latest && latest.kind === "job" ? older : timeline.data.items);
        setEarlierCursor(timeline.data.next_cursor);
        if (!latest || latest.kind !== "job") return;
        const detail = await aiJobRetrieve(latest.id, headers);
        if (cancelled || seq !== requestSeq.current || detail.status !== 200) return;
        setJob(detail.data);
        setThread(threadFromJob(detail.data));
        if (LIVE_STATES.has(detail.data.state)) {
          setBusy(true);
          watch(detail.data.id, seq);
        }
      } catch {
        // Recovery is best-effort — the thread stays openable from history.
      }
    })();
    return () => {
      cancelled = true;
      clearPoll();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- the thread id
    // is the identity; read context changes never reload the conversation.
  }, [organizationId, threadId]);

  async function loadEarlier(): Promise<void> {
    if (!threadId || !earlierCursor) return;
    try {
      const page = await aiThreadTimeline(threadId, { cursor: earlierCursor }, headers);
      if (page.status !== 200) return;
      setEarlier((previous) => [...previous, ...page.data.items]);
      setEarlierCursor(page.data.next_cursor);
    } catch {
      setMessage("No pudimos cargar mensajes anteriores. Inténtalo de nuevo.");
    }
  }

  // A delegation from a manual surface prefills the composer; the person
  // reviews and sends it (opening never calls the model).
  useEffect(() => {
    if (!prefill) return;
    setGoal(prefill.text);
    inputRef.current?.focus();
  }, [prefill]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  async function run(): Promise<void> {
    const trimmed = goal.trim();
    if (!trimmed) return;
    // A terminal job can't take follow-ups — start a fresh one instead of
    // bouncing the message off a 409.
    const followTarget = job && !TERMINAL_STATES.has(job.state) ? job : null;
    if (followTarget && LIVE_STATES.has(followTarget.state)) {
      // Mid-run instructions are accepted and delivered once the run
      // settles — the claim chain can't interleave a second run anyway.
      pendingRef.current = [...pendingRef.current, trimmed];
      setPending(pendingRef.current);
      setGoal("");
      return;
    }
    if (busy) return;
    await send(trimmed);
  }

  async function send(trimmed: string, modeOverride?: InteractionMode): Promise<void> {
    const followTarget = job && !TERMINAL_STATES.has(job.state) ? job : null;
    const mode = modeOverride ?? interactionMode;
    const ready = attachments.filter((item) => item.state === "ready" && item.id);
    if (attachments.some((item) => item.state === "uploading")) {
      setMessage("Espera a que terminen de subir los archivos.");
      return;
    }
    const attachmentIds = ready.map((item) => item.id as string);
    setBusy(true);
    setMessage("");
    if (!operationKey.current || operationKey.current.goal !== trimmed) {
      operationKey.current = { key: crypto.randomUUID(), goal: trimmed };
    }
    const seq = ++requestSeq.current;
    clearPoll();
    // The live product rides along only on the position surface — elsewhere
    // ops steps can't be validated and are dropped server-side anyway.
    const product = surface === "position" && bridge ? bridge.product : null;
    // The sig persists on the user turn — a restored ops step applies only
    // while the live product still matches what the ops validated against.
    const productSig = product
      ? productFingerprint(designAssistProduct(product as ProductJson))
      : null;
    try {
      let jobId: string;
      if (followTarget) {
        // Follow-ups continue the same durable job — transcript, plan and
        // artifacts accumulate on one record instead of fragmenting.
        const response = await aiJobMessageCreate(
          followTarget.id,
          {
            message: trimmed,
            // Live refs refresh volatile pointers (the canvas selection) so
            // a follow-up's "this" resolves to what's selected now.
            refs,
            ...(product ? { product: designAssistProduct(product as ProductJson) } : {}),
            ...(productSig ? { product_sig: productSig } : {}),
            autonomy,
            interaction_mode: mode,
            ...(attachmentIds.length ? { attachment_ids: attachmentIds } : {}),
          },
          {
            headers: {
              ...headers.headers,
              "X-Operation-Key": operationKey.current.key,
            },
          },
        );
        if (response.status !== 202) {
          throw new ApiError(response.status, response.data);
        }
        jobId = followTarget.id;
      } else {
        const response = await aiAgent(
          {
            surface,
            refs,
            goal: trimmed,
            ...(product ? { product: designAssistProduct(product as ProductJson) } : {}),
            ...(productSig ? { product_sig: productSig } : {}),
            history: [],
            operation_key: operationKey.current.key,
            autonomy,
            interaction_mode: mode,
            ...(threadId ? { thread_id: threadId } : {}),
            ...(attachmentIds.length ? { attachment_ids: attachmentIds } : {}),
          },
          headers,
        );
        if (response.status !== 202) {
          throw new ApiError(response.status, response.data);
        }
        jobId = String(response.data.job_id);
        const opened = response.data.thread_id ? String(response.data.thread_id) : null;
        if (opened && opened !== threadId) {
          adoptedThread.current = opened;
          onThread?.(opened);
        }
      }
      if (seq !== requestSeq.current) return;
      // Optimistic user turn — the transcript rebuild replaces it on the
      // first poll, but the goal should be visible immediately.
      const optimistic: Turn = {
        goal: trimmed,
        replay: false,
        result: null,
        errorCode: null,
        product,
        productSig,
        transcriptIndex: 0,
        appliedOps: new Set(),
        declinedOps: new Set(),
        mode,
        attachments: ready.map((item) => ({
          id: item.id as string,
          file_name: item.name,
          kind: item.kind ?? "",
        })),
      };
      sentTurn.current = optimistic;
      setThread((prev) => [
        ...prev,
        {
          goal: trimmed,
          replay: false,
          result: null,
          errorCode: null,
          product,
          productSig,
          transcriptIndex: prev.length ? (prev[prev.length - 1]?.transcriptIndex ?? -1) + 1 : 0,
          appliedOps: new Set(),
          declinedOps: new Set(),
          mode,
          attachments: ready.map((item) => ({
            id: item.id as string,
            file_name: item.name,
            kind: item.kind ?? "",
          })),
        },
      ]);
      setGoal("");
      setAttachments([]);
      operationKey.current = null;
      watch(jobId, seq, product);
      return;
    } catch (error) {
      if (seq !== requestSeq.current) return;
      setBusy(false);
      setMessage(
        error instanceof ApiError && typeof error.payload === "object" && error.payload !== null
          ? String(
              (error.payload as { error?: { detail?: unknown } }).error?.detail ?? t("agent.error"),
            )
          : t("agent.error"),
      );
    }
  }

  async function cancelJob(): Promise<void> {
    if (!job || !LIVE_STATES.has(job.state)) return;
    try {
      const response = await aiJobCancel(job.id, headers);
      if (response.status === 200) {
        setJob(response.data as AiJobDetail);
        setThread(threadFromJob(response.data as AiJobDetail));
        setBusy(false);
      }
    } catch {
      setMessage(t("agent.error"));
    }
  }

  async function retryJob(): Promise<void> {
    if (!job || job.state !== "FAILED_RETRYABLE" || busy) return;
    setBusy(true);
    setMessage("");
    const seq = requestSeq.current;
    try {
      const response = await aiJobRetry(job.id, headers);
      if (response.status !== 202) throw new ApiError(response.status, response.data);
      watch(job.id, seq);
    } catch {
      setBusy(false);
      setMessage(t("agent.error"));
    }
  }

  /** «Con aprobación»: one approval applies the prepared coherent set (and
   * the price + draft PDF of flow A11) with the person's own session. */
  async function approveAll(): Promise<void> {
    if (!job || busy) return;
    setBusy(true);
    setMessage("");
    try {
      const response = await aiJobApprove(job.id, headers);
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      setJob(response.data as AiJobDetail);
      setThread(threadFromJob(response.data as AiJobDetail));
      void queryClient.invalidateQueries();
    } catch (error) {
      setMessage(
        error instanceof ApiError && typeof error.payload === "object" && error.payload !== null
          ? String(
              (error.payload as { error?: { detail?: unknown } }).error?.detail ?? t("agent.error"),
            )
          : t("agent.error"),
      );
    } finally {
      setBusy(false);
    }
  }

  function startFresh(): void {
    requestSeq.current += 1;
    clearPoll();
    setJob(null);
    setThread([]);
    setMessage("");
    setBusy(false);
    operationKey.current = null;
    // Instructions queued against the old job belong to its conversation —
    // leaving them queued would post them onto the NEXT job the dock binds.
    pendingRef.current = [];
    setPending([]);
    setAttachments([]);
    inputRef.current?.focus();
  }

  /** §08 measurement — report the human's decision on a proposed step back
   * to the job. Best-effort: the server dedupes on (turn, step, action), so
   * a retry or double click can never double-count; a reporting failure
   * must never block the UI. turnIndex indexes the transcript (user turns
   * included), matching the server's own indexing. */
  function reportOutcome(
    transcriptIndex: number,
    stepIndex: number,
    action: "applied" | "declined" | "apply_failed" | "undone",
    ops: { op?: string }[],
  ): void {
    if (!job) return;
    const seq = requestSeq.current;
    void aiJobOutcomeCreate(
      job.id,
      {
        turn_index: transcriptIndex,
        step_index: stepIndex,
        action,
        ops: ops.map((op) => op.op ?? "unknown"),
      },
      headers,
    )
      .then(async () => {
        if (seq !== requestSeq.current) return;
        const current = await aiJobRetrieve(job.id, headers);
        if (seq === requestSeq.current && current.status === 200) setJob(current.data);
      })
      .catch(() => {
        if (seq === requestSeq.current)
          setMessage(
            "No pudimos registrar la decisión en la auditoría. Vuelve a abrir el trabajo para verificarla.",
          );
      });
  }

  function applyOps(turnIndex: number, stepIndex: number, ops: DesignOperation[]): void {
    const turn = thread[turnIndex];
    // The bridge must still close over the exact product the ops were
    // validated against — a commit in between made them stale. In-session
    // turns identity-compare the snapshot; restored turns carry the durable
    // product_sig the server persisted, so a reload doesn't reopen the
    // apply-onto-changed-design hole.
    if (!bridge || !turn) return;
    if (turn.product !== null) {
      if (turn.product !== bridge.product) return;
    } else if (
      turn.productSig !== null &&
      turn.productSig !== productFingerprint(designAssistProduct(bridge.product as ProductJson))
    ) {
      return;
    }
    try {
      const undo = bridge.apply(ops);
      if (undo) undos.current.set(`${turn.transcriptIndex}:${stepIndex}`, undo);
    } catch {
      reportOutcome(turn.transcriptIndex, stepIndex, "apply_failed", ops);
      setMessage(
        "No pudimos aplicar la propuesta. El diseño puede haber cambiado; vuelve a simularla.",
      );
      return;
    }
    reportOutcome(turn.transcriptIndex, stepIndex, "applied", ops);
    setThread((prev) =>
      prev.map((item, i) =>
        i === turnIndex ? { ...item, appliedOps: new Set(item.appliedOps).add(stepIndex) } : item,
      ),
    );
  }

  function declineOps(turnIndex: number, stepIndex: number, ops: DesignOperation[]): void {
    const turn = thread[turnIndex];
    if (!turn) return;
    reportOutcome(turn.transcriptIndex, stepIndex, "declined", ops);
    setThread((prev) =>
      prev.map((item, i) =>
        i === turnIndex ? { ...item, declinedOps: new Set(item.declinedOps).add(stepIndex) } : item,
      ),
    );
  }

  const removePending = (index: number): void => {
    pendingRef.current = pendingRef.current.filter((_, item) => item !== index);
    setPending(pendingRef.current);
  };

  // Flush queued instructions once the run leaves live states — one at a
  // time, so each pending becomes its own follow-up round on the same job.
  useEffect(() => {
    if (!job || LIVE_STATES.has(job.state)) return;
    const queued = pendingRef.current;
    if (!queued.length) return;
    if (TERMINAL_STATES.has(job.state)) {
      // The job died while instructions waited — say so rather than post
      // them into a terminal-state 409.
      pendingRef.current = [];
      setPending([]);
      setMessage(t("agent.pendingDropped"));
      return;
    }
    const [first, ...rest] = queued;
    if (!first) return;
    pendingRef.current = rest;
    setPending(rest);
    void send(first);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- send is stable
    // enough here: it posts against whatever job the dock is bound to.
  }, [job]);

  const live = job !== null && LIVE_STATES.has(job.state);
  // An encargo on the open window arrives with apply_requested: it lands in
  // the drawing at once (unsaved, undoable), exactly as the «Aplicar» click.
  const autoApplied = useRef(new Set<string>());
  useEffect(() => {
    if (autonomy !== "draft" || !bridge || !job) return;
    const last = thread.length - 1;
    const turn = thread[last];
    if (!turn?.result?.steps) return;
    turn.result.steps.forEach((step, stepIndex) => {
      const coordinate = `${job.id}:${turn.transcriptIndex}:${stepIndex}`;
      if (
        step.kind !== "ops" ||
        !(step as { apply_requested?: boolean }).apply_requested ||
        autoApplied.current.has(coordinate) ||
        turn.appliedOps.has(stepIndex) ||
        turn.declinedOps.has(stepIndex) ||
        (step.simulation != null && (step.simulation as { valid?: boolean }).valid !== true) ||
        (turn.product !== null && turn.product !== bridge.product)
      )
        return;
      const ops = asDesignOps(step);
      if (!ops.length) return;
      autoApplied.current.add(coordinate);
      applyOps(last, stepIndex, ops);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- applyOps is stable per render
  }, [thread, job?.id, autonomy, bridge]);
  // «Omitir todo» continues the delegated chain without asking: the quote
  // step (price + draft PDF) runs through the approval endpoint with the
  // person's session once the round settles. Once per job round.
  const autoContinued = useRef(new Set<string>());
  useEffect(() => {
    if (!job || autonomy !== "draft" || interactionMode !== "work") return;
    if (job.state !== "WAITING_FOR_APPROVAL") return;
    const last = thread.at(-1);
    const steps = last?.result?.steps ?? [];
    const waiting = steps.some(
      (step) =>
        step.kind === "quote_draft" &&
        (step as { apply_requested?: boolean }).apply_requested &&
        !(step as { applied?: unknown }).applied &&
        !(step as { apply_error?: string }).apply_error,
    );
    const key = `${job.id}:${last?.transcriptIndex ?? -1}`;
    if (!waiting || autoContinued.current.has(key)) return;
    autoContinued.current.add(key);
    void approveAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- approveAll is stable per render
  }, [job, thread, autonomy, interactionMode]);
  const approvable =
    job !== null &&
    job.state === "WAITING_FOR_APPROVAL" &&
    (thread.at(-1)?.result?.steps ?? []).some(
      (step) =>
        ["project_ops", "document_layout", "quote_draft"].includes(step.kind) &&
        !(step as { applied?: unknown }).applied &&
        !(step as { apply_error?: string }).apply_error,
    );
  const lastTurn = thread.at(-1);
  const chatProposal =
    lastTurn?.mode === "chat" &&
    (lastTurn.result?.steps ?? []).some((step) =>
      ["ops", "batch_ops", "project_ops", "document_layout", "quote_draft"].includes(step.kind),
    );
  const destinationProject = job ? (job.refs as Record<string, string>)?.project_id : undefined;
  const destinationDiffers =
    !!destinationProject && !!refs.project_id && destinationProject !== refs.project_id;
  const retryable = job !== null && job.state === "FAILED_RETRYABLE";
  const terminal = job !== null && TERMINAL_STATES.has(job.state);
  const liveProgress =
    job?.live && typeof job.live.progress === "number"
      ? Math.min(99, Math.max(0, job.live.progress))
      : null;

  return (
    <>
      <div className="ask-dock__thread" aria-live="polite">
        {earlier.length ? (
          <details className="copilot-earlier">
            <summary>
              {earlier.length} {earlier.length === 1 ? "entrada anterior" : "entradas anteriores"}{" "}
              en esta conversación
            </summary>
            <ol>
              {[...earlier].reverse().map((entry) => (
                <li key={entry.id}>
                  <span className="copilot-earlier__text">
                    {entry.kind === "job" ? entry.goal : entry.question}
                  </span>
                  {entry.kind === "ask" && entry.answer ? (
                    <span className="copilot-earlier__answer">{assistantText(entry.answer)}</span>
                  ) : null}
                  {entry.receipt ? (
                    <span className="copilot-earlier__meta">{entry.receipt.summary}</span>
                  ) : entry.state ? (
                    <span className="copilot-earlier__meta">
                      {entry.state === "CANCELED"
                        ? "Cancelado"
                        : entry.state === "FAILED" || entry.state === "FAILED_RETRYABLE"
                          ? "Con error"
                          : "Trabajo anterior"}
                    </span>
                  ) : null}
                </li>
              ))}
            </ol>
            {earlierCursor ? (
              <button
                type="button"
                className="ask-dock__meta-link"
                onClick={() => void loadEarlier()}
              >
                Cargar anteriores
              </button>
            ) : null}
          </details>
        ) : null}
        {thread.some((turn) => turn.errorCode) && !retryable && !terminal ? (
          // Earlier failed attempts of a task that later recovered: history,
          // not a live alert.
          <details className="ui-tech">
            <summary>
              {thread.filter((turn) => turn.errorCode).length === 1
                ? "1 intento anterior falló"
                : `${thread.filter((turn) => turn.errorCode).length} intentos anteriores fallaron`}
            </summary>
            <ol>
              {thread
                .filter((turn) => turn.errorCode)
                .map((turn, index) => (
                  <li key={index}>{t(jobErrorKey(turn.errorCode ?? ""))}</li>
                ))}
            </ol>
          </details>
        ) : null}
        {thread.some((turn) => turn.errorCode) && (retryable || terminal) ? (
          <div className="ask-dock__errorTurn">
            <p>
              {thread.filter((turn) => turn.errorCode).length} intentos fallidos ·{" "}
              {t(jobErrorKey(thread.filter((turn) => turn.errorCode).at(-1)?.errorCode ?? ""))}
            </p>
            {retryable ? (
              <button
                type="button"
                className="ask-dock__action"
                disabled={busy}
                onClick={() => void retryJob()}
              >
                Reintentar
              </button>
            ) : null}
            <details className="ui-tech">
              <summary>Detalles técnicos</summary>
              <ol>
                {thread
                  .filter((turn) => turn.errorCode)
                  .map((turn, index) => (
                    <li key={index}>
                      {turn.goal}
                      <code>{turn.errorCode}</code>
                    </li>
                  ))}
              </ol>
            </details>
          </div>
        ) : null}
        {thread.length === 0 && !live ? (
          <div className="ask-dock__welcome">
            <Companion state={presenceState(job)} size={96} />
            <p className="ask-dock__hint">{t("agent.hint")}</p>
          </div>
        ) : (
          thread
            .filter((turn) => turn.errorCode === null)
            .map((turn) => {
              const turnIndex = thread.indexOf(turn);
              return (
                <div key={turnIndex} className="ask-dock__turn">
                  {turn.goal ? (
                    <p className="ask-dock__question">
                      {turn.goal}
                      {turn.replay ? (
                        <span className="ask-dock__replay">{t("aiws.replayed")}</span>
                      ) : null}
                    </p>
                  ) : null}
                  {turn.attachments?.length ? (
                    <SentAttachments organizationId={organizationId} items={turn.attachments} />
                  ) : null}
                  {turn.result === null ? null : (
                    <>
                      {turn.result.queries?.length ? (
                        <details className="ui-tech">
                          <summary>Fuentes consultadas</summary>
                          <ul className="ask-dock__queries">
                            {turn.result.queries.map((query, i) => (
                              <li key={i}>
                                {query.status === "ok"
                                  ? t("agent.queried").replace(
                                      "{surface}",
                                      SURFACE_LABELS[query.surface ?? ""] ?? "datos del trabajo",
                                    )
                                  : t("agent.queryFailed").replace(
                                      "{surface}",
                                      SURFACE_LABELS[query.surface ?? ""] ?? "datos del trabajo",
                                    )}
                              </li>
                            ))}
                          </ul>
                        </details>
                      ) : null}
                      {turn.result.reply &&
                      !turn.result.steps?.some((step) =>
                        ["ops", "batch_ops", "project_ops", "prepare", "document_layout"].includes(
                          step.kind,
                        ),
                      ) ? (
                        <p className="ask-dock__answer">{assistantText(turn.result.reply)}</p>
                      ) : null}
                      {turn.result.questions?.some(
                        (question) => question !== turn.result?.clarify?.question,
                      ) ? (
                        <div className="ask-dock__questions">
                          {turn.result.questions
                            .filter((question) => question !== turn.result?.clarify?.question)
                            .map((question, i) => (
                              <p key={i}>{question}</p>
                            ))}
                        </div>
                      ) : null}
                      {turn.result.clarify ? (
                        <div className="ask-dock__questions" aria-label="Aclaración del trabajo">
                          <p>{turn.result.clarify.question}</p>
                          <div className="ask-dock__chips">
                            {turn.result.clarify.options.map((option) => (
                              <button
                                type="button"
                                className="ask-dock__chip"
                                key={option.value}
                                disabled={busy || turnIndex !== thread.length - 1}
                                onClick={() => void send(option.value)}
                              >
                                {option.label}
                              </button>
                            ))}
                          </div>
                        </div>
                      ) : null}
                      {turn.result.warnings?.length ? (
                        <details className="ui-tech">
                          <summary>Restricciones de la propuesta</summary>
                          <ul className="ask-dock__warnings">
                            {turn.result.warnings.map((warning, i) => (
                              <li key={i}>{assistantText(warning)}</li>
                            ))}
                          </ul>
                        </details>
                      ) : null}
                      {turn.result.rejected?.length ? (
                        <RejectedOperations items={turn.result.rejected} />
                      ) : null}
                      {turn.result.steps?.length ? (
                        <div className="ask-dock__actions">
                          {turn.result.steps.map((step, stepIndex) => {
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
                            if (step.kind === "batch_ops" && refs.project_id && job) {
                              const applied = turn.appliedOps.has(stepIndex);
                              return (
                                <BatchOpsStep
                                  key={stepIndex}
                                  step={step}
                                  organizationId={organizationId}
                                  projectId={refs.project_id}
                                  settled={applied}
                                  operationKey={`ai:${job.id}:${turn.transcriptIndex}:${stepIndex}`}
                                  declined={(job.outcomes ?? []).some((value) => {
                                    const outcome = value as {
                                      turn_index?: number;
                                      step_index?: number;
                                      action?: string;
                                    };
                                    return (
                                      outcome.turn_index === turn.transcriptIndex &&
                                      outcome.step_index === stepIndex &&
                                      outcome.action === "declined"
                                    );
                                  })}
                                  onSettled={(action, ops) => {
                                    reportOutcome(turn.transcriptIndex, stepIndex, action, ops);
                                    setThread((prev) =>
                                      prev.map((item, i) =>
                                        i === turnIndex
                                          ? {
                                              ...item,
                                              appliedOps: new Set(item.appliedOps).add(stepIndex),
                                            }
                                          : item,
                                      ),
                                    );
                                  }}
                                />
                              );
                            }
                            const stepProject =
                              (step.simulation as { project_id?: string } | undefined)
                                ?.project_id ?? refs.project_id;
                            if (step.kind === "project_ops" && stepProject && job) {
                              return (
                                <ProjectOpsStep
                                  key={stepIndex}
                                  step={step}
                                  organizationId={organizationId}
                                  projectId={stepProject}
                                  linkToProject={stepProject !== refs.project_id}
                                  operationKey={`ai:${job.id}:${turn.transcriptIndex}:${stepIndex}`}
                                  declined={(job.outcomes ?? []).some((value) => {
                                    const outcome = value as {
                                      turn_index?: number;
                                      step_index?: number;
                                      action?: string;
                                    };
                                    return (
                                      outcome.turn_index === turn.transcriptIndex &&
                                      outcome.step_index === stepIndex &&
                                      outcome.action === "declined"
                                    );
                                  })}
                                  onSettled={(action, ops) =>
                                    reportOutcome(turn.transcriptIndex, stepIndex, action, ops)
                                  }
                                />
                              );
                            }
                            if (step.kind === "document_layout" && job) {
                              return (
                                <DocumentLayoutStep
                                  key={stepIndex}
                                  step={step}
                                  organizationId={organizationId}
                                  declined={(job.outcomes ?? []).some((value) => {
                                    const outcome = value as {
                                      turn_index?: number;
                                      step_index?: number;
                                      action?: string;
                                    };
                                    return (
                                      outcome.turn_index === turn.transcriptIndex &&
                                      outcome.step_index === stepIndex &&
                                      outcome.action === "declined"
                                    );
                                  })}
                                  onSettled={(action) =>
                                    reportOutcome(turn.transcriptIndex, stepIndex, action, [
                                      { op: "document_layout" },
                                    ])
                                  }
                                />
                              );
                            }
                            if (step.kind === "ops") {
                              const ops = asDesignOps(step);
                              if (!ops.length) return null;
                              const coordinate = `${turn.transcriptIndex}:${stepIndex}`;
                              const wasUndone =
                                undone.has(coordinate) ||
                                (job?.outcomes ?? []).some((value) => {
                                  const outcome = value as {
                                    turn_index?: number;
                                    step_index?: number;
                                    action?: string;
                                  };
                                  return (
                                    outcome.turn_index === turn.transcriptIndex &&
                                    outcome.step_index === stepIndex &&
                                    outcome.action === "undone"
                                  );
                                });
                              const applied =
                                turn.appliedOps.has(stepIndex) ||
                                (job?.outcomes ?? []).some((value) => {
                                  const outcome = value as {
                                    turn_index?: number;
                                    step_index?: number;
                                    action?: string;
                                  };
                                  return (
                                    outcome.turn_index === turn.transcriptIndex &&
                                    outcome.step_index === stepIndex &&
                                    outcome.action === "applied"
                                  );
                                });
                              const declined = turn.declinedOps.has(stepIndex);
                              const stale =
                                !bridge ||
                                (turn.product !== null
                                  ? turn.product !== bridge.product
                                  : turn.productSig !== null &&
                                    turn.productSig !== productFingerprint(bridge.product));
                              return (
                                <div key={stepIndex} className="ask-dock__ops">
                                  {!step.simulation ? (
                                    <ul>
                                      {ops.map((op, i) => (
                                        <li key={i}>
                                          {turn.product
                                            ? describeDesignOp(
                                                op,
                                                turn.product as ProductJson,
                                                ops.slice(0, i),
                                              )
                                            : typeof op.description === "string"
                                              ? op.description
                                              : "Cambio de diseño"}
                                        </li>
                                      ))}
                                    </ul>
                                  ) : null}
                                  <p className="operation-state">
                                    <Companion
                                      state={
                                        wasUndone
                                          ? "canceled"
                                          : applied
                                            ? "success"
                                            : declined
                                              ? "canceled"
                                              : "approval"
                                      }
                                      size={20}
                                    />{" "}
                                    {wasUndone
                                      ? "Cambios deshechos"
                                      : applied
                                        ? "Cambios aplicados en el editor · guarda la posición"
                                        : declined
                                          ? "Propuesta descartada"
                                          : "Propuesta preparada · revisa antes de aplicar"}
                                  </p>
                                  <SimulationPreview
                                    simulation={step.simulation}
                                    organizationId={organizationId}
                                  />
                                  {job ? (
                                    <button
                                      type="button"
                                      className="ask-dock__action ask-dock__action--ghost"
                                      onClick={() => navigate(`/assistant?job=${job.id}&audit=1`)}
                                    >
                                      Ver auditoría
                                    </button>
                                  ) : null}
                                  <div className="ask-dock__ops-actions">
                                    <button
                                      type="button"
                                      className="ask-dock__action"
                                      disabled={
                                        applied ||
                                        declined ||
                                        stale ||
                                        !bridge ||
                                        (step.simulation != null &&
                                          (step.simulation as { valid?: boolean }).valid !== true)
                                      }
                                      title={stale && bridge ? t("assistant.stale") : undefined}
                                      onClick={() => applyOps(turnIndex, stepIndex, ops)}
                                    >
                                      {applied
                                        ? t("agent.applied")
                                        : t("assistant.apply").replace(
                                            "{count}",
                                            String(ops.length),
                                          )}
                                    </button>
                                    {applied && !wasUndone && undos.current.has(coordinate) ? (
                                      <button
                                        type="button"
                                        className="ask-dock__action"
                                        onClick={() => {
                                          if (!undos.current.get(coordinate)?.()) {
                                            setMessage(
                                              "El diseño cambió después de esta propuesta. Usa el historial del editor para revisar los cambios; no deshicimos tus ediciones.",
                                            );
                                            return;
                                          }
                                          setUndone((previous) =>
                                            new Set(previous).add(coordinate),
                                          );
                                          reportOutcome(
                                            turn.transcriptIndex,
                                            stepIndex,
                                            "undone",
                                            ops,
                                          );
                                        }}
                                      >
                                        Deshacer cambios
                                      </button>
                                    ) : null}
                                    {!applied ? (
                                      <button
                                        type="button"
                                        className="ask-dock__action ask-dock__action--ghost"
                                        disabled={declined}
                                        onClick={() => declineOps(turnIndex, stepIndex, ops)}
                                      >
                                        {declined ? t("agent.declined") : t("agent.decline")}
                                      </button>
                                    ) : null}
                                  </div>
                                </div>
                              );
                            }
                            return null;
                          })}
                        </div>
                      ) : null}
                      {turn.result.artifacts?.length ? (
                        <div className="ask-dock__artifacts">
                          {turn.result.artifacts.map((item, i) => {
                            const artifact = item as { kind?: string; title?: string };
                            // Deep-link by transcript coordinates (turn:item) — the
                            // flat shelf truncates to the newest entries, so a
                            // shelf index would drift to the wrong artifact.
                            const artRef = `${turn.transcriptIndex}:${i}`;
                            return (
                              <button
                                key={i}
                                type="button"
                                className="ask-dock__artifact"
                                title={t("aiws.openWorkspace")}
                                onClick={() =>
                                  job
                                    ? navigate(`/assistant?job=${job.id}&art=${artRef}`)
                                    : undefined
                                }
                              >
                                {artifact.title ?? artifact.kind ?? t("aiws.inspector")}
                              </button>
                            );
                          })}
                        </div>
                      ) : null}
                    </>
                  )}
                  {turnIndex === thread.length - 1 && job?.receipt && !live ? (
                    <Receipt receipt={job.receipt} onOpen={(path) => navigate(path)} />
                  ) : null}
                  {turnIndex === thread.length - 1 && approvable && !live ? (
                    <div className="copilot-approve">
                      <p>
                        {autonomy === "draft"
                          ? "Quedan cambios por aplicar."
                          : "El conjunto está preparado. Revísalo y apruébalo una vez."}
                      </p>
                      <button
                        type="button"
                        className="ui-button ui-button--primary ui-button--compact"
                        disabled={busy}
                        onClick={() => void approveAll()}
                      >
                        Aprobar y aplicar
                      </button>
                    </div>
                  ) : null}
                  {turnIndex === thread.length - 1 && chatProposal && !live ? (
                    <div className="copilot-approve">
                      <p>En Chat nada se aplica. Puedes pasar este encargo a Trabajo.</p>
                      <button
                        type="button"
                        className="ui-button ui-button--secondary ui-button--compact"
                        disabled={busy}
                        onClick={() => {
                          onInteractionMode?.("work");
                          void send(turn.goal, "work");
                        }}
                      >
                        Hacer en Trabajo
                      </button>
                    </div>
                  ) : null}
                  {turnIndex === thread.length - 1 && job ? (
                    <p className="ask-dock__meta">
                      <button
                        type="button"
                        className="ask-dock__meta-link"
                        onClick={() => navigate(`/assistant?job=${job.id}`)}
                      >
                        {t("aiws.openWorkspace")}
                      </button>
                      {" · "}
                      <button type="button" className="ask-dock__meta-link" onClick={startFresh}>
                        Nuevo encargo
                      </button>
                    </p>
                  ) : null}
                </div>
              );
            })
        )}
        {live && job ? (
          <p className="ask-dock__busy">
            {liveProgress !== null ? `${liveProgress}% · ` : ""}
            {typeof job.live?.phase === "string" && AI_PHASES[job.live.phase]
              ? AI_PHASES[job.live.phase]
              : STATE_LABEL[job.state]
                ? t(STATE_LABEL[job.state] as Parameters<typeof t>[0])
                : t("agent.thinking")}
            {" · "}
            <button type="button" className="ask-dock__meta-link" onClick={() => void cancelJob()}>
              {t("aiws.cancel")}
            </button>
          </p>
        ) : null}
      </div>
      {offline ? (
        <p className="ask-dock__offline" role="status">
          {t("agent.offline")}
        </p>
      ) : null}
      {message ? <p className="ask-dock__error">{message}</p> : null}
      {terminal ? (
        <p className="ask-dock__error">
          {job?.state === "CANCELED" ? t("agent.canceled") : t("agent.error")}
          {" · "}
          <button type="button" className="ask-dock__meta-link" onClick={startFresh}>
            {t("aiws.new")}
          </button>
        </p>
      ) : null}
      {destinationDiffers && !live ? (
        <p className="copilot-destination">
          Este encargo sigue trabajando sobre su obra original.{" "}
          <button type="button" className="ask-dock__meta-link" onClick={startFresh}>
            Nuevo encargo para la obra abierta
          </button>
        </p>
      ) : null}
      {pending.length > 0 ? (
        <ul className="ask-dock__pending" aria-label={t("agent.pending")}>
          {pending.map((item, index) => (
            <li key={`${index}-${item.slice(0, 16)}`}>
              <span>
                {t("agent.pending")} {item}
              </span>
              <button
                type="button"
                aria-label={t("agent.pendingRemove")}
                onClick={() => removePending(index)}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      {!terminal ? (
        <ValidatedForm
          className="ask-dock__form"
          onSubmit={(event) => {
            event.preventDefault();
            run().catch(() => undefined);
          }}
        >
          {contextLabel ? (
            <p className="copilot-context">
              <span>Leyendo: {contextLabel}</span>
              {onClearContext ? (
                <button
                  type="button"
                  className="ui-icon-button copilot__icon"
                  aria-label="Quitar el contexto de lectura"
                  onClick={onClearContext}
                >
                  <Icon name="close" size={16} />
                </button>
              ) : null}
            </p>
          ) : null}
          <AttachmentTray
            organizationId={organizationId}
            threadId={threadId}
            items={attachments}
            onChange={setAttachments}
          />
          <textarea
            ref={inputRef}
            value={goal}
            maxLength={2000}
            rows={2}
            placeholder={t("agent.placeholder")}
            aria-label={t("agent.placeholder")}
            onChange={(event) => setGoal(event.target.value)}
            onKeyDown={(event) => {
              // IME composition owns Enter until it commits.
              if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
                event.preventDefault();
                run().catch(() => undefined);
              }
            }}
            disabled={busy && !live}
          />
          <div className="ask-dock__compose-row">
            <span className="copilot-mode-hint">
              {interactionMode === "chat"
                ? "Chat responde y propone; no cambia tus datos."
                : autonomy === "propose"
                  ? "Solo proponer: nada se aplica."
                  : autonomy === "approve"
                    ? "Con aprobación: preparo el conjunto y lo apruebas una vez."
                    : "Omitir todo: aplico lo reversible y te muestro el recibo."}
            </span>
            <button
              type="submit"
              className="ui-button ui-button--primary ui-button--compact"
              disabled={(busy && !live) || !goal.trim()}
            >
              <Icon name="send" size={16} />
              {interactionMode === "chat" ? "Enviar" : "Encargar"}
            </button>
          </div>
        </ValidatedForm>
      ) : null}
    </>
  );
}
