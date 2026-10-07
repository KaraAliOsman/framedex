import { useEffect, useState } from "react";

import { projectDesignOptions } from "../../api/generated/dekopen";
import type { DesignOptions, Simulation } from "../../api/generated/models";
import { fmtMm } from "../../format";
import { DimLoader } from "../../ui/Signature";
import { ProductFrontSvg } from "../canvas/ProductFrontSvg";
import { resolveMembers } from "../canvas/members";
import { isProductModel, type ProductJson } from "../canvas/productEditing";
import type { OpeningLeafFact } from "../canvas/physicalOpenings";
import { formatMoney } from "../money";
import "./operations.css";

const noop = (): void => {};
type Price = {
  net?: string | null;
  currency?: string;
  reason?: string | null;
  delta_net?: string | null;
  source?: string;
};
type DrawingCalculation = {
  modules?: { module_id: string; result?: { opening_leaves?: OpeningLeafFact[] } }[];
};

function Drawing({
  product,
  options,
  color,
  engine,
}: {
  product: ProductJson;
  options: DesignOptions;
  color?: string;
  engine?: DrawingCalculation | null;
}): JSX.Element {
  return (
    <ProductFrontSvg
      product={product}
      openingFacts={Object.fromEntries(
        (engine?.modules ?? []).map((module) => [
          module.module_id,
          module.result?.opening_leaves ?? [],
        ]),
      )}
      members={resolveMembers(options, color)}
      selectedId={null}
      issues={[]}
      disabled
      preview
      dimLevel="overview"
      onSelectModule={noop}
      onAddUnit={noop}
      onCommitModuleWidth={noop}
      onCommitTotalWidth={noop}
      onCommitHeight={noop}
    />
  );
}

/** The drawing, dimensions and prices belong to the server simulation. No
 * edit or price arithmetic runs in this preview. */
export function SimulationPreview({
  simulation,
  organizationId,
}: {
  simulation: unknown;
  organizationId: string;
}): JSX.Element | null {
  const value = simulation as Simulation | null | undefined;
  const [options, setOptions] = useState<Record<string, DesignOptions>>({});
  const [error, setError] = useState(false);
  const before = value?.before as
    | {
        product?: ProductJson;
        system_id?: string;
        color?: string;
        price?: Price;
        engine?: DrawingCalculation | null;
      }
    | undefined;
  const systemIds = [
    ...new Set([value?.system_id, before?.system_id].filter((id): id is string => !!id)),
  ];
  const key = JSON.stringify(systemIds);
  useEffect(() => {
    if (key === "[]") return;
    let active = true;
    setError(false);
    setOptions({});
    void Promise.all(
      (JSON.parse(key) as string[]).map(async (id) => {
        const response = await projectDesignOptions(id, {
          headers: { "X-Organization-ID": organizationId },
        });
        if (response.status !== 200) throw Error("catalog_unavailable");
        return [id, response.data] as const;
      }),
    )
      .then((entries) => {
        if (active) setOptions(Object.fromEntries(entries));
      })
      .catch(() => {
        if (active) setError(true);
      });
    return () => {
      active = false;
    };
  }, [key, organizationId]);
  if (!value || !before) return null;
  const afterProduct = isProductModel(value.product) ? value.product : null;
  const beforeProduct = isProductModel(before.product) ? before.product : null;
  if (!beforeProduct && !afterProduct) return null;
  const price = value.price as Price;
  const items = [
    {
      label: "Antes",
      product: beforeProduct,
      system: before.system_id ?? value.system_id,
      color: before.color,
      engine: before.engine,
    },
    {
      label: "Propuesta",
      product: afterProduct,
      system: value.system_id,
      color: value.color,
      engine: value.engine as DrawingCalculation,
    },
  ];
  return (
    <section className="operation-preview" aria-label="Comparación de la propuesta">
      <p className="operation-preview__view">
        Vista interior · Simulación del motor
        {systemIds.some((id) => options[id]?.is_demo) ? " · DEMO" : ""}
      </p>
      <div className="operation-preview__drawings">
        {items.map((item) => (
          <figure key={item.label} className="sheet-miter">
            <figcaption>{item.label}</figcaption>
            {!item.product ? (
              <p>Sin posición</p>
            ) : options[item.system] ? (
              <Drawing
                product={item.product}
                options={options[item.system]!}
                color={item.color}
                engine={item.engine}
              />
            ) : (
              <p>
                {!error ? <DimLoader label="Cargando dibujo" /> : null}
                {error
                  ? "No pudimos cargar el catálogo para dibujar. Vuelve a abrir la propuesta."
                  : "Cargando dibujo…"}
              </p>
            )}
            {item.product?.assembly.modules.map((module, index) => (
              <p key={module.id} className="operation-preview__dimensions">
                Marco {index + 1} · {fmtMm(module.width_mm)} × {fmtMm(module.height_mm)} mm
              </p>
            ))}
          </figure>
        ))}
      </div>
      <dl className="operation-preview__prices">
        <dt>Venta neta antes</dt>
        <dd>
          {before.price?.net != null
            ? formatMoney(before.price.net, before.price.currency)
            : "Sin dato"}
        </dd>
        <dt>Venta neta propuesta</dt>
        <dd>{price.net != null ? formatMoney(price.net, price.currency) : "Sin dato"}</dd>
        <dt>Diferencia neta</dt>
        <dd>
          {price.delta_net != null ? formatMoney(price.delta_net, price.currency) : "Sin dato"}
        </dd>
      </dl>
      {price.reason ? (
        <p>{price.reason}</p>
      ) : (
        <p>
          Precio indicativo con las reglas de Ajustes. Guarda y revisa los precios del proyecto
          antes de emitir.
        </p>
      )}
      {!value.valid ? (
        <p role="alert">El motor bloquea la propuesta. Corrige el diseño antes de aplicar.</p>
      ) : null}
      <details>
        <summary>¿De dónde sale?</summary>
        <p>
          Medidas y diseño: operaciones verificadas por el motor sobre los datos declarados del
          marco.
        </p>
        <p>
          Venta anterior:{" "}
          {before.price?.source ??
            before.price?.reason ??
            "Sin dato: la simulación no adjuntó autoridad comercial anterior."}
        </p>
        <p>
          Venta propuesta:{" "}
          {price.source ??
            price.reason ??
            "Sin dato: la simulación no adjuntó autoridad comercial propuesta."}
        </p>
        <p>
          Diferencia: resta exacta de ambas ventas en el motor, disponible solo cuando ambas tienen
          autoridad.
        </p>
      </details>
      <details>
        <summary>Detalles técnicos de los cambios</summary>
        <pre>{JSON.stringify(value.diff, null, 2)}</pre>
      </details>
    </section>
  );
}
