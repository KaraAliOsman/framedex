import "./portal.css";
import { useSearchParams } from "react-router-dom";
import { FlowSimulationPage } from "./FlowSimulationPage";

/** Historical returns have no proposal capability; never claim a payment
 * succeeded just because the browser reached this address. */
export function PaymentReturnPage(): JSX.Element {
  const [search] = useSearchParams();
  if (search.get("sim")) return <FlowSimulationPage returnMode />;
  return (
    <main className="portal-page" data-density="document">
      <section className="portal-card portal-card--narrow">
        <h1>Resultado del pago sin verificar</h1>
        <p>
          Esta dirección no contiene el acceso al resultado de su propuesta. Volver del proveedor no
          confirma un pago.
        </p>
        <p>
          Abra el enlace original del fabricante para consultar su saldo, o contáctelo con el
          comprobante del proveedor antes de repetir el pago.
        </p>
      </section>
    </main>
  );
}
