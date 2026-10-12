import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  engineSystems,
  mountingRules,
  mountingRuleSave,
  projectDesignOptions,
} from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import { fmtMm } from "../../format";
import { parseDecimalInput } from "../../decimal";
import { actionErrorDetail } from "../errors";
import { mountingKinds, type Allowance, type MountingRule, type RuleRecord } from "./mountingModel";
import { sideLabels, type ExtraDefinition } from "./extraModel";
import "./mounting.css";

const sides = [
  ["left", "Izquierda"],
  ["right", "Derecha"],
  ["bottom", "Inferior"],
  ["top", "Superior"],
] as const;
const fields = [
  ["clearance_mm", "Holgura"],
  ["frame_mm", "Premarco o marco existente"],
  ["extension_mm", "Ensanche"],
  ["overlap_mm", "Traslape"],
] as const;
function newRule(code: string): MountingRule {
  const side = { clearance_mm: "0", frame_mm: "0", extension_mm: "0", overlap_mm: "0" };
  return {
    code,
    name: "",
    kind: "IN_OPENING",
    source: "",
    synthetic: false,
    tolerance_mm: "",
    left: { ...side },
    right: { ...side },
    top: { ...side },
    bottom: { ...side },
    extras: [],
  };
}
export function MountingRulesSettings({ orgId, canWrite }: { orgId: string; canWrite: boolean }) {
  const [system, setSystem] = useState(""),
    [draft, setDraft] = useState<MountingRule | null>(null),
    [review, setReview] = useState(false);
  const [reason, setReason] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [previous, setPrevious] = useState<MountingRule | null>(null);
  const opts = { headers: { "X-Organization-ID": orgId } };
  const systems = useQuery({
    queryKey: ["mounting-systems", orgId],
    queryFn: async () => {
      const r = await engineSystems(opts);
      if (r.status !== 200) throw new ApiError(r.status, r.data);
      return r.data.systems;
    },
  });
  const query = useQuery({
    queryKey: ["mounting-rules", orgId, system],
    enabled: Boolean(system),
    queryFn: async () => {
      const r = await mountingRules(system, opts);
      if (r.status !== 200) throw new ApiError(r.status, r.data);
      return r.data.items as RuleRecord[];
    },
  });
  const catalog = useQuery({
    queryKey: ["mounting-extra-options", orgId, system],
    enabled: Boolean(system),
    queryFn: async () => {
      const r = await projectDesignOptions(system, opts);
      if (r.status !== 200) throw new ApiError(r.status, r.data);
      return r.data.extra_definitions as ExtraDefinition[];
    },
  });
  const current = query.data?.find((item) => item.rule.code === draft?.code);
  const edit = (next: MountingRule) => {
    setDraft(next);
    setReview(false);
    setError("");
  };
  async function save(rule: MountingRule, note = reason) {
    setBusy(true);
    setError("");
    try {
      const normalize = (s: Allowance) =>
        Object.fromEntries(
          fields.map(([key]) => {
            const v = parseDecimalInput(s[key]);
            if (v === null)
              throw new Error("Declara todas las holguras en milímetros, con hasta dos decimales.");
            return [key, v];
          }),
        ) as Allowance;
      const tolerance = parseDecimalInput(rule.tolerance_mm);
      if (tolerance === null) throw new Error("Declara la tolerancia en milímetros.");
      const normalized = {
        ...rule,
        tolerance_mm: tolerance,
        ...Object.fromEntries(sides.map(([key]) => [key, normalize(rule[key])])),
      };
      const r = await mountingRuleSave(
        system,
        {
          rule: normalized,
          expected_revision:
            query.data?.find((item) => item.rule.code === rule.code)?.revision ?? 0,
          reason: note,
        },
        opts,
      );
      if (r.status !== 200) throw new ApiError(r.status, r.data);
      setPrevious(current?.rule ?? null);
      setDraft(null);
      setReview(false);
      setReason("");
      await query.refetch();
    } catch (cause) {
      setError(
        actionErrorDetail(cause, "No pudimos guardar. Revisa la regla, su fuente y el motivo."),
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="settings-group mounting-settings" aria-label="Vano y montaje">
      <h2>Vano y montaje</h2>
      <p>
        Reglas de esta organización por serie. Cada cambio crea una autoridad nueva; las medidas ya
        guardadas conservan su regla exacta.
      </p>
      {!canWrite && (
        <p>El dueño o encargado declara las holguras y accesorios. Puedes consultar las reglas.</p>
      )}
      {systems.isPending ? (
        <p role="status">Cargando series…</p>
      ) : systems.isError ? (
        <p role="alert">
          No pudimos cargar las series.{" "}
          <button onClick={() => void systems.refetch()}>Reintentar</button>
        </p>
      ) : (
        <label>
          Serie de perfiles
          <select
            value={system}
            onChange={(e) => {
              setSystem(e.target.value);
              setDraft(null);
              setPrevious(null);
              setError("");
            }}
          >
            <option value="">Elige una serie</option>
            {systems.data?.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
                {s.is_demo ? " · DEMO" : ""}
              </option>
            ))}
          </select>
        </label>
      )}
      {system &&
        (query.isPending ? (
          <p role="status">Cargando montajes…</p>
        ) : query.isError ? (
          <p role="alert">
            No pudimos cargar los montajes.{" "}
            <button onClick={() => void query.refetch()}>Reintentar</button>
          </p>
        ) : (
          <>
            {!query.data?.length && (
              <p>
                Sin dato: todavía no se declaró un montaje para esta serie. No se aplica ninguna
                holgura silenciosa.
              </p>
            )}
            {query.data?.map((item) => (
              <div className="mounting-rule-row" key={item.rule.code}>
                <p>
                  <strong>{item.rule.name}</strong>
                  {item.rule.synthetic ? " · DEMO" : ""} · autoridad {item.revision}
                </p>
                <p>
                  Holguras:{" "}
                  {sides
                    .map(
                      ([key, label]) =>
                        `${label.toLowerCase()} ${fmtMm(item.rule[key].clearance_mm)} mm`,
                    )
                    .join(" · ")}
                  . Fuente: {item.rule.source}
                </p>
                {canWrite && (
                  <button disabled={busy} onClick={() => edit(item.rule)}>
                    Revisar regla
                  </button>
                )}
              </div>
            ))}
            {canWrite && !draft && (
              <button disabled={busy} onClick={() => edit(newRule(`MOUNT_${Date.now()}`))}>
                Declarar montaje
              </button>
            )}
            {previous && !draft && (
              <button
                disabled={busy}
                onClick={() =>
                  void save(previous, "Deshacer cambio de montaje; restaurar autoridad anterior")
                }
              >
                Deshacer último cambio
              </button>
            )}
            {draft && (
              <fieldset className="mounting-rule-editor" disabled={busy}>
                <div className="mounting-grid">
                  <label>
                    Nombre del montaje
                    <input
                      value={draft.name}
                      onChange={(e) => edit({ ...draft, name: e.target.value })}
                    />
                  </label>
                  <label>
                    Tipo
                    <select
                      value={draft.kind}
                      onChange={(e) =>
                        edit({ ...draft, kind: e.target.value as MountingRule["kind"] })
                      }
                    >
                      {mountingKinds.map(([key, name]) => (
                        <option key={key} value={key}>
                          {name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Tolerancia de dispersión y fijación (mm)
                    <input
                      inputMode="decimal"
                      value={draft.tolerance_mm}
                      onChange={(e) => edit({ ...draft, tolerance_mm: e.target.value })}
                    />
                  </label>
                  <label>
                    Fuente de montaje
                    <input
                      value={draft.source}
                      onChange={(e) => edit({ ...draft, source: e.target.value })}
                    />
                  </label>
                </div>
                <label className="mounting-check">
                  <input
                    type="checkbox"
                    checked={draft.synthetic}
                    onChange={(e) => edit({ ...draft, synthetic: e.target.checked })}
                  />
                  Autoridad sintética DEMO, sin certificación
                </label>
                <p>
                  Fabricación = menor medida del vano − holguras − marco − ensanches + traslapes.
                  Los ceros visibles significan que declaras que ese lado no aplica esa deducción.
                </p>
                <div className="mounting-rule-sides">
                  {sides.map(([side, label]) => (
                    <fieldset key={side}>
                      <legend>{label}</legend>
                      {fields.map(([key, name]) => (
                        <label key={key}>
                          {name} (mm)
                          <input
                            inputMode="decimal"
                            value={draft[side][key]}
                            onChange={(e) =>
                              edit({ ...draft, [side]: { ...draft[side], [key]: e.target.value } })
                            }
                          />
                        </label>
                      ))}
                    </fieldset>
                  ))}
                </div>
                <details>
                  <summary>Ensanches y accesorios de fijación</summary>
                  {catalog.isError ? (
                    <p role="alert">
                      No se cargaron los accesorios de la serie.{" "}
                      <button onClick={() => void catalog.refetch()}>Reintentar</button>
                    </p>
                  ) : catalog.data?.length ? (
                    catalog.data.map((item) => {
                      const selected = draft.extras.find((extra) => extra.code === item.code);
                      return (
                        <div key={item.code}>
                          <label className="mounting-check">
                            <input
                              type="checkbox"
                              checked={Boolean(selected)}
                              onChange={(e) =>
                                edit({
                                  ...draft,
                                  extras: e.target.checked
                                    ? [
                                        ...draft.extras,
                                        {
                                          code: item.code,
                                          decision: "ACCEPT",
                                          sides: item.default_sides,
                                        },
                                      ]
                                    : draft.extras.filter((extra) => extra.code !== item.code),
                                })
                              }
                            />
                            {item.name}
                            {item.synthetic ? " · DEMO" : ""}
                          </label>
                          {selected && item.basis === "SIDES" && (
                            <fieldset>
                              <legend>Lados de {item.name}</legend>
                              {(item.default_sides ?? []).map((side) => {
                                return (
                                  <label className="mounting-check" key={side}>
                                    <input
                                      type="checkbox"
                                      checked={selected.sides?.includes(side) ?? false}
                                      onChange={(event) =>
                                        edit({
                                          ...draft,
                                          extras: draft.extras.map((extra) =>
                                            extra.code !== item.code
                                              ? extra
                                              : {
                                                  ...extra,
                                                  sides: event.target.checked
                                                    ? [...(extra.sides ?? []), side]
                                                    : (extra.sides ?? []).filter(
                                                        (value) => value !== side,
                                                      ),
                                                },
                                          ),
                                        })
                                      }
                                    />
                                    {sideLabels[side]}
                                  </label>
                                );
                              })}
                            </fieldset>
                          )}
                        </div>
                      );
                    })
                  ) : (
                    <p>
                      Sin dato: declara los ensanches y fijaciones en Catálogo antes de exigirlos en
                      el montaje.
                    </p>
                  )}
                </details>
                <label>
                  Motivo del cambio
                  <textarea
                    value={reason}
                    onChange={(e) => {
                      setReason(e.target.value);
                      setReview(false);
                    }}
                  />
                </label>
                {!review ? (
                  <button
                    disabled={!draft.name.trim() || !draft.source.trim() || !reason.trim()}
                    onClick={() => setReview(true)}
                  >
                    Revisar cambios
                  </button>
                ) : (
                  <section aria-label="Cambios de montaje">
                    <p>
                      {current
                        ? "Se reemplaza la regla para nuevas mediciones."
                        : "Se declara una nueva regla de montaje."}{" "}
                      Las revisiones emitidas conservan su autoridad.
                    </p>
                    <div className="mounting-grid">
                      {sides.map(([side, label]) => (
                        <div key={side}>
                          <h4>{label}</h4>
                          {fields.map(([key, name]) => (
                            <p className="mounting-number" key={key}>
                              {name}: {current ? fmtMm(current.rule[side][key]) : "Sin dato"} →{" "}
                              {fmtMm(draft[side][key])} mm
                            </p>
                          ))}
                        </div>
                      ))}
                    </div>
                    <p>
                      Ensanches y fijaciones:{" "}
                      {draft.extras.length
                        ? draft.extras
                            .map((extra) => {
                              const item = catalog.data?.find(
                                (definition) => definition.code === extra.code,
                              );
                              return `${item?.name ?? "Accesorio sin dato"}${
                                extra.sides?.length
                                  ? ` · ${extra.sides.map((side) => sideLabels[side].toLowerCase()).join(", ")}`
                                  : ""
                              }`;
                            })
                            .join("; ")
                        : "Sin accesorios declarados"}
                      .
                    </p>
                    <button className="primary-action" onClick={() => void save(draft)}>
                      Guardar autoridad de montaje
                    </button>
                  </section>
                )}
                <button
                  onClick={() => {
                    setDraft(null);
                    setReview(false);
                  }}
                >
                  Descartar cambios
                </button>
              </fieldset>
            )}
          </>
        ))}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
