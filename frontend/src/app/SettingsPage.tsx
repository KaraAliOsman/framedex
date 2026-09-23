import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../api/apiMutator";
import {
  projectPaymentIntegrationSave,
  projectPaymentIntegrationStatus,
  siiCafRegister,
  siiCafsList,
  siiCertificateStatus,
  siiCertificateUpload,
} from "../api/generated/dekopen";
import type {
  ApiUrlEnum,
  Membership,
  PaymentIntegrationStatus,
  RoleEnum,
  SiiCaf,
  SiiCertificate,
} from "../api/generated/models";
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

function FlowIntegrationCard({ orgId }: { orgId: string }): JSX.Element {
  const [status, setStatus] = useState<PaymentIntegrationStatus | null>(null);
  const [apiUrl, setApiUrl] = useState<ApiUrlEnum>("https://sandbox.flow.cl/api");
  const [apiKey, setApiKey] = useState("");
  const [secretKey, setSecretKey] = useState("");
  const [returnUrl, setReturnUrl] = useState("");
  const [enabled, setEnabled] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ text: string; error: boolean } | null>(null);
  const requestOptions = { headers: { "X-Organization-ID": orgId } };

  const load = useCallback(async () => {
    try {
      const response = await projectPaymentIntegrationStatus(requestOptions);
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      setStatus(response.data);
      if (response.data.configured) {
        setApiUrl(response.data.api_url as ApiUrlEnum);
        setReturnUrl(response.data.payer_return_url ?? "");
        setEnabled(response.data.enabled ?? true);
      }
    } catch {
      setMessage({ text: t("settings.flowLoadError"), error: true });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    void load();
  }, [load]);

  async function save(event: FormEvent): Promise<void> {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    try {
      const response = await projectPaymentIntegrationSave(
        {
          api_url: apiUrl,
          api_key: apiKey.trim() || (status?.api_key_preview ?? "").replace("…", ""),
          ...(secretKey.trim() ? { secret_key: secretKey.trim() } : {}),
          payer_return_url: returnUrl.trim(),
          enabled,
        },
        requestOptions,
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      setStatus(response.data);
      setSecretKey("");
      setMessage({ text: t("settings.flowSaved"), error: false });
    } catch {
      setMessage({ text: t("settings.flowSaveError"), error: true });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="settings-card">
      <h2 className="eyebrow">{t("settings.flow")}</h2>
      <p className="settings-hint">{t("settings.flowHint")}</p>
      <p>
        <span
          className={`production-chip ${status?.configured ? "delivery-delivered" : "delivery-scheduled"}`}
        >
          {status?.configured ? t("settings.flowConfigured") : t("settings.flowNotConfigured")}
        </span>
        {status?.api_key_preview && (
          <span className="settings-mono"> · {status.api_key_preview}</span>
        )}
      </p>
      {message && <p className={message.error ? "form-error" : "settings-hint"}>{message.text}</p>}
      <form className="payments-form" onSubmit={save}>
        <label>
          {t("settings.flowEnv")}
          <select value={apiUrl} onChange={(event) => setApiUrl(event.target.value as ApiUrlEnum)}>
            <option value="https://sandbox.flow.cl/api">{t("settings.flowSandbox")}</option>
            <option value="https://www.flow.cl/api">{t("settings.flowProduction")}</option>
          </select>
        </label>
        <label>
          {t("settings.flowApiKey")}
          <input
            required={!status?.configured}
            value={apiKey}
            onChange={(event) => setApiKey(event.target.value)}
            placeholder={status?.api_key_preview ?? "AB12CD34EF56"}
          />
        </label>
        <label>
          {t("settings.flowSecret")}
          <input
            type="password"
            value={secretKey}
            onChange={(event) => setSecretKey(event.target.value)}
            placeholder={status?.configured ? t("settings.flowSecretKeep") : ""}
          />
        </label>
        <label>
          {t("settings.flowReturnUrl")}
          <input
            value={returnUrl}
            onChange={(event) => setReturnUrl(event.target.value)}
            placeholder="https://taller.cl/pago/retorno"
          />
        </label>
        <label className="settings-inline">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(event) => setEnabled(event.target.checked)}
          />
          {t("settings.flowEnabled")}
        </label>
        <div className="payments-form-actions">
          <button type="submit" className="primary-action" disabled={busy}>
            {t("settings.flowSave")}
          </button>
        </div>
      </form>
    </div>
  );
}

function SiiCafCard({ orgId }: { orgId: string }): JSX.Element {
  const [items, setItems] = useState<SiiCaf[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ text: string; error: boolean } | null>(null);
  const requestOptions = { headers: { "X-Organization-ID": orgId } };

  const load = useCallback(async () => {
    try {
      const response = await siiCafsList(requestOptions);
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      setItems(response.data.items);
    } catch {
      setMessage({ text: t("settings.siiCafError"), error: true });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    void load();
  }, [load]);

  async function upload(event: FormEvent): Promise<void> {
    event.preventDefault();
    const input = (event.target as HTMLFormElement).querySelector<HTMLInputElement>(
      "input[type=file]",
    );
    const file = input?.files?.[0];
    if (!file) return;
    const cafXml = await file.text();
    const form = event.target as HTMLFormElement;
    const field = (name: string) =>
      (form.elements.namedItem(name) as HTMLInputElement | null)?.value.trim() ?? "";
    const actecoRaw = field("acteco");
    setBusy(true);
    setMessage(null);
    try {
      const response = await siiCafRegister(
        {
          caf_xml: cafXml,
          giro_emis: field("giro_emis"),
          dir_origen: field("dir_origen"),
          cmna_origen: field("cmna_origen"),
          acteco: actecoRaw ? Number(actecoRaw) : null,
        },
        requestOptions,
      );
      if (response.status !== 201) throw new ApiError(response.status, response.data);
      if (input) input.value = "";
      setMessage({ text: t("settings.siiCafUploaded"), error: false });
      await load();
    } catch {
      setMessage({ text: t("settings.siiCafError"), error: true });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="settings-card">
      <h2 className="eyebrow">{t("settings.siiTitle")}</h2>
      {message && <p className={message.error ? "form-error" : "settings-hint"}>{message.text}</p>}
      {items.length === 0 ? (
        <p className="settings-hint">{t("settings.siiCafEmpty")}</p>
      ) : (
        <table className="payments-table">
          <thead>
            <tr>
              <th>{t("settings.siiCafType")}</th>
              <th>{t("settings.siiCafRange")}</th>
              <th>{t("settings.siiCafUsed")}</th>
              <th>{t("settings.siiCafRemaining")}</th>
            </tr>
          </thead>
          <tbody>
            {items.map((caf) => (
              <tr key={caf.id}>
                <td>{`DTE-${caf.tipo_dte}`}</td>
                <td>{`${caf.folio_desde}–${caf.folio_hasta}`}</td>
                <td>{caf.folio_actual < caf.folio_desde ? "—" : caf.folio_actual}</td>
                <td>{caf.remaining}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <form className="payments-form" onSubmit={upload}>
        <label>
          {t("settings.siiCafFile")}
          <input type="file" accept=".xml,text/xml" required />
        </label>
        <label>
          {t("settings.siiGiro")}
          <input name="giro_emis" maxLength={80} required />
        </label>
        <label>
          {t("settings.siiAddress")}
          <input name="dir_origen" maxLength={70} required />
        </label>
        <label>
          {t("settings.siiComuna")}
          <input name="cmna_origen" maxLength={20} required />
        </label>
        <label>
          {t("settings.siiActeco")}
          <input name="acteco" type="number" min={1} required />
        </label>
        <div className="payments-form-actions">
          <button type="submit" className="primary-action" disabled={busy}>
            {t("settings.siiCafUpload")}
          </button>
        </div>
      </form>
    </div>
  );
}

function SiiCertificateCard({ orgId }: { orgId: string }): JSX.Element {
  const [certificate, setCertificate] = useState<SiiCertificate | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ text: string; error: boolean } | null>(null);
  const requestOptions = { headers: { "X-Organization-ID": orgId } };

  const load = useCallback(async () => {
    try {
      const response = await siiCertificateStatus(requestOptions);
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      setCertificate(response.data.certificate);
    } catch {
      setMessage({ text: t("settings.siiCertError"), error: true });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    void load();
  }, [load]);

  async function upload(event: FormEvent): Promise<void> {
    event.preventDefault();
    const input = (event.target as HTMLFormElement).querySelector<HTMLInputElement>(
      "input[type=file]",
    );
    const file = input?.files?.[0];
    if (!file) return;
    const form = event.target as HTMLFormElement;
    const field = (name: string) =>
      (form.elements.namedItem(name) as HTMLInputElement | null)?.value.trim() ?? "";
    setBusy(true);
    setMessage(null);
    try {
      const pfx_b64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () =>
          resolve(String(reader.result ?? "").split(",")[1] ?? "");
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(file);
      });
      const response = await siiCertificateUpload(
        {
          pfx_b64,
          password: field("password"),
          nro_resol: Number(field("nro_resol") || "0"),
          fch_resol: field("fch_resol"),
        },
        requestOptions,
      );
      if (response.status !== 201) throw new ApiError(response.status, response.data);
      if (input) input.value = "";
      setMessage({ text: t("settings.siiCertUploaded"), error: false });
      await load();
    } catch {
      setMessage({ text: t("settings.siiCertError"), error: true });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="settings-card">
      <h2 className="eyebrow">{t("settings.siiCertTitle")}</h2>
      {message && <p className={message.error ? "form-error" : "settings-hint"}>{message.text}</p>}
      {certificate === null ? (
        <p className="settings-hint">{t("settings.siiCertEmpty")}</p>
      ) : (
        <dl className="settings-list">
          <div className="settings-row">
            <dt>{t("settings.siiCertSigner")}</dt>
            <dd className="settings-mono">{certificate.rut_firma}</dd>
          </div>
          <div className="settings-row">
            <dt>{t("settings.siiCertSubject")}</dt>
            <dd>{certificate.subject}</dd>
          </div>
          <div className="settings-row">
            <dt>{t("settings.siiCertValidUntil")}</dt>
            <dd>{certificate.valid_to.slice(0, 10)}</dd>
          </div>
          <div className="settings-row">
            <dt>{t("settings.siiCertResolution")}</dt>
            <dd className="settings-mono">{`N° ${certificate.nro_resol} · ${certificate.fch_resol}`}</dd>
          </div>
        </dl>
      )}
      <form className="payments-form" onSubmit={upload}>
        <label>
          {t("settings.siiCertFile")}
          <input type="file" accept=".pfx,.p12" required />
        </label>
        <label>
          {t("settings.siiCertPassword")}
          <input name="password" type="password" maxLength={200} autoComplete="off" />
        </label>
        <label>
          {t("settings.siiCertNroResol")}
          <input name="nro_resol" type="number" min={0} required />
        </label>
        <label>
          {t("settings.siiCertFchResol")}
          <input name="fch_resol" type="date" required />
        </label>
        <div className="payments-form-actions">
          <button type="submit" className="primary-action" disabled={busy}>
            {t("settings.siiCertUpload")}
          </button>
        </div>
      </form>
    </div>
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

        {isOwner && org !== undefined && <FlowIntegrationCard orgId={org.id} />}

        {isOwner && org !== undefined && <SiiCafCard orgId={org.id} />}

        {isOwner && org !== undefined && <SiiCertificateCard orgId={org.id} />}

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
