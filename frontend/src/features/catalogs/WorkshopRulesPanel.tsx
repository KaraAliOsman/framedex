import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import {
  catalogSeriesConfirmWorkshopRules,
  catalogSeriesWorkshopRules,
} from "../../api/generated/dekopen";
import type { WorkshopRules } from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { Button, Loading, NumberField, StatusBadge } from "../../ui";
import "./workshop-rules.css";

type Params = Record<string, Record<string, string | number>>;

const ROLE_LABELS: Record<string, string> = {
  FRAME: "Marco",
  SASH: "Hoja",
  MULLION_V: "Travesaño vertical",
  MULLION_H: "Travesaño horizontal",
  DOOR_SASH: "Hoja de puerta",
  THRESHOLD: "Umbral",
};

/** Plain-language name of each inspector rule and of every value it reads. */
const RULES: { id: string; title: string; fields: [string, string, number][] }[] = [
  { id: "R01", title: "Carga de la hoja", fields: [] },
  {
    id: "R02",
    title: "Proporción de la hoja",
    fields: [
      ["min_ratio", "Alto ÷ ancho mínimo", 4],
      ["max_ratio", "Alto ÷ ancho máximo", 4],
      ["suggested_ratio", "Proporción sugerida", 4],
    ],
  },
  {
    id: "R03",
    title: "Medidas de la hoja",
    fields: [
      ["min_width_mm", "Ancho mínimo (mm)", 2],
      ["max_width_mm", "Ancho máximo (mm)", 2],
      ["max_height_mm", "Alto máximo (mm)", 2],
    ],
  },
  {
    id: "R08",
    title: "Puntos de cierre",
    fields: [["max_spacing_mm", "Separación máxima (mm)", 2]],
  },
  {
    id: "R13",
    title: "Compases de la proyectante",
    fields: [
      ["height_trigger_mm", "Desde un alto de (mm)", 2],
      ["required_stay_arms", "Compases", 0],
    ],
  },
  {
    id: "R04",
    title: "Área del vidrio",
    fields: [
      ["monolithic_4_max_area_m2", "Vidrio simple 4 mm, máx. (m²)", 4],
      ["dvh_4_any_4_max_area_m2", "Termopanel 4 + cámara + 4, máx. (m²)", 4],
    ],
  },
  { id: "R06", title: "Junquillo para el espesor del vidrio", fields: [] },
  {
    id: "R05",
    title: "Refuerzo del travesaño",
    fields: [["span_trigger_mm", "Revisar desde una luz de (mm)", 2]],
  },
  {
    id: "R07",
    title: "Desagües inferiores",
    fields: [
      ["width_trigger_mm", "Desde un ancho de (mm)", 2],
      ["required_bottom_drains", "Desagües", 0],
    ],
  },
  {
    id: "R09",
    title: "Dilatación del conjunto",
    fields: [
      ["white_limit_mm", "Tramo máximo en blanco (mm)", 2],
      ["foiled_limit_mm", "Tramo máximo foliado (mm)", 2],
    ],
  },
  { id: "R10", title: "Escuadra del marco", fields: [["tolerance_mm", "Tolerancia (mm)", 2]] },
  {
    id: "R11",
    title: "Holgura de cámara",
    fields: [
      ["expected_mm", "Esperada (mm)", 2],
      ["tolerance_mm", "Tolerancia (mm)", 2],
      ["suggested_sash_overlap_mm", "Traslape sugerido (mm)", 2],
    ],
  },
  {
    id: "R12",
    title: "Refuerzo de corredera triple",
    fields: [
      ["width_trigger_mm", "Desde un ancho de (mm)", 2],
      ["minimum_ix_cm4", "Inercia mínima (cm⁴)", 4],
    ],
  },
  {
    id: "R14",
    title: "Carros de monoriel",
    fields: [
      ["weight_trigger_kg", "Desde un peso de (kg)", 2],
      ["required_carriages", "Carros", 0],
      ["minimum_capacity_kg", "Capacidad por carro (kg)", 2],
    ],
  },
];

const NO_VALUES: Record<string, string> = {
  R01: "Se revisa con el peso de la hoja y la carga de su herraje.",
  R06: "Se revisa con la tabla de junquillos de la serie.",
};

function angle(value: unknown): string {
  return `${String(value).replace(/\.0+$/, "")}°`;
}

const ROLE_ORDER = ["FRAME", "SASH", "DOOR_SASH", "MULLION_V", "MULLION_H", "THRESHOLD"];

/** «Marco» → «45° / 45° · 45° / 90°»: the profile cuts that carry steel, per role. */
function reinforcementByRole(rules: WorkshopRules["reinforcement_rules"]): [string, string[]][] {
  const grouped = new Map<string, string[]>();
  for (const rule of rules) {
    const role = String(rule.role);
    grouped.set(role, [
      ...(grouped.get(role) ?? []),
      `${angle(rule.profile_angle_left)} / ${angle(rule.profile_angle_right)}`,
    ]);
  }
  const rank = (role: string) => ROLE_ORDER.indexOf(role) + 1 || ROLE_ORDER.length + 1;
  return [...grouped].sort(([left], [right]) => rank(left) - rank(right));
}

