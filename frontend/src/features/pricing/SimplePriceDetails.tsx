import type { SimplePolicyResponse, SimplePriceBreakdown } from "../../api/generated/models";
import { formatMoney } from "../../format";
import { policyPercentInput } from "./policyNumbers";

/** One presentation of the server's exact per-window breakdown, saved or live. */
export function SimplePriceDetails({
  breakdown,
  policy,
  currency,
}: {
  breakdown?: SimplePriceBreakdown | null;
  policy?: SimplePolicyResponse;
  currency: string;
}) {
  return (
    <>
      {breakdown && (
        <dl>
          {(
            [
              ["Materiales", breakdown.materials],
              ["Merma", breakdown.waste],
              ["Mano de obra", breakdown.labor],
              ["Instalación", breakdown.installation],
              ["Accesorios y otros servicios", breakdown.extras_cost],
              ["Costo por unidad", breakdown.direct_cost],
              ["Utilidad por unidad", breakdown.profit],
            ] as const
          ).map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{formatMoney(value, currency)}</dd>
            </div>
          ))}
        </dl>
      )}
      {policy && (
        <p>
          Margen sobre venta: {policyPercentInput(policy.margin)} %. Mano de obra{" "}
          {policy.labor_basis === "M2" ? "por m²" : "por ventana"}; instalación{" "}
          {policy.installation_basis === "M2" ? "por m²" : "por ventana"}. Redondeo hacia arriba a
          múltiplos de {formatMoney(policy.rounding_step, currency)}.
        </p>
      )}
      {breakdown && (
        <p>
          La utilidad incluye {formatMoney(breakdown.rounding, currency)} de redondeo. Desglose de
          una unidad.
        </p>
      )}
      {policy && !policy.saved && (
        <p>Precios de empresa sugeridos; puedes ajustarlos en Mi empresa.</p>
      )}
    </>
  );
}
