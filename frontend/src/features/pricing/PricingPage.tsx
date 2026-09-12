import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { apiMutator, ApiError } from "../../api/apiMutator";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { t } from "../../i18n/es-CL";
import { useCanvasStore } from "../canvas/canvasStore";
import "./pricing.css";

const modes = [
  "COST_PLUS_MARGIN",
  "PRICE_PER_M2_BY_TYPOLOGY",
  "FIXED_PRICE_MATRIX_DIMENSIONAL",
  "TARGET_GROSS_MARGIN_PROJECT",
  "COMMERCIAL_LIST_WITH_DISCOUNTS",
];
const optionLabels: Record<string, Parameters<typeof t>[0]> = {
  COST_PLUS_MARGIN: "pricing.mode1",
  PRICE_PER_M2_BY_TYPOLOGY: "pricing.mode2",
  FIXED_PRICE_MATRIX_DIMENSIONAL: "pricing.mode3",
  TARGET_GROSS_MARGIN_PROJECT: "pricing.mode4",
  COMMERCIAL_LIST_WITH_DISCOUNTS: "pricing.mode5",
  PROFILE: "pricing.profile",
  GLASS: "pricing.glass",
  HARDWARE: "pricing.hardware",
  PANEL: "pricing.panel",
  ACCESSORY: "pricing.accessory",
  BAR: "pricing.bar",
  M: "pricing.metre",
  M2: "pricing.squareMetre",
  KIT: "pricing.kit",
  UNIT: "pricing.each",
  FIXED: "pricing.fixed",
  TURN: "pricing.turn",
  TILT_TURN: "pricing.tiltTurn",
  SLIDING_2L: "pricing.sliding",
  DOOR_ENTRY: "pricing.door",
  AWNING: "pricing.awning",
  RETAIL: "pricing.retail",
  ARCHITECT: "pricing.architect",
  CONSTRUCTION: "pricing.construction",
};
function optionLabel(value: string): string {
  const key = optionLabels[value];
  return key ? t(key) : value;
}
type Field = {
  name: string;
  label: Parameters<typeof t>[0];
  type?: string;
  options?: string[];
  initial?: string;
  optional?: boolean;
};
const fields: Record<string, Field[]> = {
  "cost-lists": [
    { name: "supplier_name", label: "pricing.supplier" },
    { name: "description", label: "pricing.description", optional: true },
    { name: "currency", label: "pricing.currency", options: ["CLP", "USD"] },
    { name: "valid_from", label: "pricing.from", type: "date" },
    { name: "valid_to", label: "pricing.until", type: "date", optional: true },
  ],
  "cost-items": [
    { name: "cost_list_id", label: "pricing.listId" },
    { name: "sku", label: "pricing.sku" },
    {
      name: "item_type",
      label: "pricing.itemType",
      options: ["PROFILE", "GLASS", "HARDWARE", "PANEL", "ACCESSORY"],
    },
    { name: "unit", label: "pricing.unit", options: ["BAR", "M", "M2", "KIT", "UNIT"] },
    { name: "unit_cost", label: "pricing.cost" },
  ],
  rules: [
    { name: "pricing_mode", label: "pricing.mode", options: modes },
    { name: "default_margin_pct", label: "pricing.margin", initial: "0.35" },
    { name: "tax_rate_pct", label: "pricing.tax", initial: "0.19" },
    { name: "waste_factor_pct", label: "pricing.waste", initial: "0.08" },
    { name: "labor_rate_per_m2", label: "pricing.labor", initial: "15000" },
    { name: "installation_rate_per_m2", label: "pricing.installation", initial: "12000" },
  ],
  configurations: [
    { name: "context_code", label: "pricing.context", initial: "DEFAULT" },
    {
      name: "typology",
      label: "pricing.typology",
      options: ["FIXED", "TURN", "TILT_TURN", "SLIDING_2L", "DOOR_ENTRY", "AWNING"],
    },
    { name: "pricing_mode", label: "pricing.mode", options: modes },
    { name: "currency", label: "pricing.currency", options: ["CLP", "USD"] },
    { name: "rate_per_m2", label: "pricing.rate", optional: true },
    { name: "base_glass_sku", label: "pricing.baseGlass", optional: true },
    { name: "catalog_price", label: "pricing.catalogPrice", optional: true },
  ],
  "matrix-cells": [
    { name: "configuration_id", label: "pricing.configurationId" },
    { name: "width_mm", label: "pricing.width", type: "number" },
    { name: "height_mm", label: "pricing.height", type: "number" },
    { name: "price", label: "pricing.price" },
  ],
  fx: [
    { name: "base_currency", label: "pricing.baseCurrency", options: ["USD"] },
    { name: "quote_currency", label: "pricing.quoteCurrency", options: ["CLP"] },
    { name: "observed_rate", label: "pricing.fxRate" },
    { name: "observed_date", label: "pricing.observedDate", type: "date" },
    { name: "effective_date", label: "pricing.effectiveDate", type: "date" },
    { name: "source", label: "pricing.source" },
  ],
};
const sections = [
  "cost-lists",
  "cost-items",
  "rules",
  "configurations",
  "matrix-cells",
  "fx",
  "audits",
] as const;
const sectionLabels = [
  "pricing.lists",
  "pricing.items",
  "pricing.rules",
  "pricing.configurations",
  "pricing.matrix",
  "pricing.fx",
  "pricing.audits",
] as const;
type Row = Record<string, string | boolean | null>;

