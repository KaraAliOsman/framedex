import { useEffect, useRef, useState } from "react";

import { ApiError } from "../../api/apiMutator";
import { positionsDesignAlternatives } from "../../api/generated/dekopen";
import type { DesignAlternativesResponse } from "../../api/generated/models/designAlternativesResponse";
import { t } from "../../i18n/es-CL";
import type { MemberGeometry } from "./members";
import { elevationEnvelopeMm, isProductModel, type ProductJson } from "./productEditing";
import { ProductFrontSvg } from "./ProductFrontSvg";

type Alternative = {
  label: string;
  rationale: string | null;
  product: ProductJson;
  metrics: Record<string, unknown>;
};

type Result = {
  alternatives: Alternative[];
  rejected: { label: string | null; reasons: string[] }[];
  notes: string | null;
  model: string;
  credits: number;
  systemId: string | null;
};

const NO_ISSUES: never[] = [];
const NOOP = () => undefined;

function metric(metrics: Record<string, unknown>, key: string): string | null {
  const value = metrics[key];
  if (typeof value === "string" || typeof value === "number") return String(value);
  return null;
}

/** Generative alternatives: a brief becomes several candidate products the
 * estimator compares side by side. The backend builds and engine-validates
 * every spec — cards only ever show candidates the engine could evaluate,
 * and "Usar" commits the returned product-v2 as a normal undoable edit. */
