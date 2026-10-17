import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type {
  FinishAuthority,
  FinishColor,
  PositionDesignRequest,
} from "../../api/generated/models";
import { projectFinishPreview } from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import { chartFinish, finishColorCss, type FinishFace } from "../canvas/finishColors";
import { Button, DimLoader, Money } from "../../ui";
import { fmtMm } from "../../format";
import "./finishes.css";

const processNames: Record<string, string> = {
  MASS: "PVC en masa",
  FOIL: "Foliado",
  COEXTRUDED: "Coextruido",
  RAL: "Lacado RAL",
  ANODIZED: "Anodizado",
  WOOD_EFFECT: "Efecto madera",
};

function Swatch({ color }: { color: FinishColor }): JSX.Element {
  return (
    <span
      className="finish-swatch"
      style={{
        backgroundColor: finishColorCss(color),
        backgroundImage: color.texture_path ? `url(${color.texture_path})` : undefined,
      }}
      aria-hidden="true"
    />
  );
}

export function FinishSelector({
  authority,
  value,
  design,
  organizationId,
  disabled,
  onChange,
}: {
  authority: FinishAuthority;
  value: string;
  design: PositionDesignRequest | null;
  organizationId: string;
  disabled: boolean;
  onChange(value: string): void;
}): JSX.Element {
  const selected = chartFinish(authority, value);
  const [same, setSame] = useState(selected?.interior.code === selected?.exterior.code);
  useEffect(() => {
    setSame(selected?.interior.code === selected?.exterior.code);
  }, [value]); // eslint-disable-line react-hooks/exhaustive-deps
  const baseline = authority.combinations[0];
  const price = useQuery({
    queryKey: ["finish-price", organizationId, design, baseline?.code],
    enabled: Boolean(design && baseline && selected),
    retry: false,
    queryFn: async ({ signal }) => {
      const response = await projectFinishPreview(
        { ...design!, baseline_color: baseline!.code },
        {
          headers: { "X-Organization-ID": organizationId },
          signal,
        },
      );
      if (response.status !== 200)
        throw new Error(
          "No se pudo calcular el cambio de acabado. Revisa los datos del diseño y reintenta.",
        );
      return response.data;
    },
  });
  const combinations = authority.combinations;
  const denied = price.error instanceof ApiError && price.error.status === 403;
  function choose(face: FinishFace, code: string): void {
    const combo = combinations.find((item) =>
      same
        ? item.interior === code && item.exterior === code
        : !selected
          ? item[face] === code
          : item[face] === code &&
            item[face === "interior" ? "exterior" : "interior"] ===
              selected?.[face === "interior" ? "exterior" : "interior"].code,
    );
    if (combo) onChange(combo.code);
  }
  const rule = selected?.combination;
  return (
    <section className="finish-selector" aria-label="Acabado por caras" data-density="office">
      <div className="finish-selector__row">
        {(["interior", "exterior"] as const).map((face) => {
          const color = selected?.[face];
          return (
            <label className="finish-face" key={face}>
              <span>Color {face}</span>
              <span className="finish-face__control">
                {color && <Swatch color={color} />}
                <select
                  className="assembly-select"
                  aria-label={`Color ${face}`}
                  value={color?.code ?? ""}
                  disabled={disabled || (same && face === "exterior")}
                  onChange={(event) => choose(face, event.target.value)}
                >
                  {!color && <option value="">Elige un acabado de la carta</option>}
                  {authority.colors.map((item) => (
                    <option
                      key={item.code}
                      value={item.code}
                      disabled={
                        !combinations.some((combo) =>
                          same
                            ? combo.interior === item.code && combo.exterior === item.code
                            : !selected
                              ? combo[face] === item.code
                              : combo[face] === item.code &&
                                combo[face === "interior" ? "exterior" : "interior"] ===
                                  selected?.[face === "interior" ? "exterior" : "interior"].code,
                        )
                      }
                    >
                      {item.name}
                    </option>
                  ))}
                </select>
              </span>
            </label>
          );
        })}
        <label className="finish-equal">
          <input
            type="checkbox"
            checked={same}
            disabled={
              disabled ||
              !selected ||
              !combinations.some(
                (combo) =>
                  combo.interior === selected.interior.code &&
                  combo.exterior === selected.interior.code,
              )
            }
            onChange={(event) => {
              setSame(event.target.checked);
              if (event.target.checked && selected) {
                const combo = combinations.find(
                  (item) =>
                    item.interior === selected.interior.code &&
                    item.exterior === selected.interior.code,
                );
                if (combo) onChange(combo.code);
              }
            }}
          />
          Igual en ambas caras
        </label>
        <div className="finish-price" aria-live="polite">
          <span>Δ precio neto por posición</span>
          {price.isFetching ? (
            <DimLoader label="Calculando cambio de acabado" />
          ) : price.data?.delta_price_net ? (
            <Money value={price.data.delta_price_net} currency={price.data.currency} />
          ) : (
            <span>Sin dato</span>
          )}
        </div>
      </div>
      {!selected ? (
        <p role="alert">
          Bloqueado · el acabado guardado no está en esta carta. Elige una combinación vigente en
          Catálogo.
        </p>
      ) : (
        <>
          <p className="finish-selector__notice">
            {rule?.reinforcement_required
              ? "Refuerzo obligatorio"
              : "Refuerzo según dimensiones de la serie"}{" "}
            ·{" "}
            {rule?.extra_lead_days == null
              ? "Sin dato de plazo adicional · completa la carta del proveedor"
              : `Plazo adicional: ${rule.extra_lead_days} días`}{" "}
            ·{" "}
            {selected.interior.approximate || selected.exterior.approximate
              ? "Color aproximado; revisa la muestra del fabricante"
              : "Color declarado por el fabricante"}
            {selected.interior.synthetic || selected.exterior.synthetic ? " · DEMO" : ""}
          </p>
          <details className="finish-source">
            <summary>Restricciones y fuente del acabado</summary>
            <dl>
              {(["interior", "exterior"] as const).map((face) => (
                <div key={face}>
                  <dt>{face === "interior" ? "Cara interior" : "Cara exterior"}</dt>
                  <dd>
                    <Swatch color={selected[face]} />
                    {selected[face].name} ·{" "}
                    {processNames[selected[face].kind] ?? "Sin dato de proceso"} ·{" "}
                    {selected[face].manufacturer_code}
                  </dd>
                </div>
              ))}
              <div>
                <dt>Base</dt>
                <dd>{selected.base?.name ?? "Aluminio"}</dd>
              </div>
              <div>
                <dt>Holgura de vidrio</dt>
                <dd className="finish-number">{fmtMm(rule!.glass_clearance_mm)} mm</dd>
              </div>
              <div>
                <dt>Límites de hoja</dt>
                <dd className="finish-number">
                  {rule?.max_leaf_width_mm
                    ? `${fmtMm(rule.max_leaf_width_mm)} mm de ancho`
                    : "Según serie"}{" "}
                  ·{" "}
                  {rule?.max_leaf_height_mm
                    ? `${fmtMm(rule.max_leaf_height_mm)} mm de alto`
                    : "Según serie"}
                </dd>
              </div>
              <div>
                <dt>Fuente</dt>
                <dd>{rule?.source}</dd>
              </div>
              <div>
                <dt>Variación respecto a</dt>
                <dd>{price.data?.baseline_description ?? "Acabado base de la carta"}</dd>
              </div>
              <div>
                <dt>Fuente del precio</dt>
                <dd>{price.data?.source ?? rule?.surcharge.source}</dd>
              </div>
            </dl>
          </details>
        </>
      )}
      {price.data?.reason && <p role="status">{price.data.reason}</p>}
      {price.isError && (
        <div role="alert">
          <p>
            {denied
              ? "Tu rol no permite calcular precios. Pide revisión al dueño o a un estimador."
              : "Sin dato: no se pudo calcular el cambio de acabado. Revisa los datos del diseño y reintenta."}
          </p>
          {!denied && <Button onClick={() => void price.refetch()}>Reintentar precio</Button>}
          <details>
            <summary>Detalles técnicos</summary>
            <p>{price.error.message}</p>
          </details>
        </div>
      )}
    </section>
  );
}