function usePricingRequest(orgId: string): RequestFn {
  const lifetime = useRef(new AbortController());
  useEffect(() => {
    const controller = new AbortController();
    lifetime.current = controller;
    return () => controller.abort();
  }, []);
  return useCallback(
    async <T,>(path: string, method = "GET", body?: unknown): Promise<T> => {
      const form = body instanceof FormData;
      const response = await apiMutator<{ data: T }>(`/api/v1/pricing/${path}`, {
        method,
        signal: lifetime.current.signal,
        headers: {
          "X-Organization-ID": orgId,
          ...(form ? {} : { "Content-Type": "application/json" }),
        },
        ...(body === undefined ? {} : { body: form ? body : JSON.stringify(body) }),
      });
      return response.data;
    },
    [orgId],
  );
}

export function CommercialPricingPage(): JSX.Element {
  const org = useAuthSession().me?.active_organization;
  if (!org || !["OWNER", "ESTIMATOR"].includes(org.role))
    return <p role="alert">{t("pricing.commercialDenied")}</p>;
  return <CommercialWorkspace key={org.id} orgId={org.id} owner={org.role === "OWNER"} />;
}

function CommercialWorkspace({ orgId, owner }: { orgId: string; owner: boolean }): JSX.Element {
  const request = usePricingRequest(orgId);
  return (
    <section className="pricing-page">
      <CommercialOperations request={request} owner={owner} />
    </section>
  );
}

export function PricingPage(): JSX.Element {
  const auth = useAuthSession();
  const org = auth.me?.active_organization;
  if (!org || org.role !== "OWNER") return <p role="alert">{t("pricing.ownerOnly")}</p>;
  return <PricingWorkspace key={org.id} orgId={org.id} />;
}

