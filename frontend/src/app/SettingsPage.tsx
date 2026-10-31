import { ActivationGuide } from "../features/settings/ActivationGuide";
import { StatusBadge } from "../ui/StatusBadge";
import { CollectionIntegrations } from "../features/projects/CollectionIntegrations";
import { ValidatedForm } from "../ui/FormValidation";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type RefObject,
} from "react";
import { Link, useSearchParams } from "react-router-dom";
import { MailIntegrationCard } from "../features/notifications/MailPanels";

import { ApiError } from "../api/apiMutator";
import { actionErrorDetail } from "../features/errors";
import {
  getOrganizationBrandingLogoReadUrl,
  organizationBrandingGet,
  organizationBrandingLogoDelete,
  organizationBrandingLogoUpload,
  organizationBrandingSave,
  projectPaymentIntegrationSave,
  projectPaymentIntegrationStatus,
  siiCafRegister,
  siiCafsList,
  siiCertificateStatus,
  siiCertificateUpload,
} from "../api/generated/dekopen";
import { apiFetchBlob } from "../api/apiMutator";
import type {
  ApiUrlEnum,
  Membership,
  PaymentIntegrationStatus,
  MembershipRoleEnum,
  SiiCaf,
  SiiCertificate,
} from "../api/generated/models";
import { PageHeader, DeniedState, Button, useConfirm } from "../ui";
import {
  CompanyCard,
  UsersCard,
  NumberingCard,
  QuotationNumberingCard,
  DocumentPreview,
} from "../features/settings/AdminSections";
import { SimplePricingSettings } from "../features/pricing/SimplePricingSettings";
import { ProductionSettings } from "../features/settings/ProductionSettings";
import { SiteMeasurementSettings } from "../features/settings/SiteMeasurementSettings";
import { InterfaceSettings } from "../features/settings/InterfaceSettings";
import { AnalyticsPreferences } from "../features/analytics/AnalyticsPreferences";
import type { OrgBrandingWriteRequest, DocumentPreferences } from "../api/generated/models";
import { useAuthSession } from "../auth/AuthSessionProvider";
import { formatDate } from "../features/money";
import { t, type TranslationKey } from "../i18n/es-CL";
import { MOD_K_HINT, MOD_KEY_HINT } from "../platform";
import { ExtraPolicyEditor } from "../features/projects/ExtraPolicyEditor";
import { DocumentSettings } from "../features/projects/DocumentSettings";
import { CompanyDesignDefaults } from "../features/projects/DesignDefaults";
import { MountingRulesSettings } from "../features/projects/MountingRulesSettings";
import { GlassRulesSettings } from "../features/glass/GlassRulesSettings";
import { AiSettingsSection } from "../features/assistant/AiSettingsSection";

const ROLE_KEYS: Record<MembershipRoleEnum, TranslationKey> = {
  OWNER: "settings.roleOwner",
  ESTIMATOR: "settings.roleEstimator",
  WORKSHOP_MANAGER: "settings.roleWorkshopManager",
  INSTALLER: "settings.roleInstaller",
  OPERATOR: "settings.roleOperator",
};

function FilePick({
  inputRef,
  accept,
  file,
  onFile,
}: {
  inputRef: RefObject<HTMLInputElement>;
  accept: string;
  file: File | null;
  onFile: (file: File | null) => void;
}): JSX.Element {
  return (
    <span className="file-field">
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="file-input-hidden"
        onChange={(event) => onFile(event.target.files?.[0] ?? null)}
      />
      <button type="button" className="secondary-action" onClick={() => inputRef.current?.click()}>
        {t("settings.fileChoose")}
      </button>
      <span className="file-field__name">{file ? file.name : t("settings.fileNone")}</span>
    </span>
  );
}

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
          // Blank = keep the stored key — never echo the masked preview back
          // as if it were the credential.
          ...(apiKey.trim() ? { api_key: apiKey.trim() } : {}),
          ...(secretKey.trim() ? { secret_key: secretKey.trim() } : {}),
          payer_return_url: returnUrl.trim(),
          enabled,
        },
        requestOptions,
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      setStatus(response.data);
      setSecretKey("");
      setApiKey("");
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
        <StatusBadge
          showIcon={false}
          className={`production-chip ${status?.configured ? "delivery-delivered" : "delivery-scheduled"}`}
        >
          {status?.configured ? t("settings.flowConfigured") : t("settings.flowNotConfigured")}
        </StatusBadge>
      </p>
      {message && <p className={message.error ? "form-error" : "settings-hint"}>{message.text}</p>}
      <ValidatedForm className="payments-form" data-region="marca-documentos" onSubmit={save}>
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
            placeholder={status?.configured ? "Deja vacío para conservar la clave" : ""}
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
      </ValidatedForm>
    </div>
  );
}

