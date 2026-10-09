import { Fragment, useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { projectsList } from "../../api/generated/dekopen";
import type { PriceResponse, ProjectResponse } from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import {
  formatDate,
  formatDateTime,
  formatDecimal,
  formatMoney,
  formatPercent as formatFraction,
  formatRevision,
  fmtMm,
} from "../../format";
import { DemoBadge, DimLoader, Drawer, TraceButton } from "../../ui";
import type { ValueTrace } from "../../ui/Signature";
import { ValidatedForm } from "../../ui/FormValidation";
import { actionErrorDetail } from "../errors";

type Request = <T>(path: string, method?: string, body?: unknown) => Promise<T>;
type Reading = {
  current: string | null;
  proposed: string | null;
  delta: string | null;
  delta_pct: string | null;
  delta_pp: string | null;
  traces?: Record<string, ValueTrace>;
};
type Cascade = {
  steps?: { key: string; amount: string }[];
  traces?: Record<string, ValueTrace>;
  cost?: string;
  list_net: string;
  net: string;
  tax?: string;
  gross?: string;
  profit?: string;
  margin?: string | null;
  closes: boolean;
};
type Position = {
  position_index: number;
  location: string;
  typology: string;
  width_mm: string;
  height_mm: string;
  quantity: number;
  unit_cost?: string;
  unit_price: string;
  line_net: string;
  margin?: string | null;
  delta: string | null;
  cascade?: Cascade;
  traces?: Record<string, ValueTrace>;
  discount_pct?: string;
  composition?: {
    kind: string;
    sku: string;
    quantity: string;
    unit: string;
    cost: string;
    trace?: ValueTrace;
  }[];
  warnings: string[];
};
type Evidence = {
  editable?: boolean;
  blocked_reason?: string | null;
  comparison: Record<string, Reading>;
  cascade: Cascade;
  positions: Position[];
  band: { minimum: string; target: string; maximum: string };
  requested_margin: string;
  policy: { requires_approval: boolean; cause_text: string[] };
  sources: string[];
  demo: boolean;
  rounding: string;
  current_revision: string | null;
  explanation: {
    available: boolean;
    reason?: string;
    contributions?: {
      driver: string;
      delta: Record<string, string>;
      traces?: Record<string, ValueTrace>;
    }[];
    closes?: boolean;
  };
  controls?: Controls;
  changes?: { field: string; before: string | null; after: string }[];
};
type Operation = Omit<PriceResponse, "workspace" | "id" | "created_at"> & {
  workspace?: Evidence;
  id: string | null;
  created_at: string | null;
};
type Options = {
  fx: {
    id: string;
    base_currency: string;
    quote_currency: string;
    observed_rate: string;
    observed_date: string;
    effective_date: string;
    source: string;
  }[];
  commercial_lists: { context_code: string; pricing_mode: string }[];
  band: {
    minimum_margin_pct: string;
    default_margin_pct: string;
    maximum_margin_pct: string;
    discount_approval_pct: string;
  } | null;
};
type Controls = {
  pricing_mode: string;
  currency: string;
  effective_date: string;
  context_code: string;
  fx_snapshot_id: string;
  discount_pct: string;
  target_margin: string;
  segment: string;
};

const labels: Record<string, string> = {
  net: "Neto",
  tax: "IVA",
  total: "Total",
  cost: "Costo",
  margin: "Margen",
  profile: "Perfiles",
  reinforcement: "Refuerzo",
  glass: "Vidrio",
  hardware: "Herrajes",
  fitting: "Herrajes",
  panel: "Paneles",
  finish: "Recargo de color",
  extra: "Accesorios y extras",
  waste: "Merma",
  labor: "Proceso y mano de obra",
  installation: "Instalación",
  services: "Servicios del proyecto",
  profit_at_list: "Utilidad a precio de lista",
  discount: "Descuento",
  project_charges: "Otros cargos",
  quantity: "Cantidad",
  dimensions: "Medidas",
  design: "Diseño y catálogo técnico",
  cost_list: "Lista de costos y proceso",
  fx: "Moneda y tipo de cambio",
  commercial_list: "Lista comercial",
  segment: "Segmento",
  commercial: "Precio comercial",
  pricing_mode: "Modo de precio",
  context_code: "Lista comercial",
  currency: "Moneda",
  effective_date: "Fecha de costos",
  fx_snapshot_id: "Tipo de cambio registrado",
  discount_pct: "Descuento",
  target_margin: "Margen solicitado",
  COST_PLUS_MARGIN: "Costo más margen",
  PRICE_PER_M2_BY_TYPOLOGY: "Precio por m² y tipología",
  FIXED_PRICE_MATRIX_DIMENSIONAL: "Matriz por medidas",
  TARGET_GROSS_MARGIN_PROJECT: "Margen del proyecto",
  COMMERCIAL_LIST_WITH_DISCOUNTS: "Lista comercial con descuento",
  FIXED: "Fijo",
  TURN: "Practicable",
  TILT_TURN: "Oscilobatiente",
  SLIDING_2L: "Corredera",
  DOOR_ENTRY: "Puerta",
  AWNING: "Proyectante",
  COMPOSITE: "Composición",
  RETAIL: "Particular",
  ARCHITECT: "Arquitecto",
  CONSTRUCTION: "Constructora",
  PREVIEW: "Propuesta sin aplicar",
  PENDING: "Espera aprobación",
  APPLIED: "Aplicado",
  REJECTED: "Rechazado",
  WITHDRAWN: "Retirado",
};
const modes = [
  "COST_PLUS_MARGIN",
  "PRICE_PER_M2_BY_TYPOLOGY",
  "FIXED_PRICE_MATRIX_DIMENSIONAL",
  "TARGET_GROSS_MARGIN_PROJECT",
  "COMMERCIAL_LIST_WITH_DISCOUNTS",
];
const formatPercent = (value: string | null | undefined) => formatFraction(value, "fraction");
function pctInput(value: string): string {
  const [whole, tail = ""] = value.split(".");
  const digits = tail.padEnd(2, "0");
  const integer = BigInt(whole || "0") * 100n + BigInt(digits.slice(0, 2));
  const remainder = digits.slice(2).replace(/0+$/, "");
  return `${integer}${remainder ? `.${remainder}` : ""}`;
}
function fractionInput(value: string): string | null {
  const match = /^(\d{1,2})(?:[.,](\d{0,2}))?$/.exec(value.trim());
  if (!match) return null;
  return `0.${match[1]!.padStart(2, "0")}${(match[2] ?? "").padEnd(2, "0")}`;
}
function localToday(): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Santiago",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
}
const defaultControls = (): Controls => ({
  pricing_mode: "COST_PLUS_MARGIN",
  currency: "CLP",
  effective_date: localToday(),
  context_code: "DEFAULT",
  fx_snapshot_id: "",
  discount_pct: "0",
  target_margin: "0.35",
  segment: "RETAIL",
});

