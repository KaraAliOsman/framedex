import { useEffect, useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";

import { t } from "../i18n/es-CL";
import { Wordmark } from "../brand/Brand";
import { DimLoader } from "../ui/Signature";

import { useAuthSession } from "./AuthSessionProvider";
import { consumeReturnTo } from "./returnTo";

/** Supabase carries link failures in the URL hash:
 * `#error=access_denied&error_code=otp_expired&error_description=…`. */
function hashError(): { expired: boolean; failed: boolean } {
  const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  const code = params.get("error_code") ?? "";
  const failed = params.has("error") || params.has("error_code");
  return { expired: code === "otp_expired", failed };
}

export function AuthCallbackPage(): JSX.Element {
  const auth = useAuthSession();
  const navigate = useNavigate();
  const linkError = useMemo(hashError, []);

  useEffect(() => {
    // consumeReturnTo reads the path the guard stashed before the magic-link
    // round trip — a validated internal path only, never an open redirect.
    if (auth.status === "ready") navigate(consumeReturnTo(), { replace: true });
    if (auth.status === "mfa_required") navigate("/auth/mfa", { replace: true });
    if (auth.status === "organization_required") {
      navigate("/select-organization", { replace: true });
    }
  }, [auth.status, navigate]);

  if (["anonymous", "error", "no_membership"].includes(auth.status)) {
    return (
      <main className="auth-screen" data-density="office">
        <section className="auth-card" aria-label="Acceso por enlace">
          <Wordmark width={176} />
          <p role="alert">
            {linkError.expired
              ? t("auth.linkExpired")
              : t(auth.status === "no_membership" ? "auth.noMembership" : "auth.callbackError")}
          </p>
          <Link className="ui-button ui-button--primary" to="/login">
            {t("auth.returnToLogin")}
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="auth-screen" data-density="office" data-testid="auth-callback">
      <section className="auth-card" aria-label="Comprobando acceso">
        <Wordmark width={176} />
        <DimLoader label={t("auth.callback")} />
      </section>
    </main>
  );
}
