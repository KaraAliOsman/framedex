import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { measurementRectify, mountingRules } from "../../api/generated/dekopen";
import type {
  PositionResponse,
  ProjectResponse,
  RectificationResponse,
} from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { formatMoney, formatRevision } from "../../format";
import { actionErrorDetail } from "../errors";
import { PositionThumb } from "./PositionThumb";
import { MountingChip } from "./MeasurementPanel";
import { SurveyFields, normalizedSurvey, SurveyInputError } from "./MountingInspector";
import {
  type MeasurementRecord,
  type MountingEvidence,
  type OpeningSurvey,
  type PriceChange,
  type RuleRecord,
} from "./mountingModel";

export function RectificationPanel({
  position,
  project,
  orgId,
  onSaved,
}: {
  position: PositionResponse;
  project: ProjectResponse;
  orgId: string;
  onSaved(): void;
}) {
  const role = useAuthSession().me?.active_organization?.role;
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<OpeningSurvey[] | null>(null),
    [reason, setReason] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [proposal, setProposal] = useState<RectificationResponse | null>(null);
  const query = useQuery({
    queryKey: ["mounting-rules", orgId, position.design.system_id],
    enabled: open && (role === "OWNER" || role === "ESTIMATOR"),
    queryFn: async () => {
      const r = await mountingRules(position.design.system_id, {
        headers: { "X-Organization-ID": orgId },
      });
      if (r.status !== 200) throw new ApiError(r.status, r.data);
      return r.data.items as RuleRecord[];
    },
  });
  if (role !== "OWNER" && role !== "ESTIMATOR")
    return <p>El estimador o dueño registra la rectificación y revisa su precio.</p>;
  const record = position.measurements as MeasurementRecord | null | undefined;
  const value =
    draft ??
    record?.measurements.map((item) => ({ ...item.survey, origin: "SITE" as const })) ??
    [];
  const tree = position.design.parametric_tree as Record<string, unknown>;
  const targets =
    tree.version === "product-v2"
      ? (tree.assembly as { modules: { id: string }[] }).modules.map((m) => m.id)
      : [null];
  const edit = (next: OpeningSurvey[]) => {
    setDraft(next);
    setProposal(null);
    setError("");
  };
  async function calculate(apply = false) {
    setBusy(true);
    setError("");
    try {
      const r = await measurementRectify(
        position.id,
        {
          design: position.design,
          measurements: value.map(normalizedSurvey),
          expected_updated_at: position.updated_at,
          expected_current_revision: project.current_revision,
          reason,
          confirmed: apply,
          ...(apply && proposal ? { proposal_token: proposal.proposal_token } : {}),
        },
        { headers: { "X-Organization-ID": orgId } },
      );
      if (r.status !== 200) throw new ApiError(r.status, r.data);
      if (apply) {
        setDraft(null);
        setProposal(null);
        onSaved();
      } else setProposal(r.data);
    } catch (cause) {
      setError(
        cause instanceof SurveyInputError
          ? cause.message
          : actionErrorDetail(cause, "No pudimos rectificar. Revisa las medidas y los precios."),
      );
    } finally {
      setBusy(false);
    }
  }
  const price = proposal?.price_change as PriceChange | undefined;
  return (
    <details
      className="rectification-panel"
      onToggle={(event) => setOpen(event.currentTarget.open)}
    >
      <summary>Rectificar medidas en obra</summary>
      <p>
        Revisa el cambio de fabricación y venta antes de aplicar. Una cotización emitida abre una
        revisión para nueva aprobación.
      </p>
      {query.isPending ? (
        <p role="status">Cargando montajes…</p>
      ) : query.isError ? (
        <p role="alert">
          No pudimos cargar los montajes.{" "}
          <button onClick={() => void query.refetch()}>Reintentar</button>
        </p>
      ) : (query.data?.length ?? 0) === 0 ? (
        <p>Sin dato: el dueño o encargado debe declarar el montaje en Ajustes.</p>
      ) : (
        <fieldset disabled={busy}>
          {targets.map((target, index) => {
            const survey = value.find((s) => s.module_id === target);
            return (
              <section key={target ?? "single"}>
                <h4>Marco {index + 1}</h4>
                <label>
                  Montaje
                  <select
                    value={survey?.rule_code ?? ""}
                    onChange={(e) => {
                      const choice = query.data!.find((item) => item.rule.code === e.target.value);
                      if (!choice) return;
                      edit([
                        ...value.filter((item) => item.module_id !== target),
                        {
                          module_id: target,
                          rule_code: choice.rule.code,
                          rule_revision: choice.revision,
                          widths_mm: survey?.widths_mm ?? [""],
                          heights_mm: survey?.heights_mm ?? [""],
                          wall: survey?.wall ?? "",
                          squareness_mm: survey?.squareness_mm ?? null,
                          plumb_mm: survey?.plumb_mm ?? null,
                          origin: "SITE",
                          override: survey?.override ?? null,
                          independent_extras: survey?.independent_extras ?? null,
                        },
                      ]);
                    }}
                  >
                    <option value="">Elige el montaje</option>
                    {query.data!.map((item) => (
                      <option key={item.rule.code} value={item.rule.code}>
                        {item.rule.name}
                        {item.rule.synthetic ? " · DEMO" : ""}
                      </option>
                    ))}
                  </select>
                </label>
                {survey && (
                  <SurveyFields
                    value={survey}
                    onChange={(next) =>
                      edit(
                        value.map((item) =>
                          item.module_id === target ? { ...next, origin: "SITE" } : item,
                        ),
                      )
                    }
                  />
                )}
              </section>
            );
          })}
          <label>
            Antecedente de la rectificación
            <textarea
              value={reason}
              onChange={(e) => {
                setReason(e.target.value);
                setProposal(null);
              }}
            />
          </label>
          <button
            disabled={value.length !== targets.length || !reason.trim()}
            onClick={() => void calculate()}
          >
            Revisar rectificación y precio
          </button>
          {proposal && (
            <section aria-label="Cambio por rectificación">
              <div className="mounting-grid">
                <div>
                  <p>Antes · {formatRevision(project.current_revision)}</p>
                  <PositionThumb design={position.design} />
                </div>
                <div>
                  <p>Después · fabricación propuesta</p>
                  <PositionThumb design={proposal.design} />
                </div>
              </div>
              {(proposal.measurements as MountingEvidence[]).map((item, i) => (
                <div key={i}>
                  <MountingChip evidence={item} />
                  {item.result.warnings.map((w) => (
                    <p className="mounting-warning" key={w}>
                      {w}
                    </p>
                  ))}
                </div>
              ))}
              {price?.delta_net !== null && price?.delta_net !== undefined ? (
                <p className="mounting-number">
                  Venta neta del proyecto: {formatMoney(price.before_net!, price.currency!)} →{" "}
                  {formatMoney(price.after_net!, price.currency!)} · Δ{" "}
                  {formatMoney(price.delta_net, price.currency!)}
                </p>
              ) : (
                <p>Sin dato: {price?.reason ?? "no se pudo calcular la venta"}</p>
              )}
              <p>
                Fuente: reglas de Precios del proyecto, servicios, descuento e impuesto. La medida
                rectificada requiere confirmación antes de emitir para producción.
              </p>
              <button className="primary-action" onClick={() => void calculate(true)}>
                Aplicar rectificación{project.status === "DRAFT" ? "" : " y abrir revisión"}
              </button>
              <button onClick={() => setProposal(null)}>Descartar propuesta</button>
            </section>
          )}
        </fieldset>
      )}
      {error && <p role="alert">{error}</p>}
    </details>
  );
}