export function WorkshopRulesPanel({
  orgId,
  systemId,
  writable,
}: {
  orgId: string;
  systemId: string;
  writable: boolean;
}): JSX.Element {
  const queryClient = useQueryClient();
  const options = { headers: { "X-Organization-ID": orgId } };
  const queryKey = ["series-workshop-rules", orgId, systemId];
  const query = useQuery({
    queryKey,
    queryFn: async ({ signal }) => {
      const response = await catalogSeriesWorkshopRules(systemId, { ...options, signal });
      if (response.status !== 200) throw new Error("rules");
      return response.data;
    },
    refetchOnWindowFocus: false,
  });
  const [clearance, setClearance] = useState("");
  const [inspector, setInspector] = useState<Params>({});
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ tone: "ok" | "error"; text: string } | null>(null);

  useEffect(() => {
    if (!query.data) return;
    setClearance(query.data.chamber_clearance_mm);
    setInspector(query.data.inspector as Params);
  }, [query.data]);

  if (query.isPending) return <Loading label="Cargando las reglas de taller" />;
  if (query.isError)
    return (
      <p role="alert">No se pudieron cargar las reglas de taller. Vuelve a abrir la pestaña.</p>
    );
  const rules: WorkshopRules = query.data;
  const confirmed = rules.state === "CONFIRMED";
  const complete =
    clearance !== "" &&
    RULES.every((rule) =>
      rule.fields.every(([field]) => String(inspector[rule.id]?.[field] ?? "") !== ""),
    );

  async function confirm() {
    setBusy(true);
    setMessage(null);
    try {
      const response = await catalogSeriesConfirmWorkshopRules(
        systemId,
        {
          chamber_clearance_mm: clearance,
          inspector,
          reinforcement_rules: rules.reinforcement_rules,
          bead_offsets: rules.bead_offsets,
        },
        options,
      );
      if (response.status !== 200) throw new Error("confirm");
      queryClient.setQueryData(queryKey, response.data);
      void queryClient.invalidateQueries({ queryKey: ["series-sheet", orgId, systemId] });
      setMessage({
        tone: "ok",
        text: `Reglas confirmadas (versión ${response.data.version}). Ya puedes preparar la OT de las obras con esta serie.`,
      });
    } catch (error) {
      setMessage({
        tone: "error",
        text:
          error instanceof ApiError && error.status === 409
            ? "Esta serie ya se usa en obras: lo que ya tenía declarado no cambia. Crea una versión nueva de la serie para cambiarlo."
            : "No se pudieron guardar. Revisa que cada valor sea mayor que cero.",
      });
    } finally {
      setBusy(false);
    }
  }

  function update(rule: string, field: string, value: string) {
    setInspector((current) => ({ ...current, [rule]: { ...current[rule], [field]: value } }));
  }

  return (
    <section className="workshop-rules" aria-label="Reglas de taller">
      <header className="workshop-rules__head">
        <div>
          <h2>Reglas de taller</h2>
          <p>
            Con estas reglas DEKOPEN imprime la orden de trabajo, la optimización de corte y el
            checklist de materiales de las obras hechas con esta serie.
          </p>
        </div>
        <StatusBadge tone={confirmed ? "success" : "warning"}>
          {confirmed ? `Confirmadas · versión ${rules.version}` : "Por confirmar"}
        </StatusBadge>
      </header>

      <div className="workshop-rules__grid">
        <article className="workshop-rules__card">
          <h3>Herraje</h3>
          <label className="workshop-rules__field">
            <span>Holgura de cámara (mm)</span>
            <NumberField
              aria-label="Holgura de cámara en milímetros"
              value={clearance}
              onValueChange={setClearance}
              disabled={!writable || busy}
            />
          </label>
          <p className="workshop-rules__source">
            Aire entre hoja y marco donde va el herraje. Confírmalo con la ficha del fabricante.
          </p>
          <p className="workshop-rules__source">{rules.sources.handles}</p>
        </article>

        <article className="workshop-rules__card">
          <h3>Refuerzos</h3>
          {rules.pending_reinforcement ? (
            <p>Esta serie todavía no declara aceros. Agrégalos en Perfiles.</p>
          ) : (
            <ul className="workshop-rules__list">
              {reinforcementByRole(rules.reinforcement_rules).map(([role, cuts]) => (
                <li key={role}>
                  <strong>{ROLE_LABELS[role] ?? role}</strong>
                  <span>{cuts.join(" · ")}</span>
                </li>
              ))}
            </ul>
          )}
          <p className="workshop-rules__source">{rules.sources.reinforcement}</p>
        </article>

        <article className="workshop-rules__card">
          <h3>Junquillos</h3>
          <p>{rules.sources.beads}</p>
        </article>
      </div>

      <div className="workshop-rules__inspection">
        <h3>Revisión antes de fabricar</h3>
        <p className="workshop-rules__source">{rules.sources.inspector}</p>
        <div className="workshop-rules__rules">
          {RULES.map((rule) => (
            <fieldset key={rule.id} className="workshop-rules__rule">
              <legend>{rule.title}</legend>
              {rule.fields.length === 0 ? (
                <p>{NO_VALUES[rule.id]}</p>
              ) : (
                rule.fields.map(([field, label, decimals]) => (
                  <label key={field} className="workshop-rules__field">
                    <span>{label}</span>
                    <NumberField
                      aria-label={`${rule.title}: ${label}`}
                      decimals={decimals}
                      value={String(inspector[rule.id]?.[field] ?? "")}
                      onValueChange={(value) => update(rule.id, field, value)}
                      disabled={!writable || busy}
                    />
                  </label>
                ))
              )}
            </fieldset>
          ))}
        </div>
      </div>

      {message && (
        <p role={message.tone === "error" ? "alert" : "status"} className="workshop-rules__message">
          {message.text}
        </p>
      )}
      {writable && (
        <div className="workshop-rules__actions">
          <Button variant="primary" disabled={busy || !complete} onClick={() => void confirm()}>
            {confirmed ? "Guardar nueva versión" : "Confirmar reglas de taller"}
          </Button>
        </div>
      )}
    </section>
  );
}