function PricingWorkspace({ orgId }: { orgId: string }): JSX.Element {
  const [resource, setResource] = useState<string>("cost-lists");
  const [items, setItems] = useState<Row[]>([]);
  const [costLists, setCostLists] = useState<Row[]>([]);
  const [configurations, setConfigurations] = useState<Row[]>([]);
  const [editing, setEditing] = useState<Row | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [revision, setRevision] = useState(0);
  const lifetime = useRef<AbortController>(new AbortController());
  useEffect(() => {
    const controller = new AbortController();
    lifetime.current = controller;
    return () => controller.abort();
  }, []);
  async function request<T>(path: string, method = "GET", body?: unknown): Promise<T> {
    const form = body instanceof FormData;
    const response = await apiMutator<{ data: T }>(`/api/v1/pricing/${path}`, {
      method,
      signal: lifetime.current.signal,
      headers: {
        "X-Organization-ID": orgId,
        ...(form ? {} : { "Content-Type": "application/json" }),
      },
      ...(body === undefined ? {} : { body: form ? body : JSON.stringify(body) }),
    });
    return response.data;
  }
  useEffect(() => {
    let current = true;
    setItems([]);
    setEditing(null);
    setMessage("");
    setBusy(true);
    void request<{ items: Row[] }>(`admin/${resource}/`)
      .then((response) => {
        if (current) {
          setItems(response.items);
          if (resource === "cost-lists") setCostLists(response.items);
          if (resource === "configurations") setConfigurations(response.items);
        }
      })
      .catch(() => {
        if (current) setMessage(t("pricing.loadError"));
      })
      .finally(() => {
        if (current) setBusy(false);
      });
    if (resource === "matrix-cells") {
      void request<{ items: Row[] }>("admin/configurations/")
        .then((response) => {
          if (current) setConfigurations(response.items);
        })
        .catch(() => {
          if (current) setMessage(t("pricing.loadError"));
        });
    }
    return () => {
      current = false;
    };
    // The workspace remounts for each organization; resource/revision own reloads.
  }, [resource, revision]);

  async function save(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const values: Record<string, unknown> = {};
    for (const field of fields[resource] ?? []) {
      const value = String(data.get(field.name) ?? "");
      if (field.optional && value === "") {
        if (field.name !== "description") values[field.name] = null;
        else values[field.name] = "";
        continue;
      }
      values[field.name] = field.type === "number" ? Number(value) : value;
    }
    if (resource === "cost-lists" || resource === "configurations")
      values.is_active = data.get("is_active") === "on";
    setBusy(true);
    setMessage("");
    try {
      await request(`admin/${resource}/`, "POST", {
        ...(editing ? { id: editing.id } : {}),
        values,
        reason: data.get("reason"),
      });
      if (!lifetime.current.signal.aborted) {
        setEditing(null);
        setRevision((value) => value + 1);
      }
    } catch (error) {
      if (!lifetime.current.signal.aborted)
        setMessage(
          t(
            error instanceof ApiError && error.status === 409
              ? "pricing.conflict"
              : "pricing.saveError",
          ),
        );
    } finally {
      if (!lifetime.current.signal.aborted) setBusy(false);
    }
  }

  return (
    <section className="pricing-page">
      <header>
        <h1>{t("pricing.title")}</h1>
        <p>{t("pricing.subtitle")}</p>
      </header>
      <nav aria-label={t("pricing.sections")} className="pricing-tabs">
        {sections.map((name, index) => (
          <button
            key={name}
            type="button"
            aria-pressed={resource === name}
            disabled={busy}
            onClick={() => setResource(name)}
          >
            {t(sectionLabels[index]!)}
          </button>
        ))}
      </nav>
      {message && <p role="alert">{message}</p>}
      {busy && <p role="status">{t("pricing.loading")}</p>}
      <div className="pricing-grid">
        <div className="pricing-records">
          <button type="button" disabled={busy} onClick={() => setRevision((value) => value + 1)}>
            {t("pricing.reload")}
          </button>
          {!busy && items.length === 0 && <p>{t("pricing.empty")}</p>}
          {items.map((item) => (
            <article key={String(item.id)}>
              <strong>
                {String(
                  item.supplier_name ??
                    item.sku ??
                    item.context_code ??
                    item.source ??
                    item.entity ??
                    t("pricing.rules"),
                )}
              </strong>
              <dl>
                {(
                  fields[resource] ?? [
                    { name: "reason", label: "pricing.reason" as const },
                    { name: "created_at", label: "pricing.created" as const },
                  ]
                ).map((field) => (
                  <div key={field.name}>
                    <dt>{t(field.label)}</dt>
                    <dd>{String(item[field.name] ?? "—")}</dd>
                  </div>
                ))}
              </dl>
              {resource !== "audits" && resource !== "fx" && (
                <button type="button" disabled={busy} onClick={() => setEditing(item)}>
                  {t("pricing.edit")}
                </button>
              )}
            </article>
          ))}
        </div>
        {fields[resource] && (
          <form
            key={`${resource}-${editing?.id ?? "new"}-${revision}`}
            onSubmit={(event) => void save(event)}
            className="pricing-form"
          >
            <h2>{t(editing ? "pricing.editRecord" : "pricing.newRecord")}</h2>
            {fields[resource].map((field) => (
              <label key={field.name}>
                {t(field.label)}
                {field.name === "cost_list_id" || field.name === "configuration_id" ? (
                  <select
                    name={field.name}
                    required
                    disabled={busy}
                    defaultValue={String(editing?.[field.name] ?? "")}
                  >
                    <option value="">{t("pricing.chooseAuthority")}</option>
                    {(field.name === "cost_list_id" ? costLists : configurations).map((row) => (
                      <option key={String(row.id)} value={String(row.id)}>
                        {field.name === "cost_list_id"
                          ? `${row.supplier_name} · ${row.currency} · ${row.valid_from}`
                          : `${row.context_code} · ${optionLabel(String(row.typology))} · ${optionLabel(String(row.pricing_mode))}`}
                      </option>
                    ))}
                  </select>
                ) : field.options ? (
                  <select
                    name={field.name}
                    defaultValue={String(
                      editing?.[field.name] ?? field.initial ?? field.options[0],
                    )}
                    disabled={busy}
                  >
                    {field.options.map((value) => (
                      <option key={value} value={value}>
                        {optionLabel(value)}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    name={field.name}
                    type={field.type ?? "text"}
                    required={!field.optional}
                    defaultValue={String(editing?.[field.name] ?? field.initial ?? "")}
                    disabled={busy}
                  />
                )}
              </label>
            ))}
            {(resource === "cost-lists" || resource === "configurations") && (
              <label>
                <input
                  type="checkbox"
                  name="is_active"
                  defaultChecked={editing?.is_active !== false}
                  disabled={busy}
                />
                {t("pricing.active")}
              </label>
            )}
            <label>
              {t("pricing.reason")}
              <input name="reason" required maxLength={1000} disabled={busy} />
            </label>
            <button type="submit" disabled={busy}>
              {t("pricing.save")}
            </button>
            {editing && (
              <button type="button" disabled={busy} onClick={() => setEditing(null)}>
                {t("pricing.cancel")}
              </button>
            )}
          </form>
        )}
      </div>
      <ImportCosts
        request={request}
        costLists={costLists}
        onSaved={() => setRevision((value) => value + 1)}
      />
      <CommercialOperations request={request} owner />
    </section>
  );
}

type RequestFn = <T>(path: string, method?: string, body?: unknown) => Promise<T>;
function ImportCosts({
  request,
  costLists,
  onSaved,
}: {
  request: RequestFn;
  costLists: Row[];
  onSaved: () => void;
}): JSX.Element {
  const [preview, setPreview] = useState<Row[]>([]);
  const [pending, setPending] = useState<FormData | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const inputRevision = useRef(0);
  const requestSequence = useRef(0);
  const activeRequest = useRef<{ id: number; apply: boolean } | null>(null);
  const pendingAuthority = useRef<FormData | null>(null);
  const mounted = useRef(false);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      inputRevision.current += 1;
      activeRequest.current = null;
      pendingAuthority.current = null;
    };
  }, []);
  async function run(form: FormData, apply: boolean): Promise<void> {
    if (!mounted.current) return;
    if (apply) {
      if (activeRequest.current !== null || pendingAuthority.current !== form) return;
      pendingAuthority.current = null;
    } else if (activeRequest.current?.apply) {
      return;
    }
    const revision = inputRevision.current;
    const body = new FormData();
    form.forEach((value, key) => {
      body.append(key, value);
    });
    body.set("apply", String(apply));
    const id = ++requestSequence.current;
    activeRequest.current = { id, apply };
    pendingAuthority.current = null;
    setPreview([]);
    setPending(null);
    setError("");
    setBusy(true);
    try {
      const response = await request<{ items: Row[] }>("import/", "POST", body);
      const current = mounted.current && activeRequest.current?.id === id;
      const fresh = revision === inputRevision.current;
      if (current && fresh) {
        setPreview(response.items);
        if (!apply) {
          pendingAuthority.current = body;
          setPending(body);
        }
      }
    } catch {
      const current = mounted.current && activeRequest.current?.id === id;
      const fresh = revision === inputRevision.current;
      if (current && fresh) {
        setError(t("pricing.importError"));
        setPending(null);
      }
    } finally {
      if (mounted.current && activeRequest.current?.id === id) {
        activeRequest.current = null;
        setBusy(false);
        if (apply) onSaved();
      }
    }
  }
  return (
    <section className="pricing-import">
      <h2>{t("pricing.import")}</h2>
      <form
        onChange={() => {
          inputRevision.current += 1;
          pendingAuthority.current = null;
          setPending(null);
          setPreview([]);
          setError("");
        }}
        onSubmit={(event) => {
          event.preventDefault();
          const form = new FormData(event.currentTarget);
          form.set(
            "mapping",
            JSON.stringify(
              Object.fromEntries(
                ["sku", "description", "unit", "unit_cost"].map((key) => [
                  key,
                  form.get(`column_${key}`),
                ]),
              ),
            ),
          );
          void run(form, false);
        }}
      >
        <label>
          {t("pricing.listId")}
          <select name="cost_list_id" required defaultValue="">
            <option value="">{t("pricing.chooseAuthority")}</option>
            {costLists.map((row) => (
              <option key={String(row.id)} value={String(row.id)}>
                {String(row.supplier_name)} · {String(row.currency)} · {String(row.valid_from)}
              </option>
            ))}
          </select>
        </label>
        <label>
          {t("pricing.file")}
          <input type="file" accept=".xlsx" name="file" required />
        </label>
        {["sku", "description", "unit", "unit_cost"].map((key, index) => (
          <label key={key}>
            {t("pricing.column")} ·{" "}
            {t(
              ["pricing.sku", "pricing.description", "pricing.unit", "pricing.cost"][
                index
              ] as Parameters<typeof t>[0],
            )}
            <input
              name={`column_${key}`}
              required
              defaultValue={["SKU", "Descripción", "Unidad", "Precio Unitario"][index]}
            />
          </label>
        ))}
        <label>
          {t("pricing.separator")}
          <select name="decimal_separator">
            <option value=".">.</option>
            <option value=",">,</option>
          </select>
        </label>
        <label>
          {t("pricing.reason")}
          <input name="reason" required />
        </label>
        <button disabled={busy}>{t("pricing.previewImport")}</button>
      </form>
      {error && <p role="alert">{error}</p>}
      {preview.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>{t("pricing.sku")}</th>
              <th>{t("pricing.unit")}</th>
              <th>{t("pricing.cost")}</th>
            </tr>
          </thead>
          <tbody>
            {preview.map((row) => (
              <tr key={String(row.sku)}>
                <td>{String(row.sku)}</td>
                <td>{String(row.unit)}</td>
                <td>{String(row.unit_cost)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {pending && (
        <button disabled={busy} onClick={() => void run(pending, true)}>
          {t("pricing.confirmImport")}
        </button>
      )}
    </section>
  );
}

type Operation = {
  id: string;
  project_id: string;
  discount_pct: string;
  state: string;
  project_net: string;
  project_tax: string;
  project_gross: string;
  currency: string;
};
function CommercialOperations({
  request,
  owner,
}: {
  request: RequestFn;
  owner: boolean;
}): JSX.Element {
  const [operation, setOperation] = useState<Operation | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [reason, setReason] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [projectId, setProjectId] = useState("");
  const [selectedMode, setSelectedMode] = useState("COST_PLUS_MARGIN");
  const [history, setHistory] = useState<Operation[]>([]);
  const generation = useRef(0);
  useEffect(
    () => () => {
      generation.current += 1;
    },
    [],
  );
  function invalidate(): void {
    generation.current += 1;
    setBusy(false);
    setError("");
  }
  async function runCurrent<T>(
    action: () => Promise<T>,
    publish: (value: T) => void,
    errorKey: Parameters<typeof t>[0],
  ): Promise<void> {
    const current = ++generation.current;
    setBusy(true);
    setError("");
    try {
      const value = await action();
      if (generation.current === current) publish(value);
    } catch {
      if (generation.current === current) setError(t(errorKey));
    } finally {
      if (generation.current === current) setBusy(false);
    }
  }
  function reload(): Promise<void> {
    return runCurrent(() => request<Operation[]>("operations/"), setHistory, "pricing.loadError");
  }
  function apply(reject = false): Promise<void> {
    if (!operation) return Promise.resolve();
    return runCurrent(
      () =>
        request<Operation>(`operations/${operation.id}/apply/`, "POST", {
          reason,
          confirmed,
          ...(reject ? { reject: true } : {}),
        }),
      setOperation,
      "pricing.applyError",
    );
  }
  return (
    <section>
      <h2>{t("pricing.calculate")}</h2>
      <CommercialDraft
        request={request}
        onCreated={(id) => {
          invalidate();
          setOperation(null);
          setProjectId(id);
        }}
      />
      <form
        onChange={(event) => {
          const target = event.target as HTMLInputElement;
          if (target.name === "reason" || target.name === "confirmed") return;
          invalidate();
          setOperation(null);
        }}
        onSubmit={(event) => {
          event.preventDefault();
          const data = Object.fromEntries(new FormData(event.currentTarget));
          if (data.fx_snapshot_id === "") delete data.fx_snapshot_id;
          void runCurrent(
            () => request<Operation>("preview/", "POST", { ...data, confirmed }),
            setOperation,
            "pricing.calculateError",
          );
        }}
      >
        <label>
          {t("pricing.projectId")}
          <input
            name="project_id"
            required
            value={projectId}
            onChange={(event) => setProjectId(event.target.value)}
          />
        </label>
        <label>
          {t("pricing.mode")}
          <select
            name="pricing_mode"
            value={selectedMode}
            onChange={(event) => setSelectedMode(event.target.value)}
          >
            {modes
              .filter((mode) => owner || mode !== "TARGET_GROSS_MARGIN_PROJECT")
              .map((mode) => (
                <option key={mode} value={mode}>
                  {optionLabel(mode)}
                </option>
              ))}
          </select>
        </label>
        <label>
          {t("pricing.context")}
          <input name="context_code" defaultValue="DEFAULT" required />
        </label>
        <label>
          {t("pricing.currency")}
          <select name="currency">
            <option>CLP</option>
            <option>USD</option>
          </select>
        </label>
        <label>
          {t("pricing.effectiveDate")}
          <input name="effective_date" type="date" required />
        </label>
        <label>
          {t("pricing.fxId")}
          <input name="fx_snapshot_id" />
        </label>
        <label>
          {t("pricing.discount")}
          <input name="discount_pct" defaultValue="0" required />
        </label>
        {selectedMode === "TARGET_GROSS_MARGIN_PROJECT" && (
          <label>
            {t("pricing.margin")}
            <input name="target_margin" defaultValue="0.35" required />
          </label>
        )}
        <label>
          {t("pricing.segment")}
          <select name="segment">
            {["RETAIL", "ARCHITECT", "CONSTRUCTION"].map((value) => (
              <option key={value} value={value}>
                {optionLabel(value)}
              </option>
            ))}
          </select>
        </label>
        <label>
          {t("pricing.reason")}
          <input
            name="reason"
            required
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
        </label>
        <label>
          <input
            type="checkbox"
            name="confirmed"
            checked={confirmed}
            onChange={(event) => setConfirmed(event.target.checked)}
          />
          {t("pricing.confirmDiscount")}
        </label>
        <button disabled={busy}>{t("pricing.preview")}</button>
      </form>
      {error && <p role="alert">{error}</p>}
      {operation && (
        <article>
          <p>
            {t("pricing.projectId")}: {operation.project_id}
          </p>
          <p>
            {t("pricing.discount")}: {operation.discount_pct}
          </p>
          <p>
            {t("pricing.net")}: {operation.project_net} {operation.currency}
          </p>
          <p>
            {t("pricing.taxTotal")}: {operation.project_tax}
          </p>
          <strong>
            {t("pricing.gross")}: {operation.project_gross}
          </strong>
          <p>{t(operation.state === "APPLIED" ? "pricing.applied" : "pricing.notApplied")}</p>
          {["PREVIEW", "PENDING"].includes(operation.state) &&
            (owner || operation.state !== "PENDING") && (
              <button disabled={busy || !reason.trim()} onClick={() => void apply()}>
                {t("pricing.apply")}
              </button>
            )}
          {owner && operation.state === "PENDING" && (
            <button
              type="button"
              disabled={busy || !reason.trim()}
              onClick={() => void apply(true)}
            >
              {t("pricing.reject")}
            </button>
          )}
        </article>
      )}
      <h2>{t("pricing.history")}</h2>
      <button type="button" disabled={busy} onClick={() => void reload()}>
        {t("pricing.reload")}
      </button>
      {history.map((item) => (
        <article key={item.id}>
          <p>
            {item.project_net} {item.currency}
          </p>
          <p>
            {t(
              item.state === "PENDING"
                ? "pricing.pending"
                : item.state === "APPLIED"
                  ? "pricing.applied"
                  : item.state === "REJECTED"
                    ? "pricing.rejected"
                    : "pricing.notApplied",
            )}
          </p>
          <button
            type="button"
            disabled={busy}
            onClick={() => {
              invalidate();
              setOperation(item);
              setReason("");
              setConfirmed(false);
            }}
          >
            {t("pricing.review")}
          </button>
        </article>
      ))}
    </section>
  );
}

function CommercialDraft({
  request,
  onCreated,
}: {
  request: RequestFn;
  onCreated: (id: string) => void;
}): JSX.Element {
  const inputs = useCanvasStore((state) => state.inputs);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  if (!inputs.systemId)
    return (
      <p>
        <a href="/projects/demo/positions/g1/edit">{t("pricing.prepareDesign")}</a>
      </p>
    );
  return (
    <details>
      <summary>{t("pricing.createDraft")}</summary>
      <p>
        {inputs.nominalWidthMm} × {inputs.nominalHeightMm} mm
      </p>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          const data = Object.fromEntries(new FormData(event.currentTarget));
          setBusy(true);
          setError("");
          void request<{ id: string }>("drafts/", "POST", {
            code: data.code,
            name: data.name,
            client_name: data.client_name,
            reason: data.reason,
            positions: [
              {
                system_id: inputs.systemId,
                nominal_width_mm: inputs.nominalWidthMm,
                nominal_height_mm: inputs.nominalHeightMm,
                color: inputs.color,
                parametric_tree: { ...inputs.parametricTree, glass_article_sku: data.glass_sku },
                position_index: 1,
                quantity: Number(data.quantity),
                typology: "FIXED",
              },
            ],
          })
            .then((value) => onCreated(value.id))
            .catch(() => setError(t("pricing.saveError")))
            .finally(() => setBusy(false));
        }}
      >
        <label>
          {t("pricing.projectCode")}
          <input name="code" required disabled={busy} />
        </label>
        <label>
          {t("pricing.projectName")}
          <input name="name" required disabled={busy} />
        </label>
        <label>
          {t("pricing.client")}
          <input name="client_name" required disabled={busy} />
        </label>
        <label>
          {t("pricing.selectedGlass")}
          <input name="glass_sku" required disabled={busy} />
        </label>
        <label>
          {t("pricing.quantity")}
          <input
            name="quantity"
            type="number"
            min="1"
            step="1"
            defaultValue="1"
            required
            disabled={busy}
          />
        </label>
        <label>
          {t("pricing.reason")}
          <input name="reason" required disabled={busy} />
        </label>
        <button disabled={busy}>{t("pricing.createDraft")}</button>
      </form>
      {error && <p role="alert">{error}</p>}
    </details>
  );
}
