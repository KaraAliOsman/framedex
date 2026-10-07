import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { mountingPreview, mountingRules } from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { parseDecimalInput } from "../../decimal";
import { fmtMm } from "../../format";
import { LoadingState } from "../../ui/States";
import { actionErrorDetail } from "../errors";
import { useCanvasStore } from "../canvas/canvasStore";
import type { ProductJson, ProductModuleJson } from "../canvas/productEditing";
import { AxisBreakdown, MountingChip } from "./MeasurementPanel";
import { walls, type MountingEvidence, type OpeningSurvey, type RuleRecord } from "./mountingModel";
import "./mounting.css";

export function SurveyFields({
  value,
  onChange,
  disabled = false,
}: {
  value: OpeningSurvey;
  onChange(next: OpeningSurvey): void;
  disabled?: boolean;
}) {
  const patch = (next: Partial<OpeningSurvey>) => onChange({ ...value, ...next });
  const multiple = value.widths_mm.length === 3;
  return (
    <fieldset className="mounting-fields" disabled={disabled}>
      <label>
        Origen de las medidas
        <select
          value={value.origin}
          onChange={(e) => patch({ origin: e.target.value as OpeningSurvey["origin"] })}
        >
          <option value="CUSTOMER">Medidas del cliente</option>
          <option value="SITE">Rectificadas en obra</option>
        </select>
      </label>
      <label className="mounting-check">
        <input
          type="checkbox"
          checked={multiple}
          onChange={(e) =>
            patch({
              widths_mm: e.target.checked
                ? [value.widths_mm[0] ?? "", "", ""]
                : [value.widths_mm[0] ?? ""],
              heights_mm: e.target.checked
                ? [value.heights_mm[0] ?? "", "", ""]
                : [value.heights_mm[0] ?? ""],
            })
          }
        />
        Medir en tres puntos
      </label>
      <div className="mounting-grid">
        {(
          [
            ["widths_mm", "Ancho", ["Arriba", "Centro", "Abajo"]],
            ["heights_mm", "Alto", ["Izquierda", "Centro", "Derecha"]],
          ] as const
        ).map(([key, label, points]) => (
          <div key={key}>
            {value[key].map((sample, index) => (
              <label key={index}>
                {label}
                {multiple ? ` · ${points[index]}` : ""} (mm)
                <input
                  inputMode="decimal"
                  value={sample}
                  onChange={(e) =>
                    patch({ [key]: value[key].map((v, i) => (i === index ? e.target.value : v)) })
                  }
                />
              </label>
            ))}
          </div>
        ))}
      </div>
      <label>
        Tipo de muro
        <select
          value={value.wall}
          onChange={(e) => patch({ wall: e.target.value as OpeningSurvey["wall"] })}
        >
          <option value="">Elige el tipo de muro</option>
          {walls.map(([key, name]) => (
            <option key={key} value={key}>
              {name}
            </option>
          ))}
        </select>
      </label>
      <details>
        <summary>Avanzado · escuadra y fijación manual</summary>
        <div className="mounting-grid">
          {(["squareness_mm", "plumb_mm"] as const).map((key, index) => (
            <label key={key}>
              {index === 0 ? "Descuadre" : "Desplome"} medido (mm)
              <input
                inputMode="decimal"
                placeholder="Sin medir"
                value={value[key] ?? ""}
                onChange={(e) => patch({ [key]: e.target.value || null })}
              />
            </label>
          ))}
        </div>
        <label className="mounting-check">
          <input
            type="checkbox"
            checked={value.override !== null}
            onChange={(e) =>
              patch({
                override: e.target.checked ? { width_mm: "", height_mm: "", reason: "" } : null,
              })
            }
          />
          Fijar fabricación manualmente
        </label>
        {value.override && (
          <>
            <div className="mounting-grid">
              {(["width_mm", "height_mm"] as const).map((key, index) => (
                <label key={key}>
                  Fabricación · {index === 0 ? "ancho" : "alto"} (mm)
                  <input
                    inputMode="decimal"
                    value={value.override![key]}
                    onChange={(e) =>
                      patch({ override: { ...value.override!, [key]: e.target.value } })
                    }
                  />
                </label>
              ))}
            </div>
            <label>
              Motivo de la fijación
              <textarea
                value={value.override.reason}
                onChange={(e) =>
                  patch({ override: { ...value.override!, reason: e.target.value } })
                }
              />
            </label>
          </>
        )}
      </details>
    </fieldset>
  );
}