function SiiCafCard({ orgId }: { orgId: string }): JSX.Element {
  const [items, setItems] = useState<SiiCaf[]>([]);
  const [pickFile, setPickFile] = useState<File | null>(null);
  const pickRef = useRef<HTMLInputElement>(null);
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
    const file = pickFile;
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
      if (pickRef.current) pickRef.current.value = "";
      setPickFile(null);
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
      <ValidatedForm className="payments-form" data-region="logo-documentos" onSubmit={upload}>
        <label>
          {t("settings.siiCafFile")}
          <FilePick
            inputRef={pickRef}
            accept=".xml,text/xml"
            file={pickFile}
            onFile={setPickFile}
          />
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
      </ValidatedForm>
    </div>
  );
}

function SiiCertificateCard({ orgId }: { orgId: string }): JSX.Element {
  const [certificate, setCertificate] = useState<SiiCertificate | null>(null);
  const [pickFile, setPickFile] = useState<File | null>(null);
  const pickRef = useRef<HTMLInputElement>(null);
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
    const file = pickFile;
    if (!file) return;
    const form = event.target as HTMLFormElement;
    const field = (name: string) =>
      (form.elements.namedItem(name) as HTMLInputElement | null)?.value.trim() ?? "";
    setBusy(true);
    setMessage(null);
    try {
      const pfx_b64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result ?? "").split(",")[1] ?? "");
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
      if (pickRef.current) pickRef.current.value = "";
      setPickFile(null);
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
            <dd>{formatDate(certificate.valid_to)}</dd>
          </div>
          <div className="settings-row">
            <dt>{t("settings.siiCertResolution")}</dt>
            <dd className="settings-mono">{`N° ${certificate.nro_resol} · ${certificate.fch_resol}`}</dd>
          </div>
        </dl>
      )}
      <ValidatedForm className="payments-form" onSubmit={upload}>
        <label>
          {t("settings.siiCertFile")}
          <FilePick inputRef={pickRef} accept=".pfx,.p12" file={pickFile} onFile={setPickFile} />
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
      </ValidatedForm>
    </div>
  );
}

