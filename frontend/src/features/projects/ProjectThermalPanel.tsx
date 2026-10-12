import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  projectThermalReport,
  projectThermalSave,
  thermalCompliantAlternative,
} from "../../api/generated/dekopen";
import type { ProjectResponse, ThermalInputRequest } from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import {
  formatDecimal,
  formatDate,
  formatMoney,
  formatPercent,
  parseDecimalInput,
} from "../../format";
import { Button, DimLoader, EmptyState, TraceButton, ValidatedForm } from "../../ui";
import { actionErrorDetail } from "../errors";
import { useProjectOperations, ProjectOpsReview } from "./ProjectOpsReview";
import {
  orientationLabel,
  thermalVerdict,
  type ThermalCandidate,
  type ThermalMetric,
  type ThermalReportData,
  type ThermalSource,
} from "./thermalModel";
import "./thermal.css";

export function useThermalReport(projectId: string, orgId: string) {
  return useQuery({
    queryKey: ["thermal", orgId, projectId],
    queryFn: async ({ signal }) => {
      const result = await projectThermalReport(projectId, {
        signal,
        headers: { "X-Organization-ID": orgId },
      });
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      return result.data as unknown as ThermalReportData;
    },
  });
}

function value(number: string | null | undefined, unit: string, places = 2) {
  return number == null ? "Sin dato" : `${formatDecimal(number, places)} ${unit}`;
}

export function ThermalReadout({ metric }: { metric: ThermalMetric }) {
  const trace = metric.trace;
  const sources: ThermalSource[] = trace
    ? [
        trace.frame_report,
        trace.performance_report,
        ...trace.panes.flatMap((pane) => [pane.glass_report, pane.spacer_report]),
      ].filter((item): item is ThermalSource => item !== null)
    : [];
  const unique = [...new Map(sources.map((source) => [source.id, source])).values()];
  const hasSolarFactor = trace?.panes.some((pane) => pane.solar_factor != null);
  return (
    <div className="thermal-readout">
      <div className="thermal-values">
        <strong>
          Uw <span className="thermal-num">{value(metric.uw, "W/m²K")}</span>
        </strong>
        <TraceButton
          trace={
            trace && metric.state === "KNOWN"
              ? {
                  formula: trace.formula,
                  engineVersion:
                    "ISO 10077-1 · método de áreas; valores mostrados redondeados, cálculo sin redondeo intermedio",
                  authority: [
                    ...new Set(
                      unique.map(
                        (source) =>
                          `${source.source_document} · ${source.laboratory} · ${formatDate(source.report_date)} · ${source.standard} · ${source.source_page}`,
                      ),
                    ),
                  ].join("; "),
                  inputs: [
                    {
                      label: "Ag · vidrio visible",
                      value: formatDecimal(trace.ag_m2, 2),
                      unit: "m²",
                    },
                    { label: "Af · marco", value: formatDecimal(trace.af_m2, 2), unit: "m²" },
                    {
                      label: "lg · borde de vidrio",
                      value: formatDecimal(trace.lg_m, 3),
                      unit: "m",
                    },
                    {
                      label: "Uf · combinación de perfiles",
                      value: value(trace.uf, "", 2),
                      unit: "W/m²K",
                    },
                    ...trace.panes.flatMap((pane, index) => [
                      {
                        label: `Ug · paño ${index + 1}`,
                        value: value(pane.ug, "", 2),
                        unit: "W/m²K",
                      },
                      {
                        label: `Ψg · paño ${index + 1}`,
                        value: value(pane.psi_g, "", 3),
                        unit: "W/mK",
                      },
                    ]),
                  ],
                  result: value(metric.uw, "W/m²K"),
                }
              : null
          }
          cause={metric.missing.join(" ") || "Completa las entradas autoritativas del motor."}
          compact
        />
      </div>
      <dl className="thermal-classes">
        <div>
          <dt>Aire · 100 Pa</dt>
          <dd>{metric.air_class == null ? "Sin dato" : `Clase ${metric.air_class}`}</dd>
        </div>
        <div>
          <dt>Agua</dt>
          <dd>{metric.water_class ?? "Sin dato"}</dd>
        </div>
        <div>
          <dt>Viento</dt>
          <dd>{metric.wind_class ?? "Sin dato"}</dd>
        </div>
      </dl>
      {hasSolarFactor && trace && (
        <p>
          Factor solar g{" "}
          <span className="thermal-num">
            {trace.panes.map((pane) => value(pane.solar_factor, "", 3)).join(" / ")}
          </span>
        </p>
      )}
      {unique.length > 0 && (
        <details>
          <summary>Informes y alcance</summary>
          {unique.map((source) => (
            <div className="thermal-source" key={source.id}>
              <a href={source.source_url} target="_blank" rel="noreferrer">
                {source.source_document}
              </a>
              <p>
                {source.laboratory} · {formatDate(source.report_date)} · {source.standard} ·{" "}
                {source.source_page}
              </p>
              <p>
                {source.applicability} · vigente hasta {formatDate(source.valid_until)}
              </p>
            </div>
          ))}
        </details>
      )}
    </div>
  );
}

