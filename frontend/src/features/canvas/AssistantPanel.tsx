import { useEffect, useRef, useState } from "react";

import { ApiError } from "../../api/apiMutator";
import { positionsDesignAssist } from "../../api/generated/dekopen";
import type { DesignAssistResponse } from "../../api/generated/models/designAssistResponse";
import { t, type TranslationKey } from "../../i18n/es-CL";
import { describeDesignOp, type DesignOp } from "./designOps";
import type { ProductJson } from "./productEditing";

type Preview = {
  ops: DesignOp[];
  rejected: { op: string | null; reason: string }[];
  notes: string | null;
  model: string;
  credits: number;
  /** The product instance the ops were validated against — any later commit
   * produces a new identity and makes the index-based ops stale. */
  snapshot: ProductJson;
};

/** NL design assistant: prompt → gateway-validated op preview → one commit.
 * Every apply is a single undoable product mutation; rejected ops are listed
 * so a bad proposal can never silently pass for a real edit. */
export function AssistantPanel({
  organizationId,
  positionId,
  systemId,
  product,
  disabled,
  draft,
  onDraftHandled,
  onApply,
}: {
  organizationId: string;
  positionId: string | null;
  systemId: string | null;
  product: ProductJson;
  disabled: boolean;
  /** A queued prompt from an external affordance ("Fix with DEKOPEN",
   * context menus): "" focuses the field, text replaces the draft. The
   * human always confirms — nothing here calls the provider on its own. */
  draft: string | null;
  onDraftHandled(): void;
  onApply(ops: DesignOp[]): void;
}): JSX.Element {
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [preview, setPreview] = useState<Preview | null>(null);
  const promptRef = useRef<HTMLTextAreaElement>(null);
  const [detailsOpen, setDetailsOpen] = useState(true);
  /** Request generation token — a handled draft (or product change) must
   * invalidate any in-flight generate so its response can't restore ops
   * under a different prompt. */
  const requestSeq = useRef(0);

  useEffect(() => {
    if (draft === null) return;
    requestSeq.current += 1;
    setBusy(false);
    if (draft) setPrompt(draft);
    setMessage("");
    setPreview(null);
    setDetailsOpen(true);
    // Focus after the (possibly closed) details re-renders open.
    requestAnimationFrame(() => promptRef.current?.focus());
    onDraftHandled();
  }, [draft, onDraftHandled]);
  /** One operation key per (prompt, product, system) — a retry after a lost
   * response replays the committed call instead of debiting twice. */
  const operationKey = useRef<{
    key: string;
    prompt: string;
    product: ProductJson;
    systemId: string | null;
  } | null>(null);

  async function generate(): Promise<void> {
    if (!positionId || !systemId || !prompt.trim()) return;
    setBusy(true);
    setMessage("");
    setPreview(null);
    const trimmed = prompt.trim();
    if (
      !operationKey.current ||
      operationKey.current.prompt !== trimmed ||
      operationKey.current.product !== product ||
      operationKey.current.systemId !== systemId
    ) {
      operationKey.current = {
        key: crypto.randomUUID(),
        prompt: trimmed,
        product,
        systemId,
      };
    }
    const seq = ++requestSeq.current;
    try {
      const response = await positionsDesignAssist(
        positionId,
        {
          prompt: trimmed,
          operation_key: operationKey.current.key,
          system_id: systemId,
          product: {
            modules: product.assembly.modules.map((module) => ({
              width_mm: module.width_mm,
              height_mm: module.height_mm,
            })),
            couplings: product.assembly.couplings.map((coupling) => ({
              angle_deg: coupling.angle_deg,
            })),
          },
        },
        { headers: { "X-Organization-ID": organizationId } },
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      // A newer draft (or request) superseded this call — its ops must never
      // surface under a different prompt.
      if (seq !== requestSeq.current) return;
      const data = response.data as DesignAssistResponse;
      setPreview({
        snapshot: product,
        ops: data.ops as DesignOp[],
        rejected: data.rejected.map((item) => ({
          op: typeof item.op === "string" ? item.op : null,
          reason: typeof item.reason === "string" ? item.reason : "formato_invalido",
        })),
        notes: data.notes,
        model: data.model,
        credits: data.credits_debited,
      });
      if (data.ops.length === 0 && data.rejected.length === 0) {
        setMessage(t("assistant.empty"));
      }
    } catch (error) {
      if (seq !== requestSeq.current) return;
      setMessage(
        error instanceof ApiError && typeof error.payload === "object" && error.payload !== null
          ? String(
              (error.payload as { error?: { detail?: unknown } }).error?.detail ??
                t("assistant.error"),
            )
          : t("assistant.error"),
      );
    } finally {
      // Only the newest request clears busy — a superseded response must not
      // unlock the panel while a newer generate is still in flight.
      if (seq === requestSeq.current) setBusy(false);
    }
  }

  return (
    <details
      className="inspector-section assistant-panel"
      open={detailsOpen}
      onToggle={(event) => setDetailsOpen(event.currentTarget.open)}
    >
      <summary>{t("assistant.title")}</summary>
      {!positionId ? (
        <p className="assembly-hint">{t("assistant.saveFirst")}</p>
      ) : (
        <>
          <textarea
            ref={promptRef}
            className="assistant-panel__prompt"
            rows={2}
            placeholder={t("assistant.prompt")}
            value={prompt}
            disabled={busy || disabled}
            onChange={(event) => setPrompt(event.target.value)}
          />
          <div className="inspector-actions">
            <button
              type="button"
              className="primary-button"
              disabled={busy || disabled || !systemId || !prompt.trim()}
              onClick={() => void generate()}
            >
              {busy ? t("assistant.generating") : t("assistant.generate")}
            </button>
          </div>
          {message && <p className="assembly-hint">{message}</p>}
          {preview && (
            <div className="assistant-panel__preview">
              {preview.notes && <p className="assistant-panel__notes">{preview.notes}</p>}
              {preview.ops.length > 0 && (
                <ul className="assistant-panel__ops">
                  {preview.ops.map((op, index) => (
                    <li key={`op-${index}`}>{describeDesignOp(op, preview.snapshot)}</li>
                  ))}
                </ul>
              )}
              {preview.rejected.length > 0 && (
                <ul className="assistant-panel__rejected">
                  {preview.rejected.map((item, index) => (
                    <li key={`rejected-${index}`}>
                      {item.op ?? "?"}: {t(`assistant.reason_${item.reason}` as TranslationKey)}
                    </li>
                  ))}
                </ul>
              )}
              {preview.snapshot !== product ? (
                <p className="assembly-hint">{t("assistant.stale")}</p>
              ) : (
                <div className="inspector-actions">
                  <button
                    type="button"
                    className="primary-button"
                    disabled={preview.ops.length === 0 || disabled}
                    onClick={() => {
                      onApply(preview.ops);
                      setPreview(null);
                      setPrompt("");
                    }}
                  >
                    {t("assistant.apply").replace("{count}", String(preview.ops.length))}
                  </button>
                </div>
              )}
              <p className="assistant-panel__meta">
                {preview.model} · {preview.credits} {t("assistant.credits")}
              </p>
            </div>
          )}
        </>
      )}
    </details>
  );
}
