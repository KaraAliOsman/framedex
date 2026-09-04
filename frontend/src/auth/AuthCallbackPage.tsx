import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";

import { t } from "../i18n/es-CL";

import { useAuthSession } from "./AuthSessionProvider";

export function AuthCallbackPage(): JSX.Element {
  const auth = useAuthSession();
  const navigate = useNavigate();

  useEffect(() => {
    if (auth.status === "ready") navigate("/dashboard", { replace: true });
    if (auth.status === "mfa_required") navigate("/auth/mfa", { replace: true });
    if (auth.status === "organization_required") {
      navigate("/select-organization", { replace: true });
    }
  }, [auth.status, navigate]);

  if (["anonymous", "error", "no_membership"].includes(auth.status)) {
    return (
      <main className="auth-screen">
        <p role="alert">
          {t(auth.status === "no_membership" ? "auth.noMembership" : "auth.callbackError")}
        </p>
        <Link to="/login">{t("auth.returnToLogin")}</Link>
      </main>
    );
  }

  return (
    <main className="auth-screen" data-testid="auth-callback">
      <p role="status">{t("auth.callback")}</p>
    </main>
  );
}
