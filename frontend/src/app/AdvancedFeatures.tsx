import { Link } from "react-router-dom";
import { useAuthSession } from "../auth/AuthSessionProvider";
import { DeniedState, PageHeader } from "../ui";
import "./advanced-features.css";

export function AdvancedFeatures(): JSX.Element {
  const org = useAuthSession().me?.active_organization;
  if (!org || !["OWNER", "ESTIMATOR", "WORKSHOP_MANAGER"].includes(org.role))
    return <DeniedState reason="El dueño, vendedor o jefe de taller consulta estas funciones." />;
  const management = org.role === "OWNER" || org.role === "WORKSHOP_MANAGER";
  return (
    <section className="advanced-features" aria-labelledby="page-title">
      <PageHeader title="Funciones avanzadas" headingId="page-title" context="Empresa" />
      <ul>
        {management && (
          <>
            <li>
              <Link to="/production?section=mecanizado">Mecanizado CNC</Link>
              <p>
                Selecciona una orden para revisar sus operaciones y preparar el archivo de máquina.
              </p>
            </li>
            <li>
              <Link to="/analytics?view=margin">Cohortes y cierres de costos</Link>
              <p>Compara revisiones y costos registrados de las obras.</p>
            </li>
          </>
        )}
        <li>
          <Link to="/field">Rectificación en terreno</Link>
          <p>Abre una visita para revisar medidas y proponer la siguiente revisión de la obra.</p>
        </li>
        {org.role === "OWNER" && (
          <li>
            <Link to="/pricing/cost-lists">Listas de costos y reglas avanzadas</Link>
            <p>Consulta precios de compra, reglas y su historial de cambios.</p>
          </li>
        )}
        {org.role === "ESTIMATOR" && (
          <li>
            <Link to="/pricing/commercial">Reglas comerciales</Link>
            <p>Consulta las condiciones de venta disponibles para tu rol.</p>
          </li>
        )}
      </ul>
      <Link to="/settings/general?section=prices">Cómo calculo mis precios</Link>
    </section>
  );
}