export function PositionThermal({
  projectId,
  orgId,
  positionId,
}: {
  projectId: string;
  orgId: string;
  positionId: string;
}) {
  const query = useThermalReport(projectId, orgId);
  if (query.isPending) return <DimLoader label="Calculando Uw con sus fuentes" />;
  if (query.isError)
    return (
      <p role="alert">
        No se pudo leer el informe térmico.{" "}
        <button onClick={() => void query.refetch()}>Reintentar</button>
      </p>
    );
  const position = query.data.assessment.positions.find((item) => item.position_id === positionId);
  return position ? (
    <section aria-label="Desempeño térmico">
      <ThermalReadout metric={position.thermal} />
      <p>{thermalVerdict[position.verdict]}</p>
      <Link to={`/projects/${projectId}?section=thermal`}>Revisar zona y cumplimiento</Link>
    </section>
  ) : (
    <p>Uw Sin dato · esta revisión no contiene un informe de la posición.</p>
  );
}

export function ProjectThermalPanel({
  project,
  orgId,
  canWrite,
  onChanged,
  onDirtyChange,
}: {
  project: ProjectResponse;
  orgId: string;
  canWrite: boolean;
  onChanged: () => Promise<unknown>;
  onDirtyChange: (dirty: boolean) => void;
}) {
  const query = useThermalReport(project.id, orgId);
  const [draft, setDraft] = useState<ThermalInputRequest | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [candidate, setCandidate] = useState<ThermalCandidate | null>(null);
  const [notice, setNotice] = useState("");
  const operations = useProjectOperations(project, orgId, async () => {
    setCandidate(null);
    await query.refetch();
    return onChanged();
  });
  useEffect(() => {
    onDirtyChange(draft !== null);
    return () => onDirtyChange(false);
  }, [draft, onDirtyChange]);
  const current = draft ?? (query.data?.inputs as ThermalInputRequest | undefined);
  function change(patch: Partial<ThermalInputRequest>) {
    if (current) setDraft({ ...current, ...patch });
    setError("");
  }
  async function save() {
    if (!draft || busy || !query.data) return;
    setBusy(true);
    setError("");
    try {
      const result = await projectThermalSave(
        project.id,
        { inputs: draft, expected_updated_at: query.data.updated_at },
        { headers: { "X-Organization-ID": orgId } },
      );
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      setDraft(null);
      setNotice("Datos térmicos guardados; veredicto recalculado por el motor.");
      await query.refetch();
    } catch (cause) {
      setError(
        actionErrorDetail(
          cause,
          "No se pudieron guardar los datos. Revisa las fuentes y superficies, y vuelve a intentar.",
        ),
      );
    } finally {
      setBusy(false);
    }
  }
  async function find(positionId: string) {
    if (busy) return;
    setBusy(true);
    setError("");
    setCandidate(null);
    setNotice("");
    try {
      const result = await thermalCompliantAlternative(project.id, positionId, {
        headers: { "X-Organization-ID": orgId },
      });
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      setCandidate(result.data.candidate as ThermalCandidate | null);
      setNotice(result.data.reason ?? result.data.scope ?? "");
    } catch (cause) {
      setError(
        actionErrorDetail(
          cause,
          "No se pudo comparar el catálogo. Revisa sus fuentes y tarifas antes de reintentar.",
        ),
      );
    } finally {
      setBusy(false);
    }
  }
  async function propose() {
    if (!candidate) return;
    const target = project.positions?.find(
      (position) => position.id === candidate.assessment.position_id,
    );
    if (!target) return;
    const ops: Record<string, unknown>[] = [];
    if (target.design.system_id !== candidate.system_id)
      ops.push({ op: "set_system", system_id: candidate.system_id });
    ops.push({ op: "set_glass", module: "*", sku: candidate.glass_sku });
    await operations.propose(
      [{ op: "apply_to_positions", filter: { position_ids: [target.id] }, ops }],
      "Alternativa térmica con menor precio que cumple",
    );
  }
  if (query.isPending) return <DimLoader label="Calculando el informe térmico" />;
  if (query.isError)
    return (
      <section role="alert">
        <p>
          {actionErrorDetail(
            query.error,
            "No se pudo cargar el informe térmico. Reintenta la lectura de este proyecto.",
          )}
        </p>
        <Button onClick={() => void query.refetch()}>Reintentar</Button>
      </section>
    );
  const report = query.data;
  const assessment = report.assessment;
  const editable = canWrite && project.status === "DRAFT" && !report.sealed;
  return (
    <section className="thermal-panel" data-density="office" aria-label="Cumplimiento térmico">
      <header className="thermal-heading">
        <div>
          <h2>Ventanas · reglamentación térmica</h2>
          <p>
            {report.sealed
              ? "Informe sellado de esta revisión"
              : "Datos del catálogo vigente y fabricación guardada"}{" "}
            · {report.inputs.zone ? `Zona ${report.inputs.zone}` : "Zona Sin dato"}
          </p>
        </div>
        <strong className="thermal-verdict" data-verdict={assessment.verdict}>
          {thermalVerdict[assessment.verdict]}
        </strong>
      </header>
      <p>{assessment.scope}</p>
      <a href={assessment.source_url} target="_blank" rel="noreferrer">
        {assessment.source_label}
      </a>
      {report.sealed && <p>Para cambiar los datos, inicia una nueva revisión desde Cotización.</p>}
      {!canWrite && (
        <p>
          Solo el dueño o el estimador pueden declarar zona, muros y orientación. Puedes revisar las
          fuentes.
        </p>
      )}
      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}
      {busy && <DimLoader label="Revisando datos y catálogo" />}
      {current && (
        <details open={!report.inputs.zone && !report.sealed} className="thermal-inputs">
          <summary>Zona, envolvente y anexo técnico</summary>
          <ValidatedForm
            noValidate
            onSubmit={(event) => {
              event.preventDefault();
              void save();
            }}
          >
            <fieldset disabled={!editable || busy}>
              <div className="thermal-fields">
                <label>
                  Zona térmica
                  <select
                    value={current.zone ?? ""}
                    onChange={(event) =>
                      change({ zone: (event.target.value || null) as ThermalInputRequest["zone"] })
                    }
                  >
                    <option value="">Sin dato · elige zona</option>
                    {"ABCDEFGHI".split("").map((zone) => (
                      <option key={zone} value={zone}>
                        Zona {zone}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Uso de la unidad
                  <select
                    value={current.use ?? ""}
                    onChange={(event) =>
                      change({ use: (event.target.value || null) as ThermalInputRequest["use"] })
                    }
                  >
                    <option value="">Sin dato · elige uso</option>
                    <option value="RESIDENTIAL">Residencial</option>
                    <option value="EDUCATION">Educación</option>
                    <option value="HEALTH">Salud</option>
                    <option value="HOTEL">Hotel</option>
                  </select>
                </label>
                <label className="thermal-wide">
                  Fuente de la zona
                  <input
                    value={current.zone_source ?? ""}
                    onChange={(event) => change({ zone_source: event.target.value })}
                  />
                  <small>
                    Plano oficial NCh1079 o antecedente del responsable. La comuna no determina la
                    zona automáticamente.
                  </small>
                </label>
              </div>
              {current.use === "RESIDENTIAL" && (
                <>
                  <h3>Muros perimetrales · superficie interior</h3>
                  <p>
                    Incluye vanos y muros medianeros. Todas las ventanas de Oriente y Poniente se
                    evalúan por separado.
                  </p>
                  <div className="thermal-fields">
                    {["N", "E", "S", "W"].map((side) => (
                      <label key={side}>
                        {orientationLabel[side]} · m²
                        <input
                          inputMode="decimal"
                          value={current.walls_m2?.[side] ?? ""}
                          onChange={(event) => {
                            const raw = event.target.value;
                            const walls = { ...current.walls_m2 };
                            if (raw === "") delete walls[side];
                            else walls[side] = raw.replace(",", ".");
                            change({ walls_m2: walls });
                          }}
                        />
                      </label>
                    ))}
                    <label>
                      Parte expuesta al exterior · m²
                      <input
                        inputMode="decimal"
                        value={current.exposed_wall_area_m2 ?? ""}
                        onChange={(event) =>
                          change({
                            exposed_wall_area_m2: event.target.value.replace(",", ".") || null,
                          })
                        }
                      />
                    </label>
                    <label>
                      Fuente de las superficies
                      <input
                        value={current.wall_source ?? ""}
                        onChange={(event) => change({ wall_source: event.target.value })}
                      />
                    </label>
                  </div>
                  <p>
                    Con menos de 60 % del total de muros expuesto, el motor usa orientación global
                    teórica (OGT).
                  </p>
                </>
              )}
              <label className="thermal-check">
                <input
                  type="checkbox"
                  checked={current.envelope_complete ?? false}
                  onChange={(event) => change({ envelope_complete: event.target.checked })}
                />
                Incluí todas las ventanas de esta unidad térmica, sus cantidades y superficies.
              </label>
              <label className="thermal-check">
                <input
                  type="checkbox"
                  checked={current.regulatory_scope_confirmed ?? false}
                  onChange={(event) => change({ regulatory_scope_confirmed: event.target.checked })}
                />
                Confirmé con el responsable que aplica OGUC 4.1.10 y revisé el plan de
                descontaminación local.
              </label>
              <label className="thermal-wide">
                Memoria de cálculo del responsable
                <input
                  value={current.regulatory_calculation_source ?? ""}
                  onChange={(event) =>
                    change({ regulatory_calculation_source: event.target.value })
                  }
                />
                <small>
                  Referencia o URL del documento que coteja el método y todas las posiciones.
                </small>
              </label>
              <label className="thermal-check">
                <input
                  type="checkbox"
                  checked={current.regulatory_method_confirmed ?? false}
                  onChange={(event) =>
                    change({ regulatory_method_confirmed: event.target.checked })
                  }
                />
                El responsable cotejó el cálculo con NCh3137/1 y NCh3137/2. ISO 10077-1 por sí sola
                no acredita OGUC.
              </label>
              <label className="thermal-check">
                <input
                  type="checkbox"
                  checked={current.include_doc01 ?? false}
                  onChange={(event) => change({ include_doc01: event.target.checked })}
                />
                Incluir anexo en DOC-01; imprime únicamente valores autoritativos sellados.
              </label>
              {editable && draft && (
                <div className="thermal-actions">
                  <Button
                    type="submit"
                    variant="primary"
                    disabled={
                      !draft ||
                      Object.values(current.walls_m2 ?? {}).some(
                        (number) => parseDecimalInput(number, 6) === null,
                      )
                    }
                  >
                    Guardar datos y evaluar
                  </Button>
                  <Button type="button" disabled={!draft} onClick={() => setDraft(null)}>
                    Descartar cambios
                  </Button>
                </div>
              )}
            </fieldset>
          </ValidatedForm>
        </details>
      )}
      {assessment.causes.length > 0 && (
        <ul className="thermal-causes">
          {assessment.causes.map((cause) => (
            <li key={cause}>{cause}</li>
          ))}
        </ul>
      )}
      {assessment.positions.length === 0 ? (
        <EmptyState
          title="No hay ventanas evaluables"
          body="Agrega una posición al proyecto para calcular su desempeño."
          action={<Link to={`/projects/${project.id}/positions/new`}>Agregar posición</Link>}
        />
      ) : (
        <div className="thermal-positions">
          {assessment.positions.map((position) => (
            <article key={position.position_id} className="thermal-position">
              <header>
                <Link to={`/projects/${project.id}/positions/${position.position_id}/edit`}>
                  Posición {position.position_index} · {position.location_tag || "Sin ubicación"}
                </Link>
                <span className="thermal-num">Uw {value(position.thermal.uw, "W/m²K")}</span>
                <strong>{thermalVerdict[position.verdict]}</strong>
              </header>
              <details open={assessment.positions.length === 1}>
                <summary>Geometría, orientación y fuentes</summary>
                <div className="thermal-position-body">
                  <ThermalReadout metric={position.thermal} />
                  <div>
                    {current && (
                      <div className="thermal-fields">
                        <label>
                          Ubicación en envolvente
                          <select
                            disabled={!editable || busy}
                            value={
                              current.positions?.find(
                                (item) => item.position_id === position.position_id,
                              )?.surface ?? ""
                            }
                            onChange={(event) =>
                              change({
                                positions: [
                                  ...(current.positions ?? []).filter(
                                    (item) => item.position_id !== position.position_id,
                                  ),
                                  {
                                    position_id: position.position_id,
                                    orientation:
                                      current.positions?.find(
                                        (item) => item.position_id === position.position_id,
                                      )?.orientation ?? null,
                                    surface: (event.target.value || null) as "WALL" | "ROOF" | null,
                                  },
                                ],
                              })
                            }
                          >
                            <option value="">Sin dato · ubica la ventana</option>
                            <option value="WALL">Fachada</option>
                            <option value="ROOF">Techumbre · hasta 60° horizontal</option>
                          </select>
                        </label>
                        <label>
                          Orientación
                          <select
                            disabled={!editable || busy}
                            value={
                              current.positions?.find(
                                (item) => item.position_id === position.position_id,
                              )?.orientation ?? ""
                            }
                            onChange={(event) =>
                              change({
                                positions: [
                                  ...(current.positions ?? []).filter(
                                    (item) => item.position_id !== position.position_id,
                                  ),
                                  {
                                    position_id: position.position_id,
                                    surface:
                                      current.positions?.find(
                                        (item) => item.position_id === position.position_id,
                                      )?.surface ?? null,
                                    orientation: (event.target.value || null) as
                                      "N" | "E" | "S" | "W" | null,
                                  },
                                ],
                              })
                            }
                          >
                            <option value="">Sin dato</option>
                            {["N", "E", "S", "W"].map((side) => (
                              <option value={side} key={side}>
                                {orientationLabel[side]}
                              </option>
                            ))}
                          </select>
                        </label>
                      </div>
                    )}
                    <p className="thermal-num">
                      Área de ventana {value(position.window_area_m2, "m²", 3)} · cantidad{" "}
                      {position.quantity}
                    </p>
                    {position.minimum_air_class != null && (
                      <p>
                        Mínimo de aire ·{" "}
                        <span className="thermal-num">
                          clase {position.minimum_air_class} a 100 Pa
                        </span>
                      </p>
                    )}
                    {position.maximum_uw != null && (
                      <p>
                        Uw máximo{" "}
                        <span className="thermal-num">{value(position.maximum_uw, "W/m²K")}</span>
                      </p>
                    )}
                    {position.group && position.group !== "ROOF" && (
                      <p>
                        {orientationLabel[position.group] ?? "Fachada"} ·{" "}
                        <span className="thermal-num">
                          ventanas{" "}
                          {position.actual_percentage == null
                            ? "Sin dato"
                            : formatPercent(position.actual_percentage, "points")}{" "}
                          · máximo{" "}
                          {position.maximum_percentage == null
                            ? "Sin dato"
                            : formatPercent(position.maximum_percentage, "points")}
                        </span>
                        <br />
                        Gobierna el mayor Uw del grupo.
                      </p>
                    )}
                  </div>
                </div>
                {position.causes.filter((cause) => assessment.causes.includes(cause) === false)
                  .length > 0 && (
                  <ul className="thermal-causes">
                    {position.causes
                      .filter((cause) => !assessment.causes.includes(cause))
                      .map((cause) => (
                        <li key={cause}>{cause}</li>
                      ))}
                  </ul>
                )}
                {editable && position.verdict === "FAIL" && (
                  <Button
                    disabled={busy || !!draft}
                    onClick={() => void find(position.position_id)}
                  >
                    Buscar alternativa que cumple
                  </Button>
                )}
              </details>
            </article>
          ))}
        </div>
      )}
      {candidate && (
        <section className="thermal-alternative" aria-label="Alternativa que cumple">
          <h3>Menor precio que cumple · {candidate.system_name}</h3>
          <p>
            Posición {candidate.assessment.position_index} · {candidate.assessment.location_tag}.
            Conserva medidas, apertura, color y cantidad.
          </p>
          <ThermalReadout metric={candidate.assessment.thermal} />
          <p className="thermal-num">
            Precio neto indicativo {formatMoney(candidate.price.net, candidate.price.currency)} · Δ{" "}
            {formatMoney(candidate.delta_net, candidate.price.currency)}
          </p>
          <p>{candidate.price.source}</p>
          <Button disabled={busy || !!draft || operations.busy} onClick={() => void propose()}>
            Preparar cambio para revisar
          </Button>
          <Button onClick={() => setCandidate(null)}>Descartar alternativa</Button>
        </section>
      )}
      <ProjectOpsReview
        operations={operations}
        orgId={orgId}
        currency={project.currency ?? "CLP"}
      />
      <p>
        <Link to="/catalogs/systems">Completar informes del catálogo</Link>
      </p>
    </section>
  );
}