function Amount({
  value,
  currency,
  formula,
  sources,
  trace,
  inputs,
  display = "money",
}: {
  value: string | null | undefined;
  currency: string;
  formula: string;
  sources: string[];
  trace?: ValueTrace;
  inputs?: ValueTrace["inputs"];
  display?: "money" | "fraction" | "pp";
}): JSX.Element {
  if (value === undefined || value === null) return <span className="price-unknown">Sin dato</span>;
  const evidence = trace ?? {
    formula,
    inputs: inputs ?? [{ label: "Valor sellado en la operación", value, unit: currency }],
    authority: sources.join(" · ") || "Operación comercial sellada",
    engineVersion: "price-workspace-v1",
    result: value,
  };
  const present = (reading: string) =>
    display === "fraction"
      ? formatPercent(reading)
      : display === "pp"
        ? `${formatDecimal(reading, 1)} pp`
        : formatMoney(reading, currency);
  const presented = {
    ...evidence,
    inputs: evidence.inputs.map((input) => ({
      ...input,
      label: labels[input.label] ?? input.label,
      value:
        input.unit === "fracción" || input.unit === "%"
          ? formatFraction(input.value, input.unit === "fracción" ? "fraction" : "points")
          : ["CLP", "USD", "UF"].includes(input.unit ?? "")
            ? formatMoney(input.value, input.unit)
            : formatDecimal(
                input.value,
                Math.min(input.value.split(".")[1]?.replace(/0+$/, "").length ?? 0, 4),
              ),
      unit:
        input.unit === "fracción" || input.unit === "%"
          ? undefined
          : ((
              {
                M: "m",
                M2: "m²",
                EA: "unidad",
                UNIT: "unidad",
                KIT: "kit",
                BAR: "barra",
              } as Record<string, string>
            )[input.unit ?? ""] ?? input.unit),
    })),
    result: present(evidence.result ?? value),
  };
  return (
    <span className="price-amount">
      <span>{present(value)}</span>
      <TraceButton compact trace={presented} />
    </span>
  );
}

function PriceCascade({
  reading,
  currency,
  sources,
  costsVisible,
  netOnly = false,
}: {
  reading: Cascade;
  currency: string;
  sources: string[];
  costsVisible: boolean;
  netOnly?: boolean;
}): JSX.Element {
  return (
    <div className="price-cascade">
      {!costsVisible && (
        <div className="price-cascade__step">
          <span>Precio de lista</span>
          <Amount
            value={reading.list_net}
            currency={currency}
            sources={sources}
            trace={reading.traces?.list_net}
            formula="Suma de precios de lista de posiciones y servicios"
          />
        </div>
      )}
      {reading.steps
        ?.filter(
          (step) =>
            (!netOnly || step.key !== "tax") &&
            (costsVisible || ["discount", "project_charges"].includes(step.key)),
        )
        .map((step) => (
          <div className="price-cascade__step" key={step.key}>
            <span>{labels[step.key] ?? "Componente"}</span>
            <Amount
              value={step.amount}
              currency={currency}
              sources={sources}
              trace={reading.traces?.[step.key]}
              formula={`${labels[step.key] ?? "Componente"} · aporte exacto de la cascada`}
            />
          </div>
        ))}
      {(netOnly ? ["net"] : ["net", "tax", "gross"]).map((key) => (
        <div className="price-cascade__total" key={key}>
          <strong>{key === "gross" ? "Total" : labels[key]}</strong>
          <Amount
            value={reading[key as "net" | "tax" | "gross"]}
            currency={currency}
            sources={sources}
            trace={reading.traces?.[key]}
            formula={
              key === "gross"
                ? "Neto + IVA"
                : key === "tax"
                  ? "Neto × tasa de IVA; redondeo por proyecto"
                  : "Precio de lista + descuento firmado + cargos"
            }
          />
        </div>
      ))}
    </div>
  );
}

function controlValue(field: string, value: string | null): string {
  if (value === null) return "Sin dato";
  if (["target_margin", "discount_pct"].includes(field))
    return formatFraction(value.replace(/\s*%$/, ""), "points");
  if (field === "effective_date") return formatDate(value);
  if (field === "fx_snapshot_id") return value.replace(/(\d{4})-(\d{2})-(\d{2})/g, "$3-$2-$1");
  return labels[value] ?? (value === "DEFAULT" ? "Lista principal" : value);
}

