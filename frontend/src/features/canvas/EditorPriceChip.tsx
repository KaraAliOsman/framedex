import { Link } from "react-router-dom";
import { Popover } from "../../ui/Overlays";
import { Money } from "../../ui/DomainValues";
import type { CanvasDesignInputs } from "./canvasStore";
import { useEditorPrice } from "./useEditorPrice";

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
      label="Fuente del precio indicativo"
      trigger={
        <button type="button" className="editor-price" aria-label="Precio neto indicativo">
          {priceLoading ? (
            <span role="status">Calculando precio…</span>
          ) : price?.net !== null &&
            price?.net !== undefined &&
            price.unit_net !== null &&
            price.unit_net !== undefined ? (
            <>
              <span>
                <Money value={price.unit_net} currency={price.currency} /> <small>neto / un.</small>
              </span>
              <span>
                <Money value={price.net} currency={price.currency} /> <small>línea</small>
              </span>
            </>
          ) : (
            <span>Precio · Sin dato</span>
          )}
        </button>
      }
    >
      <h3>Precio neto indicativo</h3>
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
      <p>
        La cantidad y el redondeo de moneda se calculan en el motor. Revisa los precios del proyecto
        antes de emitir.
      </p>
      <Link to="/pricing/commercial">Revisar reglas de precio</Link>
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
                    <>Sin dato · {item.reason}</>
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
                  "Sin dato · falta una tarifa por módulo"
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
    </Popover>
  );
}