function OrgBrandingCard({
  orgId,
  onDraft,
  companyRevision,
  onSaved,
}: {
  orgId: string;
  onDraft?: (value: OrgBrandingWriteRequest) => void;
  companyRevision?: { previous?: string; updated: string };
  onSaved?: (revision: { previous?: string; updated: string }) => void;
}): JSX.Element {
  const confirm = useConfirm();
  const [expected, setExpected] = useState<string>();
  useEffect(() => {
    if (companyRevision)
      setExpected((previous) =>
        previous === companyRevision.previous ? companyRevision.updated : previous,
      );
  }, [companyRevision]);
  const [colorFallback, setColorFallback] = useState(false);
  const [logoUrl, setLogoUrl] = useState<string | null>(null);
  const [pickFile, setPickFile] = useState<File | null>(null);
  const pickRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ text: string; error: boolean } | null>(null);
  const [form, setForm] = useState({
    commercial_name: "",
    giro: "",
    brand_address: "",
    brand_phone: "",
    brand_email: "",
    brand_primary_color: "",
    document_attribution: false,
    portal_attribution: true,
    notification_email: "",
    internal_mail_enabled: false,
  });
  useEffect(() => {
    onDraft?.(form);
  }, [form, onDraft]);
  const requestOptions = useMemo(() => ({ headers: { "X-Organization-ID": orgId } }), [orgId]);

  const load = useCallback(async () => {
    try {
      const response = await organizationBrandingGet(requestOptions);
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      setForm({
        commercial_name: response.data.commercial_name ?? "",
        giro: response.data.giro ?? "",
        brand_address: response.data.brand_address ?? "",
        brand_phone: response.data.brand_phone ?? "",
        brand_email: response.data.brand_email ?? "",
        brand_primary_color: response.data.brand_primary_color,
        document_attribution: response.data.document_attribution,
        portal_attribution: response.data.portal_attribution,
        notification_email: response.data.notification_email ?? "",
        internal_mail_enabled: response.data.internal_mail_enabled,
      });
      setExpected(response.data.updated_at);
      setColorFallback(response.data.brand_color_fallback);
      if (response.data.brand_logo_key) {
        try {
          const { blob } = await apiFetchBlob(getOrganizationBrandingLogoReadUrl());
          setLogoUrl((previous) => {
            if (previous) URL.revokeObjectURL(previous);
            return URL.createObjectURL(blob);
          });
        } catch {
          setLogoUrl(null);
        }
      } else {
        setLogoUrl(null);
      }
    } catch {
      setMessage({ text: t("settings.brandingLoadError"), error: true });
    }
  }, [requestOptions]);

  useEffect(() => {
    void load();
  }, [load]);

  async function save(event: FormEvent): Promise<void> {
    event.preventDefault();
    const field = (
      name:
        | "commercial_name"
        | "giro"
        | "brand_address"
        | "brand_phone"
        | "brand_email"
        | "notification_email",
    ) => form[name].trim() || null;
    if (!/^#[0-9A-Fa-f]{6}$/.test(form.brand_primary_color)) {
      setMessage({
        text: "El color debe tener # y seis caracteres hexadecimales. Corrige el color antes de guardar.",
        error: true,
      });
      return;
    }
    if (
      !(await confirm({
        title: "Guardar marca",
        body: "La marca y los pies se usarán en nuevas emisiones. Los documentos anteriores conservan su emisor.",
      }))
    )
      return;
    setBusy(true);
    setMessage(null);
    try {
      const response = await organizationBrandingSave(
        {
          expected_updated_at: expected,
          commercial_name: field("commercial_name"),
          giro: field("giro"),
          brand_address: field("brand_address"),
          brand_phone: field("brand_phone"),
          brand_email: field("brand_email"),
          brand_primary_color: form.brand_primary_color,
          document_attribution: form.document_attribution,
          portal_attribution: form.portal_attribution,
          notification_email: field("notification_email"),
          internal_mail_enabled: form.internal_mail_enabled,
        },
        requestOptions,
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      setColorFallback(response.data.brand_color_fallback);
      setExpected(response.data.updated_at);
      setMessage({ text: t("settings.brandingSaved"), error: false });
      if (response.data.updated_at)
        onSaved?.({ previous: expected, updated: response.data.updated_at });
    } catch (error) {
      setMessage({ text: actionErrorDetail(error, t("settings.brandingSaveError")), error: true });
    } finally {
      setBusy(false);
    }
  }

  async function upload(event: FormEvent): Promise<void> {
    event.preventDefault();
    const file = pickFile;
    if (!file) return;
    setBusy(true);
    setMessage(null);
    try {
      const response = await organizationBrandingLogoUpload({ file }, requestOptions);
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      if (pickRef.current) pickRef.current.value = "";
      setPickFile(null);
      setMessage({ text: t("settings.brandingLogoUploaded"), error: false });
      setExpected(response.data.updated_at);
      if (response.data.updated_at)
        onSaved?.({ previous: expected, updated: response.data.updated_at });
      const { blob } = await apiFetchBlob(getOrganizationBrandingLogoReadUrl(), requestOptions);
      setLogoUrl((previous) => {
        if (previous) URL.revokeObjectURL(previous);
        return URL.createObjectURL(blob);
      });
    } catch {
      setMessage({ text: t("settings.brandingSaveError"), error: true });
    } finally {
      setBusy(false);
    }
  }

  async function removeLogo(): Promise<void> {
    setBusy(true);
    setMessage(null);
    try {
      const response = await organizationBrandingLogoDelete(requestOptions);
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      setMessage({ text: t("settings.brandingSaved"), error: false });
      setExpected(response.data.updated_at);
      if (response.data.updated_at)
        onSaved?.({ previous: expected, updated: response.data.updated_at });
      setLogoUrl((previous) => {
        if (previous) URL.revokeObjectURL(previous);
        return null;
      });
    } catch {
      setMessage({ text: t("settings.brandingSaveError"), error: true });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="settings-card">
      <h2 className="eyebrow">{t("settings.branding")}</h2>
      <p className="settings-hint">
        La marca y el pie se sellan al emitir. Los documentos anteriores conservan su identidad.
      </p>
      {colorFallback ? (
        <p role="status">
          El color elegido no alcanza contraste AA contra paper. Usamos teal-800 en tus nuevas
          emisiones; elige un color más oscuro si quieres reemplazarlo.
        </p>
      ) : null}
      {message && <p className={message.error ? "form-error" : "settings-hint"}>{message.text}</p>}
      {message?.error && <Button onClick={() => void load()}>Recargar marca</Button>}
      <div className="settings-branding-preview">
        {logoUrl ? (
          <img
            className="settings-branding-logo"
            src={logoUrl}
            alt={t("settings.brandingLogoAlt")}
          />
        ) : (
          <p className="settings-hint">{t("settings.brandingLogoEmpty")}</p>
        )}
      </div>
      <ValidatedForm className="payments-form" onSubmit={save}>
        <label>
          {t("settings.brandingName")}
          <input
            maxLength={255}
            value={form.commercial_name}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, commercial_name: event.target.value }))
            }
          />
        </label>
        <label>
          {t("settings.brandingGiro")}
          <input
            maxLength={255}
            value={form.giro}
            onChange={(event) => setForm((prev) => ({ ...prev, giro: event.target.value }))}
          />
        </label>
        <label>
          {t("settings.brandingAddress")}
          <input
            maxLength={255}
            value={form.brand_address}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, brand_address: event.target.value }))
            }
          />
        </label>
        <label>
          {t("settings.brandingPhone")}
          <input
            maxLength={64}
            value={form.brand_phone}
            onChange={(event) => setForm((prev) => ({ ...prev, brand_phone: event.target.value }))}
          />
        </label>
        <label>
          {t("settings.brandingEmail")}
          <input
            type="email"
            maxLength={255}
            value={form.brand_email}
            onChange={(event) => setForm((prev) => ({ ...prev, brand_email: event.target.value }))}
          />
        </label>
        <label>
          Color de la marca (#RRGGBB)
          <input
            value={form.brand_primary_color}
            maxLength={7}
            required
            onChange={(event) =>
              setForm((prev) => ({ ...prev, brand_primary_color: event.target.value }))
            }
          />
        </label>
        <label>
          <input
            type="checkbox"
            checked={form.document_attribution}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, document_attribution: event.target.checked }))
            }
          />
          Mostrar «Generado con DEKOPEN» en documentos nuevos
        </label>
        <label>
          <input
            type="checkbox"
            checked={form.portal_attribution}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, portal_attribution: event.target.checked }))
            }
          />
          Mostrar la atribución discreta en portales nuevos
        </label>
        <label>
          Correo para avisos internos
          <input
            type="email"
            value={form.notification_email}
            required={form.internal_mail_enabled}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, notification_email: event.target.value }))
            }
          />
        </label>
        <label>
          <input
            type="checkbox"
            checked={form.internal_mail_enabled}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, internal_mail_enabled: event.target.checked }))
            }
          />
          Enviar avisos internos al recibir una aprobación o bloquear una OT
        </label>
        <div className="payments-form-actions">
          <button type="submit" className="primary-action" disabled={busy}>
            {t("settings.brandingSave")}
          </button>
        </div>
      </ValidatedForm>
      <ValidatedForm className="payments-form" onSubmit={upload}>
        <label>
          {t("settings.brandingLogo")}
          <FilePick
            inputRef={pickRef}
            accept="image/png,image/jpeg,image/webp"
            file={pickFile}
            onFile={setPickFile}
          />
        </label>
        <div className="payments-form-actions">
          <button type="submit" className="primary-action" disabled={busy}>
            {t("settings.brandingLogoUpload")}
          </button>
          {logoUrl && (
            <button type="button" className="secondary-action" disabled={busy} onClick={removeLogo}>
              {t("settings.brandingLogoRemove")}
            </button>
          )}
        </div>
      </ValidatedForm>
    </div>
  );
}

