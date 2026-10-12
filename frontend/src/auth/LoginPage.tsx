import { ValidatedForm } from "../ui/FormValidation";
import { type FormEvent, useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { t } from "../i18n/es-CL";
import { Wordmark } from "../brand/Brand";
import { DimLoader } from "../ui/Signature";

import { useAuthSession } from "./AuthSessionProvider";
import { consumeReturnTo, stashReturnTo } from "./returnTo";

export function LoginPage(): JSX.Element {
  const auth = useAuthSession();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // A guarded route hands its path in router state; stash it so the intended
  // destination survives the magic-link round trip through the mail client.
  useEffect(() => {
    const from = (location.state as { from?: unknown } | null)?.from;
    if (typeof from === "string") stashReturnTo(from);
  }, [location.state]);

  if (auth.status === "ready") {
    return <Navigate to={consumeReturnTo()} replace />;
  }

  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (busy) return;
    setError(null);
    setBusy(true);
    try {
      await auth.requestMagicLink(email);
      setSent(true);
    } catch {
      setError(t("auth.magicLinkError"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-screen" data-density="office" data-testid="login-page">
      <section className="auth-card" aria-labelledby="login-title">
        <div className="auth-card__brand">
          <Wordmark width={176} />
        </div>
        <header className="auth-card__header">
          <h1 id="login-title">{t("auth.loginTitle")}</h1>
          <p className="auth-hint">{t("auth.loginDescription")}</p>
        </header>
        {auth.status === "no_membership" ? (
          <p role="alert" className="auth-notice auth-notice--error">
            Tu cuenta no pertenece a una organización. Pide al dueño que te agregue y vuelve a
            entrar.
          </p>
        ) : null}
        {!sent ? (
          <ValidatedForm className="auth-form" onSubmit={(event) => void submit(event)}>
            <label htmlFor="email">{t("auth.email")}</label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              autoFocus
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
            <button
              type="submit"
              className="ui-button ui-button--primary"
              disabled={busy || email.trim() === ""}
            >
              {busy ? t("auth.sending") : t("auth.sendMagicLink")}
            </button>
          </ValidatedForm>
        ) : null}
        {busy ? <DimLoader label="Enviando el enlace de acceso" /> : null}
        {sent ? (
          <div className="auth-sent">
            <p role="status" className="auth-notice auth-notice--ok">
              {t("auth.magicLinkSent")}
            </p>
            <button type="button" className="ui-button" onClick={() => setSent(false)}>
              Enviar otro enlace
            </button>
          </div>
        ) : null}
        {error ? (
          <p role="alert" className="auth-notice auth-notice--error">
            {error}
          </p>
        ) : null}
      </section>
    </main>
  );
}
