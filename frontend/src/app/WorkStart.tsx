import { useState } from "react";
import { Link } from "react-router-dom";
import { Orb } from "../features/assistant/Orb";
import { Icon } from "../ui/Icon";
import { ValidatedForm } from "../ui/FormValidation";

export function WorkStart(): JSX.Element {
  const [goal, setGoal] = useState("");
  function delegate(prompt: string): void {
    window.dispatchEvent(new CustomEvent("dekopen:assistant", { detail: { prompt } }));
  }
  return (
    <section className="work-start" aria-label="Empezar a trabajar">
      <div className="work-start__intro">
        <span className="work-start__eyebrow">Tu estudio de ventanas</span>
        <h2>
          Buenas ideas.
          <br />
          <span>Trabajo bien hecho.</span>
        </h2>
        <p>Diseña a tu manera o encárgaselo a tu asistente.</p>
      </div>
      <div className="work-start__work">
        <ValidatedForm
          className="work-start__composer"
          onSubmit={(event) => {
            event.preventDefault();
            if (goal.trim()) delegate(goal.trim());
          }}
        >
          <div>
            <Orb state={goal.trim() ? "input" : "idle"} size={36} />
            <label htmlFor="today-goal">¿Qué vamos a crear hoy?</label>
          </div>
          <textarea
            id="today-goal"
            rows={2}
            value={goal}
            maxLength={2000}
            onChange={(event) => setGoal(event.target.value)}
            placeholder="Por ejemplo: prepara una cotización para 4 ventanas de PVC…"
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
                event.preventDefault();
                if (goal.trim()) delegate(goal.trim());
              }
            }}
          />
          <footer>
            <span>Con las preferencias de tu empresa</span>
            <button type="submit" aria-label="Preparar encargo con IA" disabled={!goal.trim()}>
              <Icon name="arrow" size={20} />
            </button>
          </footer>
        </ValidatedForm>
        <div className="work-start__shortcuts">
          <Link to="/projects?create=1">
            <Icon name="plus" size={17} />
            Nueva obra
          </Link>
          <Link to="/catalogs/systems?import=new">
            <Icon name="upload" size={17} />
            Importar catálogo
          </Link>
          <button
            type="button"
            onClick={() =>
              delegate(
                "Ayúdame a resolver mis pendientes de hoy. Empieza por lo que bloquea a otros.",
              )
            }
          >
            <Icon name="check" size={17} />
            Resolver pendientes
          </button>
        </div>
      </div>
    </section>
  );
}
