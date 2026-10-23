import { type FormEvent, useState } from "react";

import { workshopCreate } from "../api/generated/dekopen";
import { Wordmark } from "../brand/Brand";
import { actionErrorDetail } from "../features/errors";
import { ValidatedForm } from "../ui/FormValidation";

import { useAuthSession } from "./AuthSessionProvider";

/** First use (F1): a verified person without any workshop creates their own.
 * The server sets the Chile defaults; the owner enrolls a second factor next. */
export function CreateWorkshop(): JSX.Element {
  const auth = useAuthSession();
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const valid = name.trim().length >= 2;

  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (busy || !valid) return;
    setBusy(true);
    setError("");
    try {
      const result = await workshopCreate({ name: name.trim() });
      if (result.status === 200) {
        // Selecting the new workshop reloads the context: the owner goes on
        // to enroll the second factor, then to the first-use guide.
        await auth.selectOrganization(result.data.organization_id);
      }
    } catch (caught) {
      setError(actionErrorDetail(caught, "No se pudo crear el taller. Reintenta en un momento."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-screen" data-density="office" data-testid="create-workshop">
      <section className="auth-card" aria-labelledby="workshop-title">
        <div className="auth-card__brand">
          <Wordmark width={176} />
        </div>
        <header className="auth-card__header">
          <h1 id="workshop-title">Crea tu taller</h1>
          <p className="auth-hint">
            Tu correo {auth.session?.user.email ? <strong>{auth.session.user.email}</strong> : null}{" "}
            está confirmado. Pon el nombre con que te conocen tus clientes; lo verás en cada
            cotización.
          </p>
        </header>
        <ValidatedForm className="auth-form" onSubmit={(event) => void submit(event)}>
          <label htmlFor="workshop-name">Nombre del taller</label>
          <input
            id="workshop-name"
            name="workshop-name"
            autoComplete="organization"
            autoFocus
            required
            minLength={2}
            maxLength={120}
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
          <dl className="auth-facts" aria-label="Así empieza tu taller">
            <div>
              <dt>País</dt>
              <dd>Chile</dd>
            </div>
            <div>
              <dt>Moneda</dt>
              <dd>Pesos (CLP)</dd>
            </div>
            <div>
              <dt>IVA</dt>
              <dd>19 %</dd>
            </div>
          </dl>
          <p className="auth-hint">
            Empiezas en prueba. El RUT y los datos legales se piden después, antes del primer
            documento.
          </p>
          <button type="submit" className="ui-button ui-button--primary" disabled={busy || !valid}>
            {busy ? "Creando el taller…" : "Crear mi taller"}
          </button>
        </ValidatedForm>
        {error ? (
          <p role="alert" className="auth-notice auth-notice--error">
            {error}
          </p>
        ) : null}
        <p className="auth-hint">
          ¿Te invitaron a un taller? Abre el enlace de la invitación que llegó a tu correo.
        </p>
        <button
          type="button"
          className="ui-button ui-button--ghost"
          onClick={() => void auth.signOut()}
        >
          Salir
        </button>
      </section>
    </main>
  );
}