export class SurveyInputError extends Error {}

export function normalizedSurvey(value: OpeningSurvey): OpeningSurvey {
  if (!value.wall) throw new SurveyInputError("Elige el tipo de muro medido en obra.");
  const exact = (v: string) => {
    const parsed = parseDecimalInput(v);
    if (parsed === null)
      throw new SurveyInputError("Indica medidas en milímetros, con hasta dos decimales.");
    return parsed;
  };
  return {
    ...value,
    widths_mm: value.widths_mm.map(exact),
    heights_mm: value.heights_mm.map(exact),
    squareness_mm: value.squareness_mm === null ? null : exact(value.squareness_mm),
    plumb_mm: value.plumb_mm === null ? null : exact(value.plumb_mm),
    override:
      value.override === null
        ? null
        : {
            ...value.override,
            width_mm: exact(value.override.width_mm),
            height_mm: exact(value.override.height_mm),
          },
  };
}

export function MountingInspector({
  module,
  product,
  busy,
  onChanged,
}: {
  module: ProductModuleJson;
  product: ProductJson;
  busy: boolean;
  onChanged(): void;
}) {
  const org = useAuthSession().me?.active_organization;
  const inputs = useCanvasStore((s) => s.inputs);
  const evidence = inputs.mounting?.find((item) => item.survey.module_id === module.id);
  const query = useQuery({
    queryKey: ["mounting-rules", org?.id, inputs.systemId],
    enabled: Boolean(org && inputs.systemId),
    queryFn: async () => {
      const r = await mountingRules(inputs.systemId!, {
        headers: { "X-Organization-ID": org!.id },
      });
      if (r.status !== 200) throw new ApiError(r.status, r.data);
      return r.data.items as RuleRecord[];
    },
  });
  const [draft, setDraft] = useState<OpeningSurvey | null>(null);
  const [proposal, setProposal] = useState<{
    product: ProductJson;
    evidence: MountingEvidence[];
  } | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    setDraft(null);
    setProposal(null);
    setError("");
  }, [module.id, inputs.systemId, evidence]);
  const survey = draft ?? evidence?.survey;
  const rules = query.data ?? [];
  const edit = (next: OpeningSurvey) => {
    setDraft(next);
    setProposal(null);
    setError("");
  };
  async function calculate() {
    if (!survey || !org || !inputs.systemId) return;
    setPending(true);
    setError("");
    try {
      const r = await mountingPreview(
        {
          design: {
            system_id: inputs.systemId,
            color: inputs.color,
            nominal_width_mm: inputs.nominalWidthMm,
            nominal_height_mm: inputs.nominalHeightMm,
            parametric_tree: product,
          },
          measurements: [
            ...(inputs.mounting ?? [])
              .filter((item) => item.survey.module_id !== module.id)
              .map((item) => item.survey),
            normalizedSurvey(survey),
          ],
        },
        { headers: { "X-Organization-ID": org.id } },
      );
      if (r.status !== 200) throw new ApiError(r.status, r.data);
      setProposal({
        product: r.data.design.parametric_tree as ProductJson,
        evidence: r.data.measurements as MountingEvidence[],
      });
    } catch (cause) {
      setError(
        cause instanceof SurveyInputError
          ? cause.message
          : actionErrorDetail(cause, "Revisa las medidas y la regla de montaje."),
      );
    } finally {
      setPending(false);
    }
  }
  return (
    <details className="inspector-section mounting-inspector" open>
      <summary>Vano y montaje</summary>
      {query.isPending && inputs.systemId ? (
        <LoadingState label="Cargando reglas de montaje…" />
      ) : query.isError ? (
        <p role="alert">
          No pudimos cargar los montajes.{" "}
          <button onClick={() => void query.refetch()}>Reintentar</button>
        </p>
      ) : rules.length === 0 ? (
        <p>
          Sin dato: esta serie no tiene montaje declarado. El dueño o encargado lo configura en{" "}
          <Link to="/settings/general">Ajustes › Vano y montaje</Link>.
        </p>
      ) : (
        <>
          <label>
            Tipo de montaje
            <select
              disabled={busy || pending}
              value={survey?.rule_code ?? ""}
              onChange={(e) => {
                const chosen = rules.find((item) => item.rule.code === e.target.value);
                if (!chosen) return;
                edit({
                  ...survey,
                  module_id: module.id,
                  rule_code: chosen.rule.code,
                  rule_revision: chosen.revision,
                  widths_mm: survey?.widths_mm ?? [""],
                  heights_mm: survey?.heights_mm ?? [""],
                  wall: survey?.wall ?? "",
                  origin: survey?.origin ?? "CUSTOMER",
                  squareness_mm: survey?.squareness_mm ?? null,
                  plumb_mm: survey?.plumb_mm ?? null,
                  override: survey?.override ?? null,
                });
              }}
            >
              <option value="">Elige el montaje</option>
              {rules.map((item) => (
                <option key={item.rule.code} value={item.rule.code}>
                  {item.rule.name}
                  {item.rule.synthetic ? " · DEMO" : ""}
                </option>
              ))}
            </select>
          </label>
          {survey && (
            <>
              {rules.some(
                (item) =>
                  item.rule.code === survey.rule_code && item.revision !== survey.rule_revision,
              ) && (
                <p className="mounting-warning">
                  Las medidas conservan su autoridad anterior. Para recalcular, revisa la regla
                  actual.{" "}
                  <button
                    onClick={() => {
                      const current = rules.find((item) => item.rule.code === survey.rule_code);
                      if (current) edit({ ...survey, rule_revision: current.revision });
                    }}
                  >
                    Usar regla actual
                  </button>
                </p>
              )}
              <SurveyFields value={survey} onChange={edit} disabled={busy || pending} />
              <button type="button" disabled={busy || pending} onClick={() => void calculate()}>
                Calcular fabricación
              </button>
            </>
          )}
          {pending && <LoadingState label="Calculando fabricación…" />}
          {error && <p role="alert">{error}</p>}
          {proposal && (
            <section className="mounting-proposal" aria-label="Propuesta de fabricación">
              <p>
                Fabricación actual:{" "}
                <span className="mounting-number">
                  {fmtMm(module.width_mm)} × {fmtMm(module.height_mm)} mm
                </span>
              </p>
              {proposal.evidence
                .filter((item) => item.survey.module_id === module.id)
                .map((item) => (
                  <div key={item.survey.module_id}>
                    <MountingChip evidence={item} />
                    <AxisBreakdown axis={item.result.width} label="Ancho" />
                    <AxisBreakdown axis={item.result.height} label="Alto" />
                    {item.result.warnings.map((w) => (
                      <p key={w} className="mounting-warning">
                        {w}
                      </p>
                    ))}
                    <p>Fuente: {item.rule.source}</p>
                  </div>
                ))}
              <button
                className="primary-action"
                disabled={busy}
                onClick={() => {
                  const state = useCanvasStore.getState();
                  useCanvasStore.getState().commitInputs({
                    ...state.inputs,
                    product: proposal.product,
                    mounting: proposal.evidence,
                  });
                  setProposal(null);
                  setDraft(null);
                  onChanged();
                }}
              >
                Aplicar fabricación
              </button>
            </section>
          )}
          {evidence && !proposal && (
            <>
              <MountingChip evidence={evidence} />
              <details>
                <summary>¿De dónde sale?</summary>
                <AxisBreakdown axis={evidence.result.width} label="Ancho" />
                <AxisBreakdown axis={evidence.result.height} label="Alto" />
                <p>
                  Dispersión: ancho {fmtMm(evidence.result.width.spread_mm)} mm · alto{" "}
                  {fmtMm(evidence.result.height.spread_mm)} mm. Tolerancia:{" "}
                  {fmtMm(evidence.rule.tolerance_mm)} mm.
                </p>
                <p>
                  Fuente: {evidence.rule.source}
                  {evidence.rule.synthetic ? " · DEMO, sin certificación" : ""}
                </p>
              </details>
              {evidence.result.warnings.map((w) => (
                <p key={w} className="mounting-warning">
                  {w}
                </p>
              ))}
            </>
          )}
        </>
      )}
    </details>
  );
}
