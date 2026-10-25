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
import { Button, Loading, Money } from "../../ui";
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

/** A finish shown on a small frame, not a dot: the material reads as a
 * window profile around a glass pane. */
export function FinishSample({
  color,
  size = "m",
}: {
  color: FinishColor;
  size?: "s" | "m";
}): JSX.Element {
  return (
    <span
      className={`finish-sample finish-sample--${size}`}
      style={{
        backgroundColor: finishColorCss(color),
        backgroundImage: color.texture_path ? `url(${color.texture_path})` : undefined,
      }}
      aria-hidden="true"
    >
      <span className="finish-sample__glass" />
    </span>
  );
}

/** One finish decision for the usual case (same colour on both faces); a
 * different colour per face lives under «Acabado especial» and existing
 * bicolor designs still open there. */
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
  const bicolor = Boolean(selected && selected.interior.code !== selected.exterior.code);
  const [special, setSpecial] = useState(bicolor);
  useEffect(() => {
    if (bicolor) setSpecial(true);
  }, [bicolor]);
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
  const byCode = new Map(authority.colors.map((color) => [color.code, color]));
  const single = combinations
    .filter((combo) => combo.interior === combo.exterior)
    .map((combo) => ({ combo, color: byCode.get(combo.interior) }))
    .filter((entry): entry is { combo: (typeof combinations)[number]; color: FinishColor } =>
      Boolean(entry.color),
    );
  function choose(face: FinishFace, code: string): void {
    const other = face === "interior" ? "exterior" : "interior";
    const combo =
      combinations.find((item) => item[face] === code && item[other] === selected?.[other].code) ??
      combinations.find((item) => item[face] === code);
    if (combo) onChange(combo.code);
  }
  const rule = selected?.combination;
  return (
    <section className="finish-selector" aria-label="Acabado">
      <div className="finish-grid" role="radiogroup" aria-label="Acabado de la ventana">
        {single.map(({ combo, color }) => {
          const checked = !bicolor && selected?.combination.code === combo.code;
          return (
            <button
              key={combo.code}
              type="button"
              role="radio"
              aria-checked={checked}
              className="finish-tile"
              disabled={disabled}
              onClick={() => onChange(combo.code)}
            >
              <FinishSample color={color} />
              <span className="finish-tile__name">{color.name}</span>
              <span className="finish-tile__kind">
                {processNames[color.kind] ?? "Acabado"}
                {color.synthetic ? " · Ejemplo" : ""}
              </span>
            </button>
          );
        })}
      </div>

      <div className="finish-price" aria-live="polite">
        <span>Cambio en el precio de esta ventana</span>
        {price.isFetching ? (
          <Loading label="Calculando" />
        ) : price.data?.delta_price_net ? (
          <strong>
            <Money value={price.data.delta_price_net} currency={price.data.currency} />
          </strong>
        ) : (
          <span className="finish-price__none">Se calcula al elegir la serie y las medidas</span>
        )}
      </div>

      <details
        className="finish-special"
        open={special}
        onToggle={(event) => setSpecial((event.target as HTMLDetailsElement).open)}
      >
        <summary>Acabado especial · distinto por cara</summary>
        <div className="finish-special__faces">
          {(["interior", "exterior"] as const).map((face) => {
            const color = selected?.[face];
            const other = face === "interior" ? "exterior" : "interior";
            return (
              <label className="finish-face" key={face}>
                <span>{face === "interior" ? "Cara interior" : "Cara exterior"}</span>
                <span className="finish-face__control">
                  {color && <FinishSample color={color} size="s" />}
                  <select
                    className="ui-field__input"
                    aria-label={face === "interior" ? "Cara interior" : "Cara exterior"}
                    value={color?.code ?? ""}
                    disabled={disabled}
                    onChange={(event) => choose(face, event.target.value)}
                  >
                    {!color && <option value="">Elige un acabado de la carta</option>}
                    {authority.colors.map((item) => (
                      <option
                        key={item.code}
                        value={item.code}
                        disabled={
                          !combinations.some(
                            (combo) =>
                              combo[face] === item.code &&
                              (!selected || combo[other] === selected[other].code),
                          ) && !combinations.some((combo) => combo[face] === item.code)
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
        </div>
      </details>

      {!selected ? (
        <p role="alert">
          El acabado guardado ya no está en la carta de esta serie. Elige uno vigente.
        </p>
      ) : (
        <details className="finish-source">
          <summary>
            {selected.interior.approximate || selected.exterior.approximate
              ? "Color aproximado · ver restricciones y origen"
              : "Restricciones y origen del acabado"}
          </summary>
          <dl>
            {(["interior", "exterior"] as const).map((face) => (
              <div key={face}>
                <dt>{face === "interior" ? "Cara interior" : "Cara exterior"}</dt>
                <dd>
                  {selected[face].name} ·{" "}
                  {processNames[selected[face].kind] ?? "Proceso por completar"} ·{" "}
                  {selected[face].manufacturer_code}
                </dd>
              </div>
            ))}
            <div>
              <dt>Refuerzo</dt>
              <dd>
                {rule?.reinforcement_required ? "Obligatorio" : "Según dimensiones de la serie"}
              </dd>
            </div>
            <div>
              <dt>Plazo adicional</dt>
              <dd>
                {rule?.extra_lead_days == null
                  ? "Proveedor por completar"
                  : `${rule.extra_lead_days} días`}
              </dd>
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
              <dt>Origen</dt>
              <dd>{rule?.source}</dd>
            </div>
            <div>
              <dt>Precio comparado con</dt>
              <dd>{price.data?.baseline_description ?? "Acabado base de la carta"}</dd>
            </div>
            <div>
              <dt>Origen del precio</dt>
              <dd>{price.data?.source ?? rule?.surcharge.source}</dd>
            </div>
          </dl>
        </details>
      )}
      {price.data?.reason && <p role="status">{price.data.reason}</p>}
      {price.isError && (
        <div role="alert" className="finish-error">
          <p>
            {denied
              ? "Tu rol no permite calcular precios. Pide revisión al dueño o a un estimador."
              : "No se pudo calcular el cambio de precio del acabado."}
          </p>
          {!denied && <Button onClick={() => void price.refetch()}>Reintentar</Button>}
        </div>
      )}
    </section>
  );
}
