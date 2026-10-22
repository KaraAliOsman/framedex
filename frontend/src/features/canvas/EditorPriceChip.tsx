import { Link } from "react-router-dom";
import { Popover } from "../../ui/Overlays";
import { Money } from "../../ui/DomainValues";
import type { CanvasDesignInputs } from "./canvasStore";
import { useEditorPrice } from "./useEditorPrice";
import { SimplePriceDetails } from "../pricing/SimplePriceDetails";
import "../pricing/working-price.css";

export function EditorPriceChip({
  organizationId,
  inputs,
  quantity,
  ready,
  pending = false,
}: {
  organizationId: string;
  inputs: CanvasDesignInputs;
  quantity: string;
  ready: boolean;
  pending?: boolean;
}) {
  const { price, calculating, error, retry } = useEditorPrice(
    organizationId,
    inputs,
    quantity,
    ready,
  );
  const priceLoading = pending || calculating;
  return (
    <Popover
      label="Origen del precio indicativo"
      trigger={
        <button type="button" className="editor-price" aria-label="Precio neto indicativo">
          {priceLoading ? (
            <span role="status">Calculando precio…</span>
          ) : price?.net !== null &&
            price?.net !== undefined &&
            price.unit_net !== null &&
            price.unit_net !== undefined ? (
            <>
              <small>Precio sin guardar</small>
              <span>
                <Money value={price.net} currency={price.currency} /> <small>neto</small>
              </span>
            </>
          ) : (
            <span>Precio · Falta completar</span>
          )}
        </button>
      }
    >
      <div className="working-price-detail">
        <h3>Precio neto indicativo</h3>
        {!priceLoading && price?.unit_net != null && price.net != null ? (
          <p>
            Por unidad <Money value={price.unit_net} currency={price.currency} /> · total de esta
            ventana <Money value={price.net} currency={price.currency} />, antes de impuestos. Es
            una lectura del diseño sin guardar; guarda la ventana para actualizar el total de la
            obra.
          </p>
        ) : null}
        <p>
          {priceLoading
            ? "El motor está calculando el diseño actual."
            : (price?.source ??
              price?.reason ??
              (error
                ? "No se pudo consultar el precio. Vuelve a intentar."
                : "Completa serie, vidrio y geometría para calcular el precio."))}
        </p>
        {error && (
          <button type="button" onClick={() => void retry()}>
            Reintentar precio
          </button>
        )}
        {!priceLoading && price?.net != null && (
          <SimplePriceDetails
            breakdown={price.breakdown}
            policy={price.policy}
            currency={price.currency}
          />
        )}
        {!priceLoading && price?.catalog_use?.is_example && (
          <p>Serie de ejemplo: datos sintéticos para ensayar.</p>
        )}
        {!priceLoading && (price?.catalog_use?.suggested_count ?? 0) > 0 && (
          <p>La serie usa valores sugeridos. Confírmalos antes de fabricar.</p>
        )}
        <p>
          La cantidad y el redondeo de moneda se calculan en el motor. Revisa los precios del
          proyecto antes de emitir.
        </p>
        {!priceLoading && price?.policy && (
          <Link to="/settings/general?section=prices">Cómo calculo mis precios</Link>
        )}
        {price?.use_advanced && <Link to="/pricing/commercial">Revisar reglas de precio</Link>}
        {!priceLoading && price?.modules && (
          <>
            <dl className="editor-module-prices">
              {price.modules.map((item, index) => (
                <div key={item.module_id}>
                  <dt>Módulo {index + 1}</dt>
                  <dd>
                    {item.net !== null ? (
                      <Money value={item.net} currency={price.currency} />
                    ) : (
                      <>Falta completar · {item.reason}</>
                    )}
                  </dd>
                </div>
              ))}
              <div>
                <dt>Acoples y ajustes del conjunto</dt>
                <dd>
                  {price.assembly_adjustment_net !== null &&
                  price.assembly_adjustment_net !== undefined ? (
                    <Money value={price.assembly_adjustment_net} currency={price.currency} />
                  ) : (
                    "Falta una tarifa por módulo"
                  )}
                </dd>
              </div>
              <div>
                <dt>Total por conjunto</dt>
                <dd>
                  <Money value={price.unit_net} currency={price.currency} />
                </dd>
              </div>
            </dl>
            <p>{price.breakdown_source}</p>
          </>
        )}
      </div>
    </Popover>
  );
}
