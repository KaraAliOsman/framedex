import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  catalogThermalReports,
  catalogThermalDeclare,
  catalogThermalReview,
} from "../../api/generated/dekopen";
import type { ThermalAuthorityRequest } from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { formatDate, formatDecimal, fmtMm, parseDecimalInput } from "../../format";
import { domainLabel } from "../../i18n/domainLabels";
import { Button, DemoBadge, Loading, ValidatedForm, useConfirm } from "../../ui";
import { actionErrorDetail } from "../errors";
import type { ThermalSource } from "../projects/thermalModel";
import "../projects/thermal.css";

type Report = ThermalSource &
  ThermalAuthorityRequest & {
    review_state: "PENDING" | "REVIEWED" | "REJECTED" | "REVOKED";
    reviewed_at: string | null;
    reviewer_label: string | null;
  };
type CatalogData = {
  is_demo: boolean;
  profiles: { sku: string; name: string; role: string }[];
  glasses: { sku: string; name: string; spacer: string | null; synthetic: boolean }[];
  specimens: { id: string; label: string }[];
  items: Report[];
};
const kinds = {
  FRAME: "Uf · combinación de perfiles",
  GLASS: "Ug y factor solar · vidrio",
  SPACER: "Ψg · separador y perfiles",
  PERFORMANCE: "Aire, agua y viento · sistema",
};
const openings = [
  "FIXED",
  "TURN_LEFT",
  "TURN_RIGHT",
  "TILT_TURN_LEFT",
  "TILT_TURN_RIGHT",
  "AWNING",
  "SLIDING_2L",
  "SLIDING_3L",
  "SLIDING_4L",
  "SLIDING",
  "DOOR_ENTRY",
  "DOOR_DOUBLE",
];
function fresh(kind: ThermalAuthorityRequest["kind"] = "FRAME"): ThermalAuthorityRequest {
  return {
    kind,
    profile_skus: [],
    opening_types: [],
    min_width_mm: "",
    max_width_mm: "",
    min_height_mm: "",
    max_height_mm: "",
    source_document: "",
    source_url: "",
    source_page: "",
    laboratory: "",
    laboratory_registration: "",
    report_date: "",
    valid_until: "",
    standard: "",
    applicability: "",
    synthetic: false,
  };
}