export function AlternativesPanel({
  organizationId,
  positionId,
  systemId,
  product,
  members,
  disabled,
  onUse,
}: {
  organizationId: string;
  positionId: string | null;
  systemId: string | null;
  product: ProductJson | null;
  members: MemberGeometry;
  disabled: boolean;
  onUse(next: ProductJson): void;
}): JSX.Element {
  const [brief, setBrief] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [result, setResult] = useState<Result | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(true);
  const requestSeq = useRef(0);
  /** One operation key per (brief, system): a retry after a lost response
   * replays the committed call instead of debiting twice. */
  const operationKey = useRef<{
    key: string;
    brief: string;
    systemId: string | null;
    dims: string;
  } | null>(null);

  /** A system switch invalidates anything in flight — candidates were
   * built and validated against the request's catalog. */
  useEffect(() => {
    requestSeq.current += 1;
    setResult(null);
    setBusy(false);
  }, [systemId]);

  async function generate(): Promise<void> {
    if (!positionId || !systemId || !brief.trim() || product === null) return;
    setBusy(true);
    setMessage("");
    setResult(null);
    const trimmed = brief.trim();
    // Candidates are built at the dimensions the estimator currently sees —
    // the live product, not the persisted row — so adopting one can't
    // silently discard unsaved resize edits. Dimensions also key the
    // operation: identical requests replay, changed ones are new audits.
    const envelope = elevationEnvelopeMm(product);
    const dims = `${envelope.width.toFixed(2)}x${envelope.height.toFixed(2)}`;
    if (
      !operationKey.current ||
      operationKey.current.brief !== trimmed ||
      operationKey.current.systemId !== systemId ||
      operationKey.current.dims !== dims
    ) {
      operationKey.current = { key: crypto.randomUUID(), brief: trimmed, systemId, dims };
    }
    const seq = ++requestSeq.current;
    try {
      const response = await positionsDesignAlternatives(
        positionId,
        {
          brief: trimmed,
          count: 3,
          system_id: systemId,
          operation_key: operationKey.current.key,
          width_mm: envelope.width.toFixed(2),
          height_mm: envelope.height.toFixed(2),
        },
        { headers: { "X-Organization-ID": organizationId } },
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      if (seq !== requestSeq.current) return;
      const data = response.data as DesignAlternativesResponse;
      const alternatives: Alternative[] = data.alternatives
        .map((item) => {
          const candidate = item["product"];
          if (!isProductModel(candidate)) return null;
          return {
            label: typeof item["label"] === "string" ? item["label"] : t("alternatives.fallback"),
            rationale: typeof item["rationale"] === "string" ? (item["rationale"] as string) : null,
            product: candidate,
            metrics: (item["metrics"] ?? {}) as Record<string, unknown>,
          };
        })
        .filter((item): item is Alternative => item !== null);
      setResult({
        alternatives,
        rejected: data.rejected.map((item) => ({
          label: typeof item["label"] === "string" ? (item["label"] as string) : null,
          reasons: Array.isArray(item["reasons"]) ? (item["reasons"] as unknown[]).map(String) : [],
        })),
        notes: data.notes ?? null,
        model: data.model,
        credits: data.credits_debited,
        systemId,
      });
      if (alternatives.length === 0 && data.rejected.length === 0) {
        setMessage(t("alternatives.empty"));
      }
    } catch (error) {
      if (seq !== requestSeq.current) return;
      setMessage(
        error instanceof ApiError && typeof error.payload === "object" && error.payload !== null
          ? String(
              (error.payload as { error?: { detail?: unknown } }).error?.detail ??
                t("alternatives.error"),
            )
          : t("alternatives.error"),
      );
    } finally {
      if (seq === requestSeq.current) setBusy(false);
    }
  }

  return (
    <details
      className="inspector-section alternatives-panel"
      open={detailsOpen}
      onToggle={(event) => setDetailsOpen(event.currentTarget.open)}
    >
      <summary>{t("alternatives.title")}</summary>
      {!positionId ? (
        <p className="assembly-hint">{t("alternatives.saveFirst")}</p>
      ) : (
        <>
          <textarea
            className="assistant-panel__prompt"
            rows={2}
            placeholder={t("alternatives.brief")}
            value={brief}
            disabled={busy || disabled}
            onChange={(event) => setBrief(event.target.value)}
          />
          <div className="inspector-actions">
            <button
              type="button"
              className="primary-button"
              disabled={busy || disabled || !systemId || !brief.trim()}
              onClick={() => void generate()}
            >
              {busy ? t("alternatives.generating") : t("alternatives.generate")}
            </button>
          </div>
          {message && <p className="assembly-hint">{message}</p>}
          {result && result.systemId === systemId && (
            <div className="alternatives-panel__result">
              {result.notes && <p className="assistant-panel__notes">{result.notes}</p>}
              {result.alternatives.length > 0 && (
                <div className="alternatives-panel__cards">
                  {result.alternatives.map((item, index) => {
                    const status = metric(item.metrics, "status");
                    const warnings = Array.isArray(item.metrics["warnings"])
                      ? (item.metrics["warnings"] as unknown[])
                      : [];
                    return (
                      <div key={`alt-${index}`} className="alternative-card">
                        <span className="alternative-card__thumb">
                          <ProductFrontSvg
                            product={item.product}
                            members={members}
                            selectedId={null}
                            issues={NO_ISSUES}
                            disabled
                            preview
                            onSelectModule={NOOP}
                            onAddUnit={NOOP}
                            onCommitModuleWidth={NOOP}
                            onCommitTotalWidth={NOOP}
                            onCommitHeight={NOOP}
                          />
                        </span>
                        <p className="alternative-card__label">{item.label}</p>
                        {item.rationale && (
                          <p className="alternative-card__rationale">{item.rationale}</p>
                        )}
                        <p className="alternative-card__metrics">
                          {[
                            metric(item.metrics, "module_count") &&
                              t("alternatives.metricModules").replace(
                                "{count}",
                                metric(item.metrics, "module_count") ?? "",
                              ),
                            metric(item.metrics, "glass_area_m2") &&
                              `${metric(item.metrics, "glass_area_m2")} m²`,
                            metric(item.metrics, "total_weight_kg") &&
                              `${metric(item.metrics, "total_weight_kg")} kg`,
                          ]
                            .filter(Boolean)
                            .join(" · ")}
                        </p>
                        {status && status !== "VALID" && (
                          <p className="alternative-card__warnings" title={warnings.join(", ")}>
                            {t("alternatives.incomplete")}
                          </p>
                        )}
                        <button
                          type="button"
                          className="primary-button alternative-card__use"
                          disabled={disabled || busy}
                          onClick={() => {
                            onUse(item.product);
                            setResult(null);
                            setBrief("");
                          }}
                        >
                          {t("alternatives.use")}
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
              {result.rejected.length > 0 && (
                <ul className="assistant-panel__rejected">
                  {result.rejected.map((item, index) => (
                    <li key={`rejected-${index}`}>
                      {item.label ?? "?"}: {item.reasons.join(", ")}
                    </li>
                  ))}
                </ul>
              )}
              <p className="assistant-panel__meta">
                {result.model} · {result.credits} {t("assistant.credits")}
              </p>
            </div>
          )}
        </>
      )}
    </details>
  );
}
