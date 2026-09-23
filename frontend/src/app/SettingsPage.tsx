import { Link } from "react-router-dom";

import type { Membership, RoleEnum } from "../api/generated/models";
import { useAuthSession } from "../auth/AuthSessionProvider";
import { t, type TranslationKey } from "../i18n/es-CL";
import { useTheme } from "../theme/ThemeProvider";

const ROLE_KEYS: Record<RoleEnum, TranslationKey> = {
  OWNER: "settings.roleOwner",
  ESTIMATOR: "settings.roleEstimator",
  WORKSHOP_MANAGER: "settings.roleWorkshopManager",
  INSTALLER: "settings.roleInstaller",
};

function MembershipRow({ membership }: { membership: Membership }): JSX.Element {
  return (
    <li className="settings-row">
      <span>{membership.organization_name}</span>
      <span className="settings-role">{t(ROLE_KEYS[membership.role])}</span>
    </li>
  );
}

export function SettingsPage(): JSX.Element {
  const auth = useAuthSession();
  const { theme, toggleTheme } = useTheme();
  const me = auth.me;
  const org = me?.active_organization;
  const isOwner = org?.role === "OWNER";

  return (
    <section className="settings" aria-labelledby="page-title">
      <header className="dashboard-head">
        <div>
          <h1 id="page-title">{t("settings.title")}</h1>
          <p className="dashboard-sub">{org?.name ?? t("org.none")}</p>
        </div>
      </header>

      <div className="settings-grid">
        <div className="settings-card">
          <h2 className="eyebrow">{t("settings.account")}</h2>
          <dl className="settings-list">
            <div className="settings-row">
              <dt>{t("settings.email")}</dt>
              <dd className="settings-mono">{me?.user.email}</dd>
            </div>
            <div className="settings-row">
              <dt>{t("settings.twoFactor")}</dt>
              <dd>{me?.aal === "aal2" ? t("settings.aal2") : t("settings.aal1")}</dd>
            </div>
            <div className="settings-row">
              <dt>{t("settings.role")}</dt>
              <dd>{org ? t(ROLE_KEYS[org.role]) : "—"}</dd>
            </div>
          </dl>
        </div>

        <div className="settings-card">
          <h2 className="eyebrow">{t("settings.appearance")}</h2>
          <div className="settings-theme" role="radiogroup" aria-label={t("settings.theme")}>
            {(["light", "dark"] as const).map((option) => (
              <button
                key={option}
                type="button"
                role="radio"
                aria-checked={theme === option}
                className="settings-theme-option"
                data-active={theme === option}
                onClick={() => {
                  if (theme !== option) toggleTheme();
                }}
              >
                {option === "light" ? t("settings.light") : t("settings.dark")}
              </button>
            ))}
          </div>
        </div>

        {me !== null && me.memberships.length > 0 && (
          <div className="settings-card">
            <h2 className="eyebrow">{t("settings.memberships")}</h2>
            <ul className="settings-list settings-plain">
              {me.memberships.map((membership) => (
                <MembershipRow key={membership.organization_id} membership={membership} />
              ))}
            </ul>
          </div>
        )}

        {isOwner && (
          <div className="settings-card">
            <h2 className="eyebrow">{t("settings.billing")}</h2>
            <p className="settings-hint">{t("settings.billingHint")}</p>
            <div className="settings-links">
              <Link to="/settings/billing">{t("settings.billingPage")}</Link>
              <Link to="/settings/wallet">{t("settings.walletPage")}</Link>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
