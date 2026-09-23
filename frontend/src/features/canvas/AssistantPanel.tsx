import { useState } from "react";

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
};

/** NL design assistant: prompt → gateway-validated op preview → one commit.
 * Every apply is a single undoable product mutation; rejected ops are listed
 * so a bad proposal can never silently pass for a real edit. */
export function AssistantPanel({
  organizationId,
  positionId,
  product,
  disabled,
  onApply,
}: {
  organizationId: string;
  positionId: string | null;
  product: ProductJson;
  disabled: boolean;
  onApply(ops: DesignOp[]): void;
}): JSX.Element {
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [preview, setPreview] = useState<Preview | null>(null);

  async function generate(): Promise<void> {
    if (!positionId || !prompt.trim()) return;
    setBusy(true);
    setMessage("");
    setPreview(null);
    try {
      const response = await positionsDesignAssist(
        positionId,
        {
          prompt: prompt.trim(),
          operation_key: crypto.randomUUID(),
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
      const data = response.data as DesignAssistResponse;
      setPreview({
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
      setMessage(
        error instanceof ApiError && typeof error.payload === "object" && error.payload !== null
          ? String(
              (error.payload as { error?: { detail?: unknown } }).error?.detail ??
                t("assistant.error"),
            )
          : t("assistant.error"),
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <details className="inspector-section assistant-panel" open>
      <summary>{t("assistant.title")}</summary>
      {!positionId ? (
        <p className="assembly-hint">{t("assistant.saveFirst")}</p>
      ) : (
        <>
          <textarea
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
              disabled={busy || disabled || !prompt.trim()}
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
                    <li key={`op-${index}`}>{describeDesignOp(op)}</li>
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
