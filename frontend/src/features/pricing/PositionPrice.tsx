import { Link } from "react-router-dom";
import type {
  PositionResponse,
  ProjectResponse,
  SimplePriceBreakdown,
} from "../../api/generated/models";
import { SimplePriceDetails } from "./SimplePriceDetails";
import { formatMoney } from "../../format";
import { Popover } from "../../ui/Overlays";
import "./working-price.css";

type Sale = {
  line_net?: string | null;
  unit_net?: string | null;
  source?: string;
  breakdown?: SimplePriceBreakdown | null;
  catalog_use?: { suggested_count?: number; verified?: boolean; is_example?: boolean } | null;
};

export function PositionPrice({
  project,
  position,
}: {
  project: ProjectResponse;
  position: PositionResponse;
}) {
  const sale = position.commercial as Sale | null;
  if (sale?.line_net == null) return <span>Sin precio</span>;
  const currency = project.working_price?.currency ?? project.currency;
  const breakdown = sale.breakdown;
  const policy = project.working_price?.policy;
  const name = position.location_tag || `Ventana ${position.position_index}`;
  return (
    <Popover
      label={`Precio de ${name}`}
      trigger={
        <button
          className="position-price"
          type="button"
          aria-label={`¿De dónde sale el precio de ${name}?`}
          onClick={(event) => event.stopPropagation()}
        >
          {formatMoney(sale.line_net, currency)}
        </button>
      }
    >
      <div className="working-price-detail">
        <h3>¿De dónde sale?</h3>
        <p>
          {name} · {position.quantity} {position.quantity === 1 ? "unidad" : "unidades"}
        </p>
        <SimplePriceDetails breakdown={breakdown} policy={policy} currency={currency} />
        <dl>
          <div>
            <dt>Precio neto por unidad</dt>
            <dd>{formatMoney(sale.unit_net, currency)}</dd>
          </div>
          <div>
            <dt>Total neto de esta ventana</dt>
            <dd>{formatMoney(sale.line_net, currency)}</dd>
          </div>
        </dl>
        <p>Los totales incluyen la cantidad guardada.</p>
        {sale.catalog_use?.is_example && <p>Serie de ejemplo: datos sintéticos para ensayar.</p>}
        {(sale.catalog_use?.suggested_count ?? 0) > 0 && (
          <p>
            La serie usa valores sugeridos. Confírmalos y verifica una ventana de prueba antes de
            fabricar.
          </p>
        )}
        <p>{sale.source || "Origen: cálculo del motor de esta revisión."}</p>
        {!breakdown && (
          <p>
            El detalle de costos y margen está disponible para el dueño en los ajustes avanzados.
          </p>
        )}
        {policy && <Link to="/settings/general?section=prices">Cómo calculo mis precios</Link>}
      </div>
    </Popover>
  );
}
