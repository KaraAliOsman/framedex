import { Link } from "react-router-dom";
import { DocLockup } from "./Brand";

export function AboutPage(): JSX.Element {
  return (
    <main className="recovery-page" data-density="office">
      <section className="recovery-sheet">
        <DocLockup />
        <h1>Acerca de DEKOPEN</h1>
        <p>
          Ingeniería paramétrica y cotización para fábricas de ventanas y puertas de PVC y aluminio.
        </p>
        <p>
          Las medidas, cortes y precios provienen del motor y de las autoridades declaradas en el
          catálogo. La marca representa la sección de un perfil extruido.
        </p>
        <Link className="ui-button" to="/settings">
          Volver a Ajustes
        </Link>
      </section>
    </main>
  );
}