function Projection({ operation, owner }: { operation: Operation; owner: boolean }): JSX.Element {
  const value = operation.workspace;
  const currency = operation.currency;
  if (!value)
    return (
      <section className="price-reading">
        <h2>
          {formatRevision(operation.revision_code)} · {labels[operation.state]}
        </h2>
        <p>
          Sin dato: esta operación histórica no guardó la cascada ni las autoridades necesarias para
          explicar cada impulsor.
        </p>
        <PriceCascade
          reading={{
            list_net: operation.project_net,
            net: operation.project_net,
            tax: operation.project_tax,
            gross: operation.project_gross,
            closes: true,
          }}
          currency={currency}
          sources={[]}
          costsVisible={false}
        />
      </section>
    );
  const sources = value.sources;
  return (
    <div className="price-reading">
      <div className="price-reading__heading">
        <h2>Actual y propuesto</h2>
        {value.demo && (
          <DemoBadge source="El cálculo utiliza autoridades sintéticas del catálogo DEMO." />
        )}
      </div>
      <p className="price-reading__context">
        {value.current_revision
          ? `Actual: ${formatRevision(value.current_revision)} · `
          : "Actual: sin precio aplicado · "}
        Propuesto: {formatRevision(operation.revision_code)}
      </p>
      <table className="price-comparison">
        <thead>
          <tr>
            <th>Concepto</th>
            <th>Actual</th>
            <th>Propuesto</th>
            <th>Δ</th>
          </tr>
        </thead>
        <tbody>
          {[
            "net",
            "tax",
            "total",
            ...(owner && operation.costs_visible ? ["cost", "margin"] : []),
          ].map((key) => {
            const row = value.comparison[key];
            if (!row) return null;
            return (
              <tr key={key}>
                <th>{labels[key]}</th>
                {key === "margin" ? (
                  <>
                    <td>
                      <Amount
                        value={row.current}
                        currency={currency}
                        sources={sources}
                        display="fraction"
                        trace={row.traces?.current}
                        formula="Margen de la operación aplicada"
                      />
                    </td>
                    <td>
                      <Amount
                        value={row.proposed}
                        currency={currency}
                        sources={sources}
                        display="fraction"
                        trace={row.traces?.proposed}
                        formula="Margen calculado por el motor"
                      />
                    </td>
                    <td>
                      <Amount
                        value={row.delta_pp}
                        currency={currency}
                        sources={sources}
                        display="pp"
                        trace={row.traces?.delta_pp}
                        formula="Diferencia de margen en puntos porcentuales"
                      />
                    </td>
                  </>
                ) : (
                  <>
                    <td>
                      <Amount
                        value={row.current}
                        currency={currency}
                        sources={sources}
                        trace={row.traces?.current}
                        formula="Autoridad de la última operación aplicada"
                      />
                    </td>
                    <td>
                      <Amount
                        value={row.proposed}
                        currency={currency}
                        sources={sources}
                        trace={
                          row.traces?.proposed ??
                          value.cascade.traces?.[key === "total" ? "gross" : key]
                        }
                        formula={`Motor · ${labels[key]} propuesto`}
                      />
                    </td>
                    <td>
                      <Amount
                        value={row.delta}
                        currency={currency}
                        sources={sources}
                        trace={row.traces?.delta}
                        inputs={[
                          { label: "Actual", value: row.current ?? "", unit: currency },
                          { label: "Propuesto", value: row.proposed ?? "", unit: currency },
                        ]}
                        formula="Propuesto − actual"
                      />
                      {row.delta_pct !== null && (
                        <small>
                          <Amount
                            value={row.delta_pct}
                            currency={currency}
                            sources={sources}
                            display="fraction"
                            trace={row.traces?.delta_pct}
                            formula="Δ relativo al precio aplicado"
                          />
                        </small>
                      )}
                    </td>
                  </>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="price-band">
        <p>
          <strong>Banda de margen</strong> · mínimo {formatPercent(value.band.minimum)}, objetivo{" "}
          {formatPercent(value.band.target)}, máximo {formatPercent(value.band.maximum)}
        </p>
        <svg aria-hidden viewBox="0 0 100 10">
          <path d="M0 5H100" />
          {[value.band.minimum, value.band.target, value.band.maximum].map((amount, index) => (
            <path key={index} d={`M${Number(amount) * 100} 1V9`} />
          ))}
          <circle
            cx={
              Number(
                owner && operation.costs_visible
                  ? (value.cascade.margin ?? value.requested_margin)
                  : value.requested_margin,
              ) * 100
            }
            cy="5"
            r="1.4"
          />
        </svg>
        <p>
          {owner && operation.costs_visible ? (
            <>
              Utilidad de la obra:{" "}
              <Amount
                value={value.cascade.profit}
                currency={currency}
                sources={sources}
                trace={value.cascade.traces?.profit}
                formula="Neto − costo total"
              />
            </>
          ) : (
            <>
              Margen solicitado: {formatPercent(value.requested_margin)}. Los costos de compra son
              confidenciales.
            </>
          )}
        </p>
        {value.policy.cause_text.map((text) => (
          <p key={text} className="price-policy">
            {text}
          </p>
        ))}
      </div>
      <h3>De costo a precio</h3>
      <PriceCascade
        reading={value.cascade}
        currency={currency}
        sources={sources}
        costsVisible={owner && operation.costs_visible}
      />
      <h3>Posiciones</h3>
      <div className="price-positions" tabIndex={0} aria-label="Tabla de posiciones">
        <table>
          <thead>
            <tr>
              {[
                "Pos.",
                "Ubicación y tipología",
                "Medidas · cantidad",
                ...(owner && operation.costs_visible ? ["Costo unitario"] : []),
                "Precio unitario",
                "Neto línea",
                ...(owner && operation.costs_visible ? ["Margen"] : []),
                "Δ neto",
              ].map((title) => (
                <th key={title}>{title}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {value.positions.map((line) => (
              <Fragment key={line.position_index}>
                <tr>
                  <th>{line.position_index}</th>
                  <td>
                    {line.location || "Sin ubicación"}
                    <small>{labels[line.typology] ?? "Composición"}</small>
                  </td>
                  <td>
                    {fmtMm(line.width_mm)} × {fmtMm(line.height_mm)} mm
                    <small>
                      {line.quantity} {line.quantity === 1 ? "unidad" : "unidades"}
                    </small>
                  </td>
                  {owner && operation.costs_visible && (
                    <td>
                      <Amount
                        value={line.unit_cost}
                        currency={currency}
                        sources={sources}
                        trace={line.traces?.unit_cost}
                        formula="Composición + merma + mano de obra por unidad"
                      />
                    </td>
                  )}
                  <td>
                    <Amount
                      value={line.unit_price}
                      currency={currency}
                      sources={sources}
                      trace={line.traces?.unit_price}
                      formula="Precio unitario calculado; lectura a cuatro decimales"
                    />
                  </td>
                  <td>
                    <Amount
                      value={line.line_net}
                      currency={currency}
                      sources={sources}
                      trace={line.traces?.line_net}
                      formula="Precio exacto × cantidad × (1 − descuento); redondeo de línea"
                    />
                  </td>
                  {owner && operation.costs_visible && (
                    <td>
                      <Amount
                        value={line.margin}
                        currency={currency}
                        sources={sources}
                        display="fraction"
                        trace={line.traces?.margin}
                        formula="(Neto de la posición − costo) ÷ neto"
                      />
                    </td>
                  )}
                  <td>
                    <Amount
                      value={line.delta}
                      currency={currency}
                      sources={sources}
                      trace={line.traces?.delta}
                      formula="Neto propuesto de la posición − neto aplicado"
                    />
                  </td>
                </tr>
                <tr>
                  <td colSpan={owner && operation.costs_visible ? 8 : 6}>
                    <details>
                      <summary>Composición de la posición {line.position_index}</summary>
                      <p>Descuento de esta posición: {formatPercent(line.discount_pct)}.</p>
                      {line.warnings.map((text) => (
                        <p key={text}>{text}</p>
                      ))}
                      {owner && operation.costs_visible && line.cascade ? (
                        <>
                          <PriceCascade
                            reading={line.cascade}
                            currency={currency}
                            sources={sources}
                            costsVisible
                            netOnly
                          />
                          <p>
                            IVA definitivo por proyecto. Esta lectura llega al neto de la posición.
                          </p>
                          <table className="price-composition">
                            <thead>
                              <tr>
                                <th>Artículo</th>
                                <th>Uso</th>
                                <th>Costo por unidad de ventana</th>
                              </tr>
                            </thead>
                            <tbody>
                              {line.composition?.map((item, index) => (
                                <tr key={index}>
                                  <td>
                                    {item.kind === "FINISH" && item.sku === "WHITE"
                                      ? "Blanco"
                                      : item.sku}
                                  </td>
                                  <td>
                                    {formatDecimal(
                                      item.quantity,
                                      ["M", "M2"].includes(item.unit) ? 2 : 0,
                                    )}{" "}
                                    {(
                                      {
                                        M: "m",
                                        M2: "m²",
                                        BAR: "barra",
                                        KIT: "kit",
                                        EA: "unidad",
                                      } as Record<string, string>
                                    )[item.unit] ?? "unidad"}
                                  </td>
                                  <td>
                                    <Amount
                                      value={item.cost}
                                      currency={currency}
                                      sources={sources}
                                      trace={item.trace}
                                      formula="Costo consumido del artículo según la compra y el cálculo sellados"
                                    />
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </>
                      ) : (
                        <>
                          {line.cascade && (
                            <PriceCascade
                              reading={line.cascade}
                              currency={currency}
                              sources={sources}
                              costsVisible={false}
                              netOnly
                            />
                          )}
                          <p>
                            La venta de esta posición queda sellada en su neto. La composición de
                            compra está reservada al dueño y jefe de taller.
                          </p>
                        </>
                      )}
                    </details>
                  </td>
                </tr>
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
      <p className="price-rounding">{value.rounding}</p>
      <h3>¿Por qué cambió?</h3>
      {value.explanation.available ? (
        <>
          <p>
            Reprecio en orden canónico. Las interacciones se atribuyen al impulsor aplicado después;
            los aportes cierran el Δ exacto.
          </p>
          <table className="price-drivers">
            <thead>
              <tr>
                <th>Impulsor</th>
                <th>Δ neto</th>
                <th>Δ total</th>
              </tr>
            </thead>
            <tbody>
              {value.explanation.contributions?.map((item) => (
                <tr key={item.driver}>
                  <th>{labels[item.driver] ?? "Condición"}</th>
                  <td>
                    <Amount
                      value={item.delta.net}
                      currency={currency}
                      sources={sources}
                      trace={item.traces?.net}
                      formula={`Reprecio tras ${labels[item.driver] ?? "condición"} − etapa anterior`}
                    />
                  </td>
                  <td>
                    <Amount
                      value={item.delta.total}
                      currency={currency}
                      sources={sources}
                      trace={item.traces?.total}
                      formula="Diferencia de total con IVA entre etapas"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      ) : (
        <p>{value.explanation.reason}</p>
      )}
      {value.changes && value.changes.length > 0 && (
        <details>
          <summary>Cambios por campo</summary>
          <dl>
            {value.changes.map((change) => (
              <div key={change.field}>
                <dt>{labels[change.field] ?? "Condición comercial"}</dt>
                <dd>
                  {controlValue(change.field, change.before)} →{" "}
                  {controlValue(change.field, change.after)}
                </dd>
              </div>
            ))}
          </dl>
        </details>
      )}
      <details>
        <summary>Autoridades del cálculo</summary>
        <ul>
          {sources.map((source) => (
            <li key={source}>{source}</li>
          ))}
        </ul>
      </details>
    </div>
  );
}

function PriceControlRail({ children }: { children: ReactNode }): JSX.Element {
  const [compact, setCompact] = useState(
    () => window.matchMedia?.("(max-width: 1280px)").matches ?? false,
  );
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const query = window.matchMedia?.("(max-width: 1280px)");
    if (!query) return;
    const changed = () => {
      setCompact(query.matches);
      setOpen(false);
    };
    query.addEventListener("change", changed);
    return () => query.removeEventListener("change", changed);
  }, []);
  const panel = (
    <aside className="price-controls" aria-label="Control de precios">
      {children}
    </aside>
  );
  if (!compact) return panel;
  return (
    <div className="price-control-entry">
      <button type="button" onClick={() => setOpen(true)}>
        Ajustar propuesta y decidir
      </button>
      {open && (
        <Drawer title="Propuesta y decisión" onClose={() => setOpen(false)}>
          <div className="pricing-page price-control-drawer">{panel}</div>
        </Drawer>
      )}
    </div>
  );
}

export function ProjectPrices({
  request,
  owner,
  projectId: boundProjectId,
}: {
  request: Request;
  owner: boolean;
  projectId?: string;
}): JSX.Element {
  const auth = useAuthSession();
  const orgId = auth.me?.active_organization?.id;
  const userId = auth.me?.user?.id;
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [projectId, setProjectId] = useState(boundProjectId ?? "");
  const [controls, setControls] = useState<Controls>(defaultControls);
  const [options, setOptions] = useState<Options | null>(null);
  const [history, setHistory] = useState<Operation[]>([]);
  const [projection, setProjection] = useState<Operation | null>(null);
  const [review, setReview] = useState<Operation | null>(null);
  const [reason, setReason] = useState("Cotización inicial del proyecto");
  const [comment, setComment] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState("");
  const [emptyProject, setEmptyProject] = useState(false);
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [reload, setReload] = useState(0);
  const generation = useRef(0);
  const actionGeneration = useRef(0);
  const touched = useRef(false);
  const reasonEdited = useRef(false);

  const loadHistory = useCallback(async () => {
    const result = await request<Operation[]>("operations/");
    if (!Array.isArray(result)) throw new Error("El historial no devolvió operaciones válidas.");
    return result;
  }, [request]);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    void Promise.all([
      request<Options>("options/"),
      loadHistory(),
      projectsList({ headers: { "X-Organization-ID": orgId! } }),
    ])
      .then(([available, operations, projectResult]) => {
        if (!active) return;
        if (!Array.isArray(available.fx) || !Array.isArray(available.commercial_lists))
          throw new Error("Las autoridades comerciales no están disponibles.");
        setOptions(available);
        setHistory(operations);
        if (projectResult.status !== 200)
          throw new Error("No se pudo cargar la lista de proyectos.");
        setProjects(projectResult.data.items);
        if (!touched.current)
          setControls((current) => ({
            ...current,
            target_margin: available.band?.default_margin_pct ?? current.target_margin,
          }));
      })
      .catch((failure: unknown) => {
        if (active && !(failure instanceof DOMException && failure.name === "AbortError"))
          setError(
            actionErrorDetail(
              failure,
              "No se pudieron cargar las autoridades de precios. Vuelve a intentar.",
            ),
          );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
      generation.current += 1;
      actionGeneration.current += 1;
    };
  }, [request, loadHistory, orgId, reload]);

  useEffect(() => {
    const current = ++generation.current;
    if (!projectId || !options || review) return;
    setCalculating(true);
    setError("");
    setEmptyProject(false);
    const timer = window.setTimeout(() => {
      void request<Operation>("workspace/", "POST", {
        ...controls,
        project_id: projectId,
        reason: reason || "Proyección de precios",
        fx_snapshot_id: controls.fx_snapshot_id || null,
        confirmed,
      })
        .then((value) => {
          if (generation.current !== current) return;
          if (!value.workspace || !Array.isArray(value.workspace.positions))
            throw new Error("El motor no entregó una lectura de precios válida.");
          setProjection(value);
        })
        .catch((failure: unknown) => {
          if (
            generation.current === current &&
            !(failure instanceof DOMException && failure.name === "AbortError")
          ) {
            setProjection(null);
            if (
              failure instanceof ApiError &&
              (failure.payload as { error?: { code?: string } } | null)?.error?.code ===
                "project_has_no_positions"
            ) {
              setEmptyProject(true);
              return;
            }
            setError(
              actionErrorDetail(
                failure,
                "No se pudo calcular. Revisa las autoridades y los costos de las posiciones.",
              ),
            );
          }
        })
        .finally(() => {
          if (generation.current === current) setCalculating(false);
        });
    }, 350);
    return () => {
      window.clearTimeout(timer);
      generation.current += 1;
    };
    // A reason is audit text; editing it does not change the price.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, controls, options, review, refresh, request]);
  useEffect(() => {
    if (reasonEdited.current || !projection?.workspace) return;
    setReason(
      projection.workspace.policy.requires_approval
        ? projection.workspace.policy.cause_text.join(" ")
        : "Cotización inicial del proyecto",
    );
  }, [projection]);
  function update(key: keyof Controls, value: string): void {
    generation.current += 1;
    actionGeneration.current += 1;
    touched.current = true;
    setConfirmed(false);
    setBusy(false);
    setNotice("");
    setReview(null);
    setControls((current) => ({ ...current, [key]: value }));
  }
  function chooseOperation(item: Operation): void {
    generation.current += 1;
    actionGeneration.current += 1;
    setBusy(false);
    setCalculating(false);
    setReview(item);
    setComment("");
    setConfirmed(false);
    setNotice("");
    setError("");
  }
  async function act(kind: "save" | "approve" | "reject" | "withdraw" | "read"): Promise<void> {
    generation.current += 1;
    const current = ++actionGeneration.current;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      let operation = review ?? projection;
      if (!operation) return;
      if (kind === "read") {
        await request("acknowledge/", "POST", { operation_ids: [operation.id] });
        if (actionGeneration.current !== current) return;
        setNotice("Decisión marcada como leída.");
      } else if (kind === "save") {
        operation = await request<Operation>("preview/", "POST", {
          ...controls,
          project_id: projectId,
          reason,
          fx_snapshot_id: controls.fx_snapshot_id || null,
          confirmed,
        });
        if (actionGeneration.current !== current) return;
        if (
          JSON.stringify(operation.workspace?.comparison) !==
          JSON.stringify(projection?.workspace?.comparison)
        ) {
          setReview(operation);
          setNotice("Las autoridades cambiaron. Revisa el precio actualizado antes de aplicar.");
        } else if (operation.state === "PENDING" && !owner) {
          setReview(operation);
          setNotice("Solicitud enviada al dueño. Puedes retirarla mientras espera aprobación.");
        } else {
          operation = await request<Operation>(`operations/${operation.id}/apply/`, "POST", {
            reason,
            confirmed,
          });
          if (actionGeneration.current !== current) return;
          setReview(operation);
          setNotice("Precio aplicado al proyecto.");
        }
      } else {
        operation = await request<Operation>(
          `operations/${operation.id}/${kind === "withdraw" ? "withdraw" : "apply"}/`,
          "POST",
          {
            reason: kind === "withdraw" ? reason || "Retiro de solicitud" : comment,
            ...(kind === "withdraw" ? {} : { confirmed, reject: kind === "reject" }),
          },
        );
        if (actionGeneration.current !== current) return;
        setReview(operation);
        setNotice(
          kind === "reject"
            ? "Solicitud rechazada. El solicitante recibirá la decisión."
            : kind === "withdraw"
              ? "Solicitud retirada."
              : "Solicitud aprobada y precio aplicado. El solicitante recibirá la decisión.",
        );
      }
      const operations = await loadHistory();
      if (actionGeneration.current === current) {
        setHistory(operations);
        if (kind === "read")
          setReview((value) => (value ? { ...value, notification_unread: false } : null));
      }
      window.dispatchEvent(new Event("dekopen:pricing-changed"));
    } catch (failure) {
      if (actionGeneration.current === current)
        setError(
          actionErrorDetail(
            failure,
            "No se guardó el cambio. Revisa los datos y vuelve a intentar.",
          ),
        );
    } finally {
      if (actionGeneration.current === current) setBusy(false);
    }
  }
  const displayed = review ?? projection;
  const requested = displayed?.workspace?.policy.requires_approval;
  const rows = history.filter((item) => !boundProjectId || item.project_id === boundProjectId);
  const groups = [...new Set(rows.map((item) => `${item.project_id}|${item.revision_code}`))];
  return (
    <section className="project-prices">
      {!boundProjectId && (
        <>
          <h2>{owner ? "Solicitudes y decisiones de precios" : "Tus solicitudes y decisiones"}</h2>
          <p>Abre una solicitud para decidir; entra al proyecto para preparar un precio.</p>
          <label>
            Proyecto
            <select
              value={projectId}
              onChange={(event) => {
                generation.current += 1;
                actionGeneration.current += 1;
                setProjectId(event.target.value);
                setConfirmed(false);
                setBusy(false);
                setProjection(null);
                setReview(null);
              }}
            >
              <option value="">Selecciona un proyecto</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.code} · {project.name}
                </option>
              ))}
            </select>
          </label>
        </>
      )}
      {loading && (
        <p className="price-loading" role="status">
          <DimLoader label="Cargando precios y autoridades" />
          Cargando precios y autoridades…
        </p>
      )}
      {emptyProject && (
        <section className="price-empty">
          <h2>El proyecto aún no tiene posiciones</h2>
          <p>Agrega la primera ventana para calcular su precio y comprobar los costos.</p>
          <Link
            className="ui-button ui-button--primary"
            to={`/projects/${projectId}/positions/new`}
          >
            Agregar primera ventana
          </Link>
        </section>
      )}
      {error && (
        <div className="price-error" role="alert">
          <p>{error}</p>
          {owner ? (
            <Link to="/pricing/cost-lists">Completar costos y autoridades</Link>
          ) : (
            <p>Si falta un costo vigente, el dueño debe completarlo antes de aplicar.</p>
          )}
          <button
            type="button"
            onClick={() => {
              setReload((count) => count + 1);
              setRefresh((count) => count + 1);
            }}
          >
            Volver a intentar
          </button>
        </div>
      )}
      {notice && <p role="status">{notice}</p>}
      {(projectId || review) && !emptyProject && (
        <div className="price-layout">
          <section aria-label="Lectura de precios" aria-busy={calculating || undefined}>
            {calculating && (
              <p className="price-loading" role="status">
                <DimLoader label="Recalculando precios" />
                El motor está recalculando la propuesta…
              </p>
            )}
            {displayed ? (
              <Projection operation={displayed} owner={owner} />
            ) : (
              !loading &&
              !error &&
              !emptyProject && <p>Sin dato: el proyecto todavía no tiene un precio calculado.</p>
            )}
          </section>
          <PriceControlRail>
            {review ? (
              <section>
                <h2>{labels[review.state]}</h2>
                <p>
                  {review.project_code} · {review.project_name} ·{" "}
                  {formatRevision(review.revision_code)}
                </p>
                <p>
                  Solicitó {review.requested_by_email ?? "un integrante del taller"} ·{" "}
                  {review.created_at && formatDateTime(review.created_at)}
                </p>
                <p>{review.reason}</p>
                {review.approved_at && (
                  <p>Decisión del dueño · {formatDateTime(review.approved_at)}</p>
                )}
                {review.state === "PENDING" && owner && (
                  <ValidatedForm
                    onSubmit={(event) => {
                      event.preventDefault();
                      void act("approve");
                    }}
                  >
                    <label>
                      Comentario de la decisión
                      <textarea
                        required
                        value={comment}
                        onChange={(event) => setComment(event.target.value)}
                      />
                    </label>
                    <label>
                      <input
                        type="checkbox"
                        checked={confirmed}
                        onChange={(event) => setConfirmed(event.target.checked)}
                      />
                      Confirmo las condiciones comerciales
                    </label>
                    <button
                      className="ui-button ui-button--primary"
                      type="submit"
                      disabled={busy || !comment.trim()}
                    >
                      Aprobar y aplicar
                    </button>
                    <button
                      className="ui-button ui-button--danger"
                      type="button"
                      disabled={busy || !comment.trim()}
                      onClick={() => void act("reject")}
                    >
                      Rechazar
                    </button>
                  </ValidatedForm>
                )}
                {review.state === "PREVIEW" && (owner || review.requested_by === userId) && (
                  <ValidatedForm
                    onSubmit={(event) => {
                      event.preventDefault();
                      void act("approve");
                    }}
                  >
                    <label>
                      Motivo para aplicar
                      <textarea
                        required
                        value={comment}
                        onChange={(event) => setComment(event.target.value)}
                      />
                    </label>
                    <button
                      className="ui-button ui-button--primary"
                      type="submit"
                      disabled={busy || !comment.trim()}
                    >
                      Aplicar
                    </button>
                  </ValidatedForm>
                )}
                {review.state === "PENDING" && (owner || review.requested_by === userId) && (
                  <button type="button" disabled={busy} onClick={() => void act("withdraw")}>
                    Retirar solicitud
                  </button>
                )}
                {review.notification_unread && (
                  <button type="button" disabled={busy} onClick={() => void act("read")}>
                    Marcar decisión como leída
                  </button>
                )}
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => {
                    setReview(null);
                    setProjectId(review.project_id);
                    setProjection(null);
                    setRefresh((count) => count + 1);
                  }}
                >
                  Preparar nueva propuesta
                </button>
              </section>
            ) : (
              <ValidatedForm
                onSubmit={(event) => {
                  event.preventDefault();
                  void act("save");
                }}
              >
                <h2>Propuesta</h2>
                <label>
                  Modo de precio
                  <select
                    value={controls.pricing_mode}
                    onChange={(event) => update("pricing_mode", event.target.value)}
                  >
                    {modes
                      .filter((mode) => owner || mode !== "TARGET_GROSS_MARGIN_PROJECT")
                      .map((mode) => (
                        <option key={mode} value={mode}>
                          {labels[mode]}
                        </option>
                      ))}
                  </select>
                </label>
                {["COST_PLUS_MARGIN", "TARGET_GROSS_MARGIN_PROJECT"].includes(
                  controls.pricing_mode,
                ) && (
                  <>
                    <div>
                      <label>
                        Mover margen
                        <input
                          aria-label="Mover margen"
                          type="range"
                          min="0"
                          max="99"
                          step="0.1"
                          value={pctInput(controls.target_margin)}
                          onChange={(event) => {
                            const value = fractionInput(event.target.value);
                            if (value) update("target_margin", value);
                          }}
                        />
                      </label>
                      <label>
                        Margen solicitado (%)
                        <input
                          aria-label="Margen solicitado (%)"
                          inputMode="decimal"
                          value={pctInput(controls.target_margin)}
                          onChange={(event) => {
                            const value = fractionInput(event.target.value);
                            if (value) update("target_margin", value);
                          }}
                        />
                      </label>
                    </div>
                    <p>El motor recalcula la utilidad y la banda al mover el margen.</p>
                  </>
                )}
                {controls.pricing_mode !== "COST_PLUS_MARGIN" &&
                  controls.pricing_mode !== "TARGET_GROSS_MARGIN_PROJECT" && (
                    <label>
                      Lista comercial
                      <select
                        required
                        value={controls.context_code}
                        onChange={(event) => update("context_code", event.target.value)}
                      >
                        <option value="">Selecciona una lista</option>
                        {options?.commercial_lists
                          .filter((item) => item.pricing_mode === controls.pricing_mode)
                          .map((item) => (
                            <option key={item.context_code} value={item.context_code}>
                              {item.context_code === "DEFAULT"
                                ? "Lista principal"
                                : item.context_code}
                            </option>
                          ))}
                      </select>
                    </label>
                  )}
                <label>
                  Descuento (%)
                  <input
                    inputMode="decimal"
                    value={pctInput(controls.discount_pct)}
                    onChange={(event) => {
                      const value = fractionInput(event.target.value);
                      if (value) update("discount_pct", value);
                    }}
                  />
                </label>
                <label>
                  Segmento
                  <select
                    value={controls.segment}
                    onChange={(event) => update("segment", event.target.value)}
                  >
                    {["RETAIL", "ARCHITECT", "CONSTRUCTION"].map((item) => (
                      <option key={item} value={item}>
                        {labels[item]}
                      </option>
                    ))}
                  </select>
                </label>
                <details>
                  <summary>Moneda y autoridades</summary>
                  <label>
                    Moneda
                    <select
                      value={controls.currency}
                      onChange={(event) => update("currency", event.target.value)}
                    >
                      <option value="CLP">CLP</option>
                      <option value="USD">USD</option>
                    </select>
                  </label>
                  <label>
                    Fecha de costos
                    <input
                      type="date"
                      required
                      value={controls.effective_date}
                      onChange={(event) => update("effective_date", event.target.value)}
                    />
                  </label>
                  <label>
                    Tipo de cambio registrado
                    <select
                      value={controls.fx_snapshot_id}
                      onChange={(event) => update("fx_snapshot_id", event.target.value)}
                    >
                      <option value="">Sin conversión de moneda</option>
                      {options?.fx
                        .filter(
                          (item) =>
                            item.effective_date === controls.effective_date &&
                            item.quote_currency === controls.currency,
                        )
                        .map((item) => (
                          <option key={item.id} value={item.id}>
                            {item.base_currency} → {item.quote_currency} ·{" "}
                            {formatDecimal(item.observed_rate, 8)} ·{" "}
                            {formatDate(item.observed_date)}
                          </option>
                        ))}
                    </select>
                  </label>
                </details>
                <label>
                  Motivo
                  {requested && (
                    <span className="field-hint">
                      {displayed?.workspace?.policy.cause_text.join(" ")}
                    </span>
                  )}
                  <textarea
                    required
                    value={reason}
                    onChange={(event) => {
                      reasonEdited.current = true;
                      setReason(event.target.value);
                    }}
                  />
                </label>
                {owner && (
                  <label>
                    <input
                      type="checkbox"
                      checked={confirmed}
                      onChange={(event) => {
                        setConfirmed(event.target.checked);
                        setRefresh((count) => count + 1);
                      }}
                    />
                    Confirmo las condiciones comerciales
                  </label>
                )}
                <button
                  className="ui-button ui-button--primary"
                  type="submit"
                  disabled={
                    busy ||
                    loading ||
                    calculating ||
                    !projection ||
                    projection.workspace?.editable === false ||
                    !reason.trim()
                  }
                >
                  {requested && !owner ? "Solicitar aprobación" : "Aplicar"}
                </button>
                {projection?.workspace?.blocked_reason && (
                  <>
                    <p role="status">{projection.workspace.blocked_reason}</p>
                    <Link to={`/projects/${projectId}`}>Abrir proyecto para revisar el precio</Link>
                  </>
                )}
                <Link to={`/projects/${projectId}`}>Revisar servicios del proyecto</Link>
                {owner && (
                  <Link to="/pricing/cost-lists?section=rules">Ajustar banda y autoridades</Link>
                )}
              </ValidatedForm>
            )}
          </PriceControlRail>
        </div>
      )}
      <section className="price-history">
        <div className="price-reading__heading">
          <h2>Historial por revisión</h2>
          <button type="button" disabled={busy} onClick={() => setReload((count) => count + 1)}>
            Actualizar historial
          </button>
        </div>
        {!loading && rows.length === 0 && (
          <p>
            No hay operaciones guardadas. La proyección se conserva en pantalla hasta que apliques o
            solicites aprobación.
          </p>
        )}
        {groups.map((group) => {
          const items = rows.filter((item) => `${item.project_id}|${item.revision_code}` === group);
          const first = items[0];
          if (!first) return null;
          return (
            <section key={group}>
              <h3>
                {first.project_code} · {formatRevision(first.revision_code)}
              </h3>
              {items.map((item) => (
                <article className="price-history__row" key={item.id}>
                  <div>
                    <Amount
                      value={item.project_gross}
                      currency={item.currency}
                      sources={item.workspace?.sources ?? []}
                      trace={item.workspace?.cascade.traces?.gross}
                      formula="Total sellado de esta operación comercial"
                    />
                    <span>{labels[item.state]}</span>
                    {item.resulted_in_issue && <span>Resultó en emisión</span>}
                    {item.notification_unread && <strong>Decisión nueva</strong>}
                    <p>
                      {item.requested_by_email ?? "Integrante del taller"} ·{" "}
                      {item.created_at && formatDateTime(item.created_at)} · {item.reason}
                    </p>
                  </div>
                  <button type="button" disabled={busy} onClick={() => chooseOperation(item)}>
                    {item.state === "PENDING" && owner ? "Revisar solicitud" : "Ver detalle"}
                  </button>
                </article>
              ))}
            </section>
          );
        })}
        <p>Últimas 100 operaciones de la organización.</p>
      </section>
    </section>
  );
}
