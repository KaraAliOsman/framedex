import { useState } from "react";
import { Navigate } from "react-router-dom";

import { t } from "../i18n/es-CL";

import { useAuthSession } from "./AuthSessionProvider";

export function SelectOrganizationPage(): JSX.Element {
  const auth = useAuthSession();
  const [pendingId, setPendingId] = useState<string | null>(null);
  if (auth.status === "ready") return <Navigate to="/dashboard" replace />;

  return (
    <main className="auth-screen" data-testid="organization-selector">
      <section className="auth-card">
        <p className="eyebrow">{t("org.eyebrow")}</p>
        <h1>{t("org.select")}</h1>
        <div className="organization-list">
          {auth.memberships.map((membership) => (
            <button
              key={membership.organization_id}
              type="button"
              disabled={pendingId !== null}
              onClick={() => {
                setPendingId(membership.organization_id);
                void auth
                  .selectOrganization(membership.organization_id)
                  .finally(() => setPendingId(null));
              }}
            >
              <strong>{membership.organization_name}</strong>
              <span>{membership.role}</span>
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}
