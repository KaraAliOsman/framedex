import { type FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";

import { t } from "../i18n/es-CL";

import { useAuthSession } from "./AuthSessionProvider";

export function LoginPage(): JSX.Element {
  const auth = useAuthSession();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (auth.status === "ready") return <Navigate to="/dashboard" replace />;

  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    try {
      await auth.requestMagicLink(email);
      setSent(true);
    } catch {
      setError(t("auth.magicLinkError"));
    }
  }

  return (
    <main className="auth-screen" data-testid="login-page">
      <section className="auth-card" aria-labelledby="login-title">
        <p className="eyebrow">{t("app.brandOs")}</p>
        <h1 id="login-title">{t("auth.loginTitle")}</h1>
        <p>{t("auth.loginDescription")}</p>
        <form onSubmit={(event) => void submit(event)}>
          <label htmlFor="email">{t("auth.email")}</label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <button type="submit">{t("auth.sendMagicLink")}</button>
        </form>
        {sent ? <p role="status">{t("auth.magicLinkSent")}</p> : null}
        {error ? <p role="alert">{error}</p> : null}
      </section>
    </main>
  );
}
