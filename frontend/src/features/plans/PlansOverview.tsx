import type { CapabilitiesResponse } from "../../api/generated/models/capabilitiesResponse";
import { t } from "../../i18n/es-CL";
import { useCapabilities } from "./useCapabilities";

/** Empresa › Planes (dirección final 06 · 8): «Manual completo» and «La
 * misma IA, más capacidad de uso». Every AI plan gets the same core, model
 * and control; plans differ by included usage. Figures come from the server
 * resolution (frozen legacy allowances) — nothing here sells a smarter AI,
 * better openings or more control by price, and nothing activates a sale. */

const PLAN_LABEL: Record<string, Parameters<typeof t>[0]> = {
  STARTER: "billing.STARTER",
  TRIAL: "billing.TRIAL",
  PRO: "billing.PRO",
  BUSINESS: "billing.BUSINESS",
  BUSINESS_2X: "billing.BUSINESS_2X",
};

const NUMBER = new Intl.NumberFormat("es-CL");
const DATE = new Intl.DateTimeFormat("es-CL", {
  dateStyle: "medium",
  timeZone: "America/Santiago",
});

function planName(code: string): string {
  const key = PLAN_LABEL[code];
  return key ? t(key) : code;
}

function windowText(kind: string): string {
  return kind === "trial_total" ? "en total durante la prueba" : "por mes de servicio";
}

function originText(origin: string | null): string {
  if (origin === "pack") return "Pack comprado · no vence";
  if (origin === "trial") return "Prueba";
  if (origin === "monthly") return "Cupo del mes";
  return "Saldo anterior";
}

export function PlansOverview(): JSX.Element | null {
  const capabilities = useCapabilities();
  const data: CapabilitiesResponse | undefined = capabilities.data;
  if (!data) return null;
  const aiPlans = data.plans.filter((plan) => plan.ai && plan.code !== "TRIAL");
  const owner = data.role === "OWNER";
  return (
    <section aria-labelledby="plans-title" className="settings-group plans-overview">
      <h2 id="plans-title" className="settings-group__title">
        Planes
      </h2>
      <div className="plans-overview__grid">
        <article className="plans-overview__card">
          <h3>Manual completo</h3>
          <p>
            Cotizador profesional sin IA: catálogos, obras, posiciones y aperturas, Mesa de obra y
            Estudio, motor de cálculo, precios, PDF, cortes, compras, taller y terreno. No depende
            del asistente ni consume créditos.
          </p>
        </article>
        <article className="plans-overview__card">
          <h3>La misma IA, más capacidad de uso</h3>
          <p>
            Todos los planes con IA tienen el mismo núcleo, el mismo modelo
            {data.model_selection ? ` (${data.model_selection})` : ""} y el mismo control: Chat y
            Trabajo, Solo proponer, Con aprobación y Omitir todo, historial, adjuntos, resumen y
            deshacer. Cambia el uso incluido.
          </p>
          <ul className="plans-overview__core">
            {data.capabilities.map((item) => (
              <li key={item.id}>{item.label}</li>
            ))}
          </ul>
          <table className="plans-overview__table">
            <thead>
              <tr>
                <th scope="col">Plan</th>
                <th scope="col">Créditos incluidos</th>
              </tr>
            </thead>
            <tbody>
              {aiPlans.map((plan) => (
                <tr
                  key={plan.code}
                  aria-current={plan.code === data.plan.code ? "true" : undefined}
                >
                  <th scope="row">{planName(plan.code)}</th>
                  <td>
                    {NUMBER.format(plan.included_credits)} {windowText(plan.window_kind)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="plans-overview__note">
            Extras profesionales:{" "}
            {data.extras.length ? "disponibles según contrato." : "ninguno declarado por ahora."}{" "}
            Los packs comprados no vencen; el cupo mensual no usado sí vence.
          </p>
        </article>
      </div>
      {owner && data.ai_entitlement.granted ? (
        <div className="plans-overview__usage" aria-label="Uso de IA de la empresa">
          <h3>Uso de IA</h3>
          <dl>
            <div>
              <dt>Cupo incluido</dt>
              <dd>
                {NUMBER.format(data.limits.included_credits)} {windowText(data.limits.window_kind)}
              </dd>
            </div>
            {data.limits.window?.next_grant_at ? (
              <div>
                <dt>Próxima entrega</dt>
                <dd>{DATE.format(new Date(data.limits.window.next_grant_at))}</dd>
              </div>
            ) : null}
            {data.balances.spendable !== null ? (
              <div>
                <dt>Saldo gastable</dt>
                <dd>
                  {NUMBER.format(data.balances.spendable)} créditos
                  {data.balances.reserved
                    ? ` · ${NUMBER.format(data.balances.reserved)} reservados`
                    : ""}
                </dd>
              </div>
            ) : null}
            {data.budget.monthly_limit !== null ? (
              <div>
                <dt>Presupuesto mensual</dt>
                <dd>
                  {NUMBER.format(data.budget.used ?? 0)} de{" "}
                  {NUMBER.format(data.budget.monthly_limit)} créditos · desde el{" "}
                  {DATE.format(new Date(data.budget.window_start))}
                </dd>
              </div>
            ) : null}
          </dl>
          {data.balances.by_origin.length ? (
            <ul className="plans-overview__lots">
              {data.balances.by_origin.map((lot, index) => (
                <li key={`${lot.origin}-${index}`}>
                  {originText(lot.origin)}: {NUMBER.format(lot.remaining)}
                  {lot.expires_at ? ` · vence el ${DATE.format(new Date(lot.expires_at))}` : ""}
                </li>
              ))}
            </ul>
          ) : null}
          <p className="plans-overview__note">
            Cada intercambio con la IA descuenta un costo fijo por ruta (
            {data.consumption_policy_version}); el cargo final aparece en el resumen de cada tarea.
          </p>
        </div>
      ) : null}
    </section>
  );
}