export function ThermalCatalogPanel({ systemId }: { systemId: string }) {
  const { me } = useAuthSession();
  const org = me?.active_organization;
  const canManage = !!org && ["OWNER", "WORKSHOP_MANAGER"].includes(org.role);
  const query = useQuery({
    queryKey: ["thermal-catalog", org?.id, systemId],
    enabled: !!org,
    queryFn: async ({ signal }) => {
      const result = await catalogThermalReports(systemId, {
        signal,
        headers: { "X-Organization-ID": org!.id },
      });
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      return result.data as unknown as CatalogData;
    },
  });
  const [draft, setDraft] = useState<ThermalAuthorityRequest | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const confirm = useConfirm();
  function change(patch: Partial<ThermalAuthorityRequest>) {
    if (draft) setDraft({ ...draft, ...patch });
    setError("");
  }
  async function save() {
    if (!draft || !org || busy) return;
    setBusy(true);
    setError("");
    try {
      const result = await catalogThermalDeclare(systemId, draft, {
        headers: { "X-Organization-ID": org.id },
      });
      if (result.status !== 201) throw new ApiError(result.status, result.data);
      setDraft(null);
      await query.refetch();
    } catch (cause) {
      setError(
        actionErrorDetail(
          cause,
          "No se pudo registrar el informe. Revisa sus valores, fechas y alcance antes de reintentar.",
        ),
      );
    } finally {
      setBusy(false);
    }
  }
  async function review(report: Report, state: "REVIEWED" | "REJECTED" | "REVOKED") {
    if (!org || busy) return;
    const approved = await confirm({
      title:
        state === "REVOKED"
          ? "Revocar este informe"
          : state === "REJECTED"
            ? "Rechazar este informe"
            : "Confirmar revisión técnica",
      body:
        state === "REVIEWED"
          ? "Declaro que cotejé los valores con el documento original, la inscripción vigente del laboratorio, vigencia, norma y alcance exacto. La revisión no certifica datos de ejemplo."
          : "El informe deja de servir para cálculos nuevos. Las revisiones emitidas conservan los documentos que se usaron al emitir.",
      confirmLabel:
        state === "REVIEWED"
          ? "Confirmar revisión"
          : state === "REVOKED"
            ? "Revocar informe"
            : "Rechazar informe",
    });
    if (!approved) return;
    setBusy(true);
    setError("");
    try {
      const result = await catalogThermalReview(
        systemId,
        report.id,
        { state, confirmed: true },
        { headers: { "X-Organization-ID": org.id } },
      );
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      await query.refetch();
    } catch (cause) {
      setError(
        actionErrorDetail(cause, "La revisión no se pudo guardar. Recarga el informe y reintenta."),
      );
    } finally {
      setBusy(false);
    }
  }
  if (query.isPending) return <Loading label="Leyendo informes térmicos" />;
  if (query.isError)
    return (
      <section role="alert">
        <p>
          {actionErrorDetail(
            query.error,
            "No se pudieron leer los informes del sistema. Reintenta la consulta.",
          )}
        </p>
        <Button onClick={() => void query.refetch()}>Reintentar</Button>
      </section>
    );
  const data = query.data;
  const numeric: [keyof ThermalAuthorityRequest, string][] =
    draft?.kind === "FRAME"
      ? [["uf", "Uf · W/m²K"]]
      : draft?.kind === "GLASS"
        ? [
            ["ug", "Ug · W/m²K"],
            ["solar_factor", "Factor solar g · 0 a 1"],
          ]
        : draft?.kind === "SPACER"
          ? [["psi_g", "Ψg · W/mK"]]
          : [];
  const missing =
    draft &&
    ([
      "source_document",
      "source_url",
      "source_page",
      "laboratory",
      "report_date",
      "valid_until",
      "standard",
      "applicability",
      "min_width_mm",
      "max_width_mm",
      "min_height_mm",
      "max_height_mm",
    ].some((key) => !draft[key as keyof ThermalAuthorityRequest]) ||
      !draft.opening_types.length ||
      (draft.kind !== "GLASS" && !draft.profile_skus?.length));
  return (
    <section
      className="thermal-panel"
      aria-label="Informes térmicos del catálogo"
      data-density="office"
    >
      <header className="thermal-heading">
        <div>
          <h3>Informes térmicos y prestaciones</h3>
          <p>
            El informe original no se puede cambiar. Cada corrección se registra como un informe
            nuevo; la revisión estampa al actor en el servidor.
          </p>
        </div>
        {canManage && !draft && (
          <Button onClick={() => setDraft(fresh())}>Registrar informe</Button>
        )}
      </header>
      {data.is_demo && (
        <p>
          <DemoBadge /> Catálogo sintético. Ninguna revisión puede convertirlo en certificado.
        </p>
      )}
      {!canManage && (
        <p>
          El dueño o el encargado de taller registran y revisan estos informes. Puedes consultar su
          alcance.
        </p>
      )}
      {error && <p role="alert">{error}</p>}
      {busy && <Loading label="Guardando evidencia revisada" />}
      {draft && (
        <ValidatedForm
          noValidate
          onSubmit={(event) => {
            event.preventDefault();
            void save();
          }}
        >
          <fieldset disabled={busy} className="thermal-inputs">
            <legend>Documento original y alcance</legend>
            <div className="thermal-fields">
              <label>
                Dato del informe
                <select
                  value={draft.kind}
                  onChange={(event) =>
                    setDraft(fresh(event.target.value as ThermalAuthorityRequest["kind"]))
                  }
                >
                  {Object.entries(kinds).map(([key, label]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              {(draft.kind === "GLASS" || draft.kind === "SPACER") && (
                <label>
                  Vidrio
                  <select
                    value={draft.glass_sku ?? ""}
                    onChange={(event) => {
                      const glass = data.glasses.find((item) => item.sku === event.target.value);
                      change({
                        glass_sku: glass?.sku ?? null,
                        ...(draft.kind === "SPACER" ? { spacer_code: glass?.spacer ?? null } : {}),
                      });
                    }}
                  >
                    <option value="">Elige una composición</option>
                    {data.glasses.map((glass) => (
                      <option key={glass.sku} value={glass.sku}>
                        {glass.name}
                        {glass.synthetic ? " · Ejemplo" : ""}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              {numeric.map(([key, label]) => (
                <label key={key}>
                  {label}
                  <input
                    inputMode="decimal"
                    value={(draft[key as keyof ThermalAuthorityRequest] as string | null) ?? ""}
                    onChange={(event) =>
                      change({ [key]: event.target.value.replace(",", ".") || null })
                    }
                  />
                </label>
              ))}
              {draft.kind === "SPACER" && (
                <p>
                  Separador de la receta:{" "}
                  {draft.spacer_code === "WARM_EDGE"
                    ? "Borde cálido"
                    : draft.spacer_code === "ALUMINIUM"
                      ? "Aluminio"
                      : draft.spacer_code === "NONE"
                        ? "Sin cámara"
                        : "Falta · completa la composición del vidrio"}
                </p>
              )}
              {draft.kind === "PERFORMANCE" && (
                <>
                  <label className="thermal-wide">
                    Producto ensayado · ventana que reproduce el informe
                    <select
                      value={draft.source_position_id ?? ""}
                      onChange={(event) =>
                        change({ source_position_id: event.target.value || null })
                      }
                    >
                      <option value="">Elige el producto ensayado</option>
                      {data.specimens.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.label}
                        </option>
                      ))}
                    </select>
                    <small>
                      Debe coincidir en medidas, vidrio, herrajes y distribución. Otro producto
                      necesita su propio ensayo.
                    </small>
                  </label>
                  <p className="thermal-wide">
                    Para aire: ensayo NCh3297, clasificación NCh3296 e inscripción vigente del
                    laboratorio en el registro MINVU.
                  </p>
                  <label>
                    Aire · clase a 100 Pa
                    <select
                      value={draft.air_class ?? ""}
                      onChange={(event) =>
                        change({
                          air_class: event.target.value === "" ? null : Number(event.target.value),
                          air_pressure_pa: event.target.value === "" ? null : "100",
                        })
                      }
                    >
                      <option value="">Completar</option>
                      {[0, 1, 2, 3, 4].map((value) => (
                        <option key={value} value={value}>
                          Clase {value}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Clase de agua
                    <input
                      value={draft.water_class ?? ""}
                      onChange={(event) => change({ water_class: event.target.value || null })}
                    />
                  </label>
                  <label>
                    Clase de viento
                    <input
                      value={draft.wind_class ?? ""}
                      onChange={(event) => change({ wind_class: event.target.value || null })}
                    />
                  </label>
                </>
              )}
              {(
                [
                  ["source_document", "Informe o certificado"],
                  ["source_url", "URL del documento original"],
                  ["source_page", "Página o apartado"],
                  ["laboratory", "Laboratorio o entidad emisora"],
                  ["laboratory_registration", "Inscripción vigente MINVU · referencia o URL"],
                  ["standard", "Norma y edición"],
                ] as const
              ).map(([key, label]) => (
                <label key={key}>
                  {label}
                  <input
                    value={draft[key as keyof ThermalAuthorityRequest] as string}
                    onChange={(event) => change({ [key]: event.target.value })}
                  />
                </label>
              ))}
              <label>
                Fecha del informe
                <input
                  type="date"
                  value={draft.report_date}
                  onChange={(event) => change({ report_date: event.target.value })}
                />
              </label>
              <label>
                Vigente hasta · referencia explícita
                <input
                  type="date"
                  value={draft.valid_until}
                  onChange={(event) => change({ valid_until: event.target.value })}
                />
              </label>
              {(
                [
                  ["min_width_mm", "Ancho mínimo · mm"],
                  ["max_width_mm", "Ancho máximo · mm"],
                  ["min_height_mm", "Alto mínimo · mm"],
                  ["max_height_mm", "Alto máximo · mm"],
                ] as const
              ).map(([key, label]) => (
                <label key={key}>
                  {label}
                  <input
                    inputMode="decimal"
                    value={draft[key as keyof ThermalAuthorityRequest] as string}
                    onChange={(event) => change({ [key]: event.target.value.replace(",", ".") })}
                  />
                </label>
              ))}
              <label className="thermal-wide">
                Alcance literal del documento
                <textarea
                  value={draft.applicability}
                  onChange={(event) => change({ applicability: event.target.value })}
                />
                <small>
                  No extiendas un ensayo a medidas, aperturas o perfiles que su informe no cubre.
                </small>
              </label>
            </div>
            {draft.kind !== "GLASS" && (
              <fieldset>
                <legend>Combinación exacta de perfiles del informe</legend>
                <div className="thermal-fields">
                  {data.profiles
                    .filter(
                      (profile) =>
                        !["GLAZING_BEAD", "ADDITIONAL", "COVER_TRIM", "SILL", "PLINTH"].includes(
                          profile.role,
                        ),
                    )
                    .map((profile) => (
                      <label key={profile.sku} className="thermal-check">
                        <input
                          type="checkbox"
                          checked={draft.profile_skus?.includes(profile.sku) ?? false}
                          onChange={(event) =>
                            change({
                              profile_skus: event.target.checked
                                ? [...(draft.profile_skus ?? []), profile.sku]
                                : (draft.profile_skus ?? []).filter((sku) => sku !== profile.sku),
                            })
                          }
                        />
                        {profile.name}
                      </label>
                    ))}
                </div>
              </fieldset>
            )}
            <fieldset>
              <legend>Aperturas cubiertas por el documento</legend>
              <div className="thermal-fields">
                {openings.map((opening) => (
                  <label key={opening} className="thermal-check">
                    <input
                      type="checkbox"
                      checked={draft.opening_types.includes(opening)}
                      onChange={(event) =>
                        change({
                          opening_types: event.target.checked
                            ? [...draft.opening_types, opening]
                            : draft.opening_types.filter((value) => value !== opening),
                        })
                      }
                    />
                    {domainLabel(opening)}
                  </label>
                ))}
              </div>
            </fieldset>
            <label className="thermal-check">
              <input
                type="checkbox"
                checked={draft.synthetic ?? false}
                onChange={(event) => change({ synthetic: event.target.checked })}
              />
              Dato sintético de prueba; no permite afirmar cumplimiento.
            </label>
            <div className="thermal-actions">
              <Button
                variant="primary"
                type="submit"
                disabled={
                  !!missing ||
                  (draft.kind === "PERFORMANCE" && !draft.source_position_id) ||
                  numeric.some(
                    ([key]) =>
                      parseDecimalInput(
                        (draft[key as keyof ThermalAuthorityRequest] as string) ?? "",
                        6,
                      ) === null,
                  )
                }
              >
                Registrar pendiente de revisión
              </Button>
              <Button type="button" onClick={() => setDraft(null)}>
                Descartar informe
              </Button>
            </div>
          </fieldset>
        </ValidatedForm>
      )}
      {data.items.length === 0 && (
        <p>
          No hay informes registrados. Completa Uf, Ug, separador y clase de aire con documentos
          originales antes de afirmar cumplimiento.
        </p>
      )}
      {data.items.map((report) => (
        <article className="thermal-position" key={report.id}>
          <header>
            <strong>{kinds[report.kind]}</strong>
            <span>
              {report.synthetic ? "Ejemplo · " : ""}
              {
                {
                  PENDING: "Pendiente de revisión",
                  REVIEWED: "Revisado",
                  REJECTED: "Rechazado",
                  REVOKED: "Revocado",
                }[report.review_state]
              }
            </span>
          </header>
          <p className="thermal-num">
            {[
              ["Uf", report.uf, "W/m²K"],
              ["Ug", report.ug, "W/m²K"],
              ["g", report.solar_factor, ""],
              ["Ψg", report.psi_g, "W/mK"],
            ]
              .filter(([, number]) => number != null)
              .map(
                ([label, number, unit]) =>
                  `${label} ${formatDecimal(number!, label === "Ψg" ? 3 : 2)} ${unit}`,
              )
              .join(" · ")}
            {report.air_class != null ? `Aire · clase ${report.air_class} a 100 Pa` : ""}
            {report.water_class ? ` · Agua ${report.water_class}` : ""}
            {report.wind_class ? ` · Viento ${report.wind_class}` : ""}
          </p>
          <p>
            <a href={report.source_url} target="_blank" rel="noreferrer">
              {report.source_document}
            </a>{" "}
            · {report.laboratory} · {formatDate(report.report_date)} · {report.source_page} ·{" "}
            {report.standard}
          </p>
          <p className="thermal-num">
            Alcance {fmtMm(report.min_width_mm)}–{fmtMm(report.max_width_mm)} ×{" "}
            {fmtMm(report.min_height_mm)}–{fmtMm(report.max_height_mm)} mm · hasta{" "}
            {formatDate(report.valid_until)}
          </p>
          <p>{report.applicability}</p>
          <p>
            {report.reviewer_label
              ? `Revisó ${report.reviewer_label}`
              : "Falta indicar quién revisó"}{" "}
            · {report.reviewed_at ? formatDate(report.reviewed_at) : "Pendiente"}
          </p>
          <details>
            <summary>Combinación y aperturas</summary>
            <p>
              {data.profiles
                .filter((profile) => report.profile_skus?.includes(profile.sku))
                .map((profile) => profile.name)
                .join(" · ") || "Vidrio, sin combinación de perfiles"}
            </p>
            <p>{report.opening_types.map(domainLabel).join(" · ")}</p>
          </details>
          {canManage && report.review_state === "PENDING" && (
            <div className="thermal-actions">
              <Button disabled={busy} onClick={() => void review(report, "REVIEWED")}>
                Revisar y confirmar
              </Button>
              <Button disabled={busy} onClick={() => void review(report, "REJECTED")}>
                Rechazar
              </Button>
            </div>
          )}
          {canManage && report.review_state === "REVIEWED" && (
            <Button disabled={busy} onClick={() => void review(report, "REVOKED")}>
              Revocar informe
            </Button>
          )}
        </article>
      ))}
    </section>
  );
}