const SETTINGS_SECTIONS = [
  ["account", "Cuenta"],
  ["company", "Empresa"],
  ["design", "Valores habituales"],
  ["prices", "Cómo calculo mis precios"],
  ["users", "Usuarios y roles"],
  ["commercial", "Comercial"],
  ["documents", "Documentos"],
  ["numbering", "Numeración"],
  ["production", "Producción"],
  ["analytics", "Analítica"],
  ["integrations", "Integraciones"],
  ["ai", "Inteligencia artificial"],
] as const;

export function SettingsPage(): JSX.Element {
  const auth = useAuthSession(),
    org = auth.me?.active_organization;
  const [params, setParams] = useSearchParams();
  const section = params.get("section") ?? "company";
  const owner = org?.role === "OWNER",
    commercial = owner || org?.role === "ESTIMATOR";
  const workshop = owner || org?.role === "WORKSHOP_MANAGER";
  const [draft, setDraft] = useState<{ scope: string; value: OrgBrandingWriteRequest }>({
    scope: "",
    value: {},
  });
  const scope = `${org?.id}-${section}`;
  const branding = draft.scope === scope ? draft.value : {};
  const [companyRevision, setCompanyRevision] = useState<{
    orgId: string;
    previous?: string;
    updated: string;
  }>();
  const onBrand = useCallback(
    (value: OrgBrandingWriteRequest) => setDraft({ scope, value }),
    [scope],
  );
  const onDocument = useCallback(
    (value: DocumentPreferences) => setDraft({ scope, value: { document_preferences: value } }),
    [scope],
  );
  if (!org) return <DeniedState reason="Elige tu organización antes de configurar." />;
  return (
    <section
      className="settings"
      data-density={org.role === "OPERATOR" || org.role === "INSTALLER" ? "workshop" : "office"}
      aria-labelledby="page-title"
    >
      <PageHeader title="Ajustes" headingId="page-title" context={org.name} />
      <div className="settings-sections">
        <nav aria-label="Secciones de ajustes">
          {SETTINGS_SECTIONS.map(([key, label]) => (
            <button
              key={key}
              type="button"
              aria-current={section === key ? "page" : undefined}
              onClick={() => setParams({ section: key })}
            >
              {label}
            </button>
          ))}
          <Link to="/settings/billing">Plan y facturación</Link>
          <Link to="/settings/wallet">Créditos de IA</Link>
          {workshop && <Link to="/analytics">Informes</Link>}
          <Link to="/settings/advanced">Funciones avanzadas</Link>
        </nav>
        <div className="settings-content" key={`${org.id}-${section}`}>
          {section === "account" && (
            <>
              <section className="settings-card">
                <h2>Tu cuenta</h2>
                <dl className="settings-list">
                  <div className="settings-row">
                    <dt>Correo</dt>
                    <dd>{auth.me?.user.email}</dd>
                  </div>
                  <div className="settings-row">
                    <dt>Segundo factor</dt>
                    <dd>{auth.me?.aal === "aal2" ? "Verificado" : "Sin verificar"}</dd>
                  </div>
                  <div className="settings-row">
                    <dt>Rol</dt>
                    <dd>{t(ROLE_KEYS[org.role])}</dd>
                  </div>
                </dl>
                <p>
                  Buscar: <kbd>{MOD_K_HINT}</kbd> · Deshacer: <kbd>{MOD_KEY_HINT}Z</kbd>
                </p>
                <Link className="ui-button" to="/auth/mfa?configure=1">
                  Configurar segundo factor
                </Link>
              </section>
              <InterfaceSettings orgId={org.id} />
              <section className="settings-card">
                <h2>Organizaciones</h2>
                <ul className="settings-list">
                  {auth.me?.memberships.map((m) => (
                    <MembershipRow key={m.organization_id} membership={m} />
                  ))}
                </ul>
              </section>
            </>
          )}
          {section === "company" && (
            <div className="settings-with-preview">
              <div>
                <CompanyCard
                  orgId={org.id}
                  canEdit={owner}
                  revision={companyRevision?.orgId === org.id ? companyRevision : undefined}
                  onSaved={(company, previous) =>
                    setCompanyRevision({ orgId: org.id, previous, updated: company.updated_at })
                  }
                />
                {commercial ? (
                  <OrgBrandingCard
                    orgId={org.id}
                    onDraft={onBrand}
                    onSaved={(revision) => setCompanyRevision({ orgId: org.id, ...revision })}
                    companyRevision={
                      companyRevision?.orgId === org.id ? companyRevision : undefined
                    }
                  />
                ) : (
                  <DeniedState reason="El dueño o estimador configura la marca de documentos." />
                )}
              </div>
              {commercial && <DocumentPreview orgId={org.id} branding={branding} />}
            </div>
          )}
          {section === "design" && <CompanyDesignDefaults orgId={org.id} canEdit={commercial} />}
          {section === "prices" && <SimplePricingSettings orgId={org.id} owner={owner} />}
          {section === "users" && <UsersCard orgId={org.id} canEdit={owner} />}
          {section === "commercial" && (
            <div className="settings-with-preview">
              <div>
                {commercial ? (
                  <DocumentSettings
                    orgId={org.id}
                    canEdit={commercial}
                    section="commercial"
                    onDraft={onDocument}
                  />
                ) : (
                  <DeniedState reason="El dueño o estimador configura condiciones comerciales." />
                )}
                <ExtraPolicyEditor orgId={org.id} canWrite={owner} />
              </div>
              {commercial && <DocumentPreview orgId={org.id} branding={branding} />}
            </div>
          )}
          {section === "documents" && (
            <div className="settings-with-preview">
              <div>
                {commercial ? (
                  <DocumentSettings
                    orgId={org.id}
                    canEdit={commercial}
                    section="documents"
                    onDraft={onDocument}
                  />
                ) : (
                  <DeniedState reason="El dueño o estimador configura los documentos de la empresa." />
                )}
              </div>
              {commercial && <DocumentPreview orgId={org.id} branding={branding} />}
            </div>
          )}
          {section === "numbering" && (
            <>
              <QuotationNumberingCard orgId={org.id} canEdit={owner} />
              <NumberingCard orgId={org.id} />
            </>
          )}
          {section === "analytics" &&
            (workshop ? (
              <AnalyticsPreferences orgId={org.id} canEdit={owner} />
            ) : (
              <DeniedState reason="El dueño y el jefe de taller consultan la configuración de analítica." />
            ))}
          {section === "production" && (
            <>
              {["OWNER", "ESTIMATOR", "WORKSHOP_MANAGER"].includes(org.role) ? (
                <>
                  <SiteMeasurementSettings orgId={org.id} canEdit={owner} />
                  <ProductionSettings orgId={org.id} canEdit={workshop} />
                  <DocumentSettings orgId={org.id} canEdit={commercial} section="production" />
                  <MountingRulesSettings orgId={org.id} canWrite={workshop} />
                  <GlassRulesSettings orgId={org.id} canWrite={workshop} />
                </>
              ) : (
                <DeniedState reason="El dueño o jefe de taller configura estaciones, montaje y materiales." />
              )}
            </>
          )}
          {section === "integrations" && (
            <>
              {owner && <ActivationGuide orgId={org.id} />}
              {owner ? (
                <>
                  <CollectionIntegrations orgId={org.id} />
                  <details className="settings-card">
                    <summary>Conectar Flow</summary>
                    <FlowIntegrationCard orgId={org.id} />
                  </details>
                  <MailIntegrationCard orgId={org.id} />
                  <details className="settings-card">
                    <summary>Configurar emisión SII</summary>
                    <SiiCafCard orgId={org.id} />
                    <SiiCertificateCard orgId={org.id} />
                  </details>
                </>
              ) : (
                <DeniedState reason="El dueño configura conexiones y consulta sus credenciales protegidas." />
              )}
            </>
          )}
          {section === "ai" &&
            (owner ? (
              <AiSettingsSection orgId={org.id} />
            ) : (
              <DeniedState reason="El dueño configura proveedor, rutas y presupuesto de IA." />
            ))}
          {!SETTINGS_SECTIONS.some(([key]) => key === section) && (
            <p>Esta sección no existe. Elige una sección de Ajustes.</p>
          )}
        </div>
      </div>
    </section>
  );
}
