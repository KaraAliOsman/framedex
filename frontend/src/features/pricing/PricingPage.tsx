import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";

import { projectsList, projectsRetrieve } from "../../api/generated/dekopen";

import type { PriceResponse, ProjectResponse } from "../../api/generated/models";
import { formatDateTime } from "../../format";
import { formatMoney } from "../money";
import { apiMutator, ApiError } from "../../api/apiMutator";
import { actionErrorDetail } from "../errors";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { DeniedState } from "../../ui";
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
  COMPOSITE: "pricing.composite",
  RETAIL: "pricing.retail",
  ARCHITECT: "pricing.architect",
  CONSTRUCTION: "pricing.construction",
};
function optionLabel(value: string): string {
  const key = optionLabels[value];
  return key ? t(key) : value;
}
/** The seeded DEFAULT context is a real value, not a display string — render
 * the operator-facing label everywhere it surfaces (review m2). */
function contextLabel(value: unknown): string {
  return value === "DEFAULT" ? t("pricing.contextDefault") : String(value);
}

const ISO_DAY = /^(\d{4})-(\d{2})-(\d{2})/;
/** Rates store as fractions (0.35); people think in percents. Render the
 * percent value with at most two decimals — never float artifacts. */
function pctDisplay(value: unknown): string {
  const pct = Number(value) * 100;
  if (!Number.isFinite(pct)) return "0";
  return pct.toFixed(2).replace(/\.?0+$/, "");
}
/** Stored values are ISO; operators read DD-MM-AAAA everywhere else in the
 * product. Render the business format, keep the raw value for submission. */
function renderFieldValue(field: Field, value: unknown): string {
  if (value === undefined || value === null || value === "") return "—";
  const text = String(value);
  if (field.type === "date") {
    const match = ISO_DAY.exec(text);
    if (match) return `${match[3]}-${match[2]}-${match[1]}`;
  }
  if (field.type === "percent") return `${pctDisplay(text)} %`;
  if (field.name === "created_at") return formatDateTime(text);
  if (field.name === "entity") return t(auditEntityLabels[text] ?? "pricing.auditEntity.other");
  if (field.name === "field") return t(auditActionLabels[text] ?? "pricing.auditAction.other");
  if (field.name === "actor_type") return t(auditActorLabels[text] ?? "pricing.auditActor.other");
  return text;
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
    { name: "default_margin_pct", label: "pricing.margin", type: "percent", initial: "35" },
    { name: "tax_rate_pct", label: "pricing.tax", type: "percent", initial: "19" },
    { name: "waste_factor_pct", label: "pricing.waste", type: "percent", initial: "8" },
    { name: "labor_rate_per_m2", label: "pricing.labor", initial: "15000" },
    { name: "installation_rate_per_m2", label: "pricing.installation", initial: "12000" },
  ],
  configurations: [
    { name: "context_code", label: "pricing.context", initial: "DEFAULT" },
    {
      name: "typology",
      label: "pricing.typology",
      options: ["FIXED", "TURN", "TILT_TURN", "SLIDING_2L", "DOOR_ENTRY", "AWNING", "COMPOSITE"],
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
  audits: [
    { name: "entity", label: "pricing.auditEntity" },
    { name: "field", label: "pricing.auditAction" },
    { name: "reason", label: "pricing.reason" },
    { name: "actor_type", label: "pricing.auditActor" },
    { name: "created_at", label: "pricing.created" },
  ],
};
// Audit rows carry raw storage names (entity = table, field = SQL verb);
// people read domain nouns and past-tense actions.
const auditEntityLabels: Record<string, Parameters<typeof t>[0]> = {
  price_audit_logs: "pricing.auditEntity.priceAuditLogs",
  price_lists: "pricing.auditEntity.priceLists",
  price_list_items: "pricing.auditEntity.priceListItems",
  pricing_configurations: "pricing.auditEntity.pricingConfigurations",
  pricing_matrix_cells: "pricing.auditEntity.pricingMatrixCells",
  pricing_operations: "pricing.auditEntity.pricingOperations",
  pricing_rules: "pricing.auditEntity.pricingRules",
  project_positions: "pricing.auditEntity.projectPositions",
  fx_snapshots: "pricing.auditEntity.fxSnapshots",
};
const auditActionLabels: Record<string, Parameters<typeof t>[0]> = {
  INSERT: "pricing.auditAction.insert",
  UPDATE: "pricing.auditAction.update",
  DELETE: "pricing.auditAction.delete",
};
const auditActorLabels: Record<string, Parameters<typeof t>[0]> = {
  HUMAN: "pricing.auditActor.human",
  SYSTEM: "pricing.auditActor.system",
  AI_AGENT: "pricing.auditActor.ai",
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
  // Each request gets its own controller, registered in a live set aborted on
  // unmount. A single shared controller cannot work: a child effect (e.g. the
  // mount history load) may fire before this component's own effect assigns
  // it, and StrictMode's remount must not cancel requests issued afterwards.
  const live = useRef<Set<AbortController>>(new Set());
  useEffect(() => {
    const controllers = live.current;
    return () => {
      controllers.forEach((controller) => controller.abort());
      controllers.clear();
    };
  }, []);
  return useCallback(
    async <T,>(path: string, method = "GET", body?: unknown): Promise<T> => {
      const form = body instanceof FormData;
      const controller = new AbortController();
      live.current.add(controller);
      try {
        const response = await apiMutator<{ data: T }>(`/api/v1/pricing/${path}`, {
          method,
          signal: controller.signal,
          headers: {
            "X-Organization-ID": orgId,
            ...(form ? {} : { "Content-Type": "application/json" }),
          },
          ...(body === undefined ? {} : { body: form ? body : JSON.stringify(body) }),
        });
        return response.data;
      } finally {
        live.current.delete(controller);
      }
    },
    [orgId],
  );
}

export function CommercialPricingPage(): JSX.Element {
  const { id: projectId } = useParams();
  const org = useAuthSession().me?.active_organization;
  if (!org || !["OWNER", "ESTIMATOR"].includes(org.role))
    return <DeniedState reason={t("pricing.commercialDenied")} />;
  return (
    <CommercialWorkspace
      key={`${org.id}:${projectId ?? ""}`}
      orgId={org.id}
      owner={org.role === "OWNER"}
      projectId={projectId}
    />
  );
}

function CommercialWorkspace({
  orgId,
  owner,
  projectId,
}: {
  orgId: string;
  owner: boolean;
  projectId?: string;
}): JSX.Element {
  const request = usePricingRequest(orgId);
  return (
    <section className="pricing-page">
      {projectId && (
        <Link className="ui-backlink ui-backlink--back" to={`/projects/${projectId}`}>
          {t("projects.back")}
        </Link>
      )}
      <CommercialOperations request={request} owner={owner} boundProjectId={projectId} />
    </section>
  );
}

export function PricingPage(): JSX.Element {
  const auth = useAuthSession();
  const org = auth.me?.active_organization;
  if (!org || org.role !== "OWNER") return <DeniedState reason={t("pricing.ownerOnly")} />;
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
      values[field.name] =
        field.type === "percent"
          ? Number(value) / 100
          : field.type === "number"
            ? Number(value)
            : value;
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
                    (item.context_code !== undefined && item.context_code !== null
                      ? contextLabel(item.context_code)
                      : (item.source ?? item.entity ?? t("pricing.rules"))),
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
                    <dd>{renderFieldValue(field, item[field.name])}</dd>
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
        {fields[resource] && resource !== "audits" && (
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
                          : `${contextLabel(row.context_code)} · ${optionLabel(String(row.typology))} · ${optionLabel(String(row.pricing_mode))}`}
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
                    type={field.type === "percent" ? "number" : (field.type ?? "text")}
                    step={field.type === "percent" ? "0.1" : undefined}
                    min={field.type === "percent" ? "0" : undefined}
                    max={field.type === "percent" ? "100" : undefined}
                    required={!field.optional}
                    defaultValue={
                      field.type === "percent"
                        ? editing?.[field.name] !== undefined &&
                          editing?.[field.name] !== null &&
                          editing?.[field.name] !== ""
                          ? pctDisplay(editing[field.name])
                          : (field.initial ?? "0")
                        : String(editing?.[field.name] ?? field.initial ?? "")
                    }
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

type Operation = PriceResponse;

/** Whole-percent-free margin: (net − cost) / net, both Decimal strings —
 * computed in cents so the display never carries a float artifact. */
function moneyCents(value: string): bigint | null {
  const match = value.trim().match(/^(-?)(\d*)(?:\.(\d*))?$/);
  if (match === null || (match[2] === "" && (match[3] ?? "") === "")) return null;
  const units = match[2] === "" ? "0" : match[2];
  const fraction = `${match[3] ?? ""}00`.slice(0, 2);
  return BigInt(`${match[1]}${units}${fraction}`);
}
function marginText(net: string, cost: string, currency: string): string {
  const netCents = moneyCents(net);
  const costCents = moneyCents(cost);
  if (netCents === null || costCents === null || netCents <= 0n) return "—";
  const diffCents = netCents - costCents;
  const margin = Number((diffCents * 10_000n) / netCents) / 100;
  const whole = diffCents / 100n;
  const cents = diffCents % 100n;
  const signed = diffCents < 0n ? "-" : "";
  const text = `${signed}${whole < 0n ? -whole : whole}.${`${cents < 0n ? -cents : cents}`.padStart(2, "0")}`;
  return `${formatMoney(text, currency)} · ${margin.toFixed(1)} %`;
}

/** §03-D — the pricing decision surface: the estimator and the approver
 * read the SAME frozen numbers — per-position cost vs selling, project
 * margin, the recorded reason and who applied/rejected it. */
function OperationDecision({
  operation,
  owner,
  busy,
  reasonReady,
  boundProject,
  projectLabel,
  currentUserId,
  onApply,
  onReject,
}: {
  operation: Operation;
  owner: boolean;
  busy: boolean;
  reasonReady: boolean;
  boundProject?: ProjectResponse;
  projectLabel?: string;
  currentUserId?: string;
  onApply: () => void;
  onReject: () => void;
}): JSX.Element {
  const costs = new Map(
    (operation.cost_lines ?? []).map((line) => [line.position_index, line.line_cost]),
  );
  // Position metadata joins only when the operation targets the live
  // revision of the project it actually belongs to — a stale operation's
  // indexes can point at moved/deleted positions, and a project fetched
  // for another operation must never loan its labels, so both stay empty
  // rather than mislead.
  const isBoundProject = boundProject?.id === operation.project_id;
  const positions = new Map(
    (isBoundProject && operation.revision_code === boundProject?.current_revision
      ? (boundProject.positions ?? [])
      : []
    ).map((position) => [position.position_index, position]),
  );
  // A delta is only meaningful when both sides share a currency — a
  // historical operation in another currency shows its own totals instead.
  const diff =
    isBoundProject &&
    boundProject?.pricing_current &&
    boundProject.total_price_gross &&
    boundProject.currency === operation.currency
      ? Number(operation.project_gross) - Number(boundProject.total_price_gross)
      : null;
  return (
    <article className="operation-decision">
      <header className="operation-decision__head">
        <span className="status-chip" data-status={operation.state.toLowerCase()}>
          {t(
            operation.state === "PENDING"
              ? "pricing.pending"
              : operation.state === "APPLIED"
                ? "pricing.applied"
                : operation.state === "REJECTED"
                  ? "pricing.rejected"
                  : "pricing.notApplied",
          )}
        </span>
        {projectLabel && (
          <span className="operation-decision__meta">
            {t("pricing.projectId")}: {projectLabel}
          </span>
        )}
        <span className="operation-decision__meta">
          {operation.revision_code} · {t("pricing.discount")} {pctDisplay(operation.discount_pct)} %
          · <time dateTime={operation.created_at}>{formatDateTime(operation.created_at)}</time>
        </span>
      </header>

      <div className="operation-totals">
        <div className="operation-total">
          <dt>{t("pricing.totalCost")}</dt>
          <dd>{formatMoney(operation.total_cost, operation.currency)}</dd>
        </div>
        <div className="operation-total">
          <dt>{t("pricing.marginRealized")}</dt>
          <dd>{marginText(operation.project_net, operation.total_cost, operation.currency)}</dd>
        </div>
        <div className="operation-total">
          <dt>{t("pricing.net")}</dt>
          <dd>{formatMoney(operation.project_net, operation.currency)}</dd>
        </div>
        <div className="operation-total">
          <dt>{t("pricing.taxTotal")}</dt>
          <dd>{formatMoney(operation.project_tax, operation.currency)}</dd>
        </div>
        <div className="operation-total operation-total--gross">
          <dt>{t("pricing.gross")}</dt>
          <dd>{formatMoney(operation.project_gross, operation.currency)}</dd>
        </div>
        {diff !== null && diff !== 0 && (
          <div className="operation-total">
            <dt>{t("pricing.vsCurrent")}</dt>
            <dd data-negative={diff < 0 || undefined}>
              {diff > 0 ? "+" : ""}
              {formatMoney(String(diff), operation.currency)}
            </dd>
          </div>
        )}
      </div>

      <table className="operation-lines">
        <caption>{t("pricing.perPosition")}</caption>
        <thead>
          <tr>
            <th scope="col">#</th>
            <th scope="col">{t("projects.location")}</th>
            <th scope="col">{t("pricing.quantity")}</th>
            <th scope="col">{t("pricing.cost")}</th>
            <th scope="col">{t("pricing.net")}</th>
            <th scope="col">{t("pricing.marginRealized")}</th>
          </tr>
        </thead>
        <tbody>
          {(operation.lines ?? []).map((line) => {
            const position = positions.get(line.position_index);
            return (
              <tr key={line.position_index}>
                <td>{line.position_index}</td>
                <td>{position?.location_tag || "—"}</td>
                <td>{position?.quantity ?? "—"}</td>
                <td>{formatMoney(costs.get(line.position_index) ?? "0", operation.currency)}</td>
                <td>{formatMoney(line.line_net, operation.currency)}</td>
                <td>
                  {marginText(
                    line.line_net,
                    costs.get(line.position_index) ?? "0",
                    operation.currency,
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <p className="operation-decision__audit">
        {t("pricing.auditReason")}: {operation.reason || "—"} · {t("pricing.auditBy")}{" "}
        {operation.requested_by
          ? operation.requested_by === currentUserId
            ? t("pricing.auditYou")
            : operation.requested_by.slice(0, 8)
          : "—"}
        {operation.approved_at &&
          ` · ${t("pricing.auditDecided")} ${formatDateTime(operation.approved_at)}`}
      </p>

      <div className="operation-decision__actions">
        {["PREVIEW", "PENDING"].includes(operation.state) &&
          (owner || operation.state !== "PENDING") && (
            <button
              className="ui-button"
              disabled={busy || !reasonReady}
              onClick={onApply}
              type="button"
            >
              {t("pricing.apply")}
            </button>
          )}
        {owner && operation.state === "PENDING" && (
          <button
            className="ui-button ui-button--danger"
            disabled={busy || !reasonReady}
            onClick={onReject}
            type="button"
          >
            {t("pricing.reject")}
          </button>
        )}
      </div>
    </article>
  );
}
function CommercialOperations({
  request,
  owner,
  boundProjectId,
}: {
  request: RequestFn;
  owner: boolean;
  boundProjectId?: string;
}): JSX.Element {
  const [operation, setOperation] = useState<Operation | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [reason, setReason] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [projectId, setProjectId] = useState(boundProjectId ?? "");
  const [selectedMode, setSelectedMode] = useState("COST_PLUS_MARGIN");
  const [history, setHistory] = useState<Operation[]>([]);
  const [boundProject, setBoundProject] = useState<ProjectResponse | undefined>();
  // Bumped after a successful apply — the project's live totals changed, so
  // the vsCurrent comparison must rebind rather than diff against the
  // pre-apply snapshot.
  const [boundReload, setBoundReload] = useState(0);
  const generation = useRef(0);

  const me = useAuthSession().me;
  const orgId = me?.active_organization?.id;
  const currentUserId = me?.user?.id;

  const [projectOptions, setProjectOptions] = useState<ProjectResponse[]>([]);

  const [projectsError, setProjectsError] = useState(false);

  const [projectReload, setProjectReload] = useState(0);

  useEffect(() => {
    let active = true;

    setProjectOptions([]);

    setProjectsError(false);

    if (orgId)
      void projectsList({ headers: { "X-Organization-ID": orgId } })
        .then((response) => {
          if (response.status !== 200) throw new Error("projects unavailable");

          if (active) setProjectOptions(response.data.items);
        })
        .catch(() => {
          if (active) setProjectsError(true);
        });

    return () => {
      active = false;
    };
  }, [orgId, projectReload]);

  const projectLabel = (project: ProjectResponse) =>
    [project.code, project.client_name, project.name].filter(Boolean).join(" · ");

  // The decision surface needs position labels and the currently applied
  // totals — fetch the operation's project once it exists. A new operation
  // must never see the previous project's labels: clear first, rebind only
  // when this operation's project answers, and never join across ids.
  useEffect(() => {
    let active = true;
    setBoundProject(undefined);
    if (!orgId || !operation?.project_id) {
      return;
    }
    void projectsRetrieve(operation.project_id, {
      headers: { "X-Organization-ID": orgId },
    })
      .then((response) => {
        if (active) setBoundProject(response.status === 200 ? response.data : undefined);
      })
      .catch(() => {
        if (active) setBoundProject(undefined);
      });
    return () => {
      active = false;
    };
  }, [orgId, operation?.project_id, boundReload]);

  // The audit requires a reason on every preview; seed the first quote's
  // reason so the estimator isn't blocked before any price exists — still
  // editable, still recorded verbatim in the audit trail.
  useEffect(() => {
    if (projectId && !reason && history.length === 0) {
      setReason(t("pricing.firstQuoteReason"));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, history.length]);

  // The applied operation is the page's primary state — load history on
  // mount instead of waiting for a manual Recargar click. StrictMode's
  // simulated remount must not issue a second read: the ref survives the
  // double-invoked effects while the generation guard owns staleness. The
  // remount branch releases `busy`: the cleanup bumped the generation, so
  // the orphaned mount-load's `finally` can never reset it — and no
  // user-triggered run can exist yet on a remount.
  const historyMounted = useRef(false);
  useEffect(() => {
    if (historyMounted.current) {
      setBusy(false);
      return;
    }
    historyMounted.current = true;
    if (orgId) void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId]);

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
    setConfirmed(false);
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
    } catch (error) {
      if (generation.current === current) setError(actionErrorDetail(error, t(errorKey)));
    } finally {
      if (generation.current === current) setBusy(false);
    }
  }
  function reload(): Promise<void> {
    return runCurrent(() => request<Operation[]>("operations/"), setHistory, "pricing.loadError");
  }
  function isOperation(value: unknown): value is Operation {
    return (
      typeof value === "object" &&
      value !== null &&
      typeof (value as Operation).id === "string" &&
      typeof (value as Operation).state === "string" &&
      Array.isArray((value as Operation).lines)
    );
  }
  function publishOperation(value: Operation): void {
    if (!isOperation(value)) throw new Error("pricing.malformedOperation");
    setOperation(value);
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
      (value) => {
        publishOperation(value);
        setHistory((rows) => rows.map((row) => (row.id === value.id ? value : row)));
        setBoundReload((count) => count + 1);
      },
      "pricing.applyError",
    );
  }
  return (
    <section>
      <h2>{t("pricing.calculate")}</h2>

      {projectsError && (
        <p role="alert">
          {t("projects.loadError")}{" "}
          <button type="button" onClick={() => setProjectReload((value) => value + 1)}>
            {t("pricing.reload")}
          </button>
        </p>
      )}
      {!boundProjectId && (
        <CommercialDraft
          request={request}
          onCreated={(id) => {
            invalidate();
            setOperation(null);
            setProjectId(id);

            setProjectReload((value) => value + 1);
          }}
        />
      )}
      <form
        className="commercial-form"
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
          // The UI collects percents; the authority stores fractions.
          for (const key of ["discount_pct", "target_margin"] as const) {
            if (data[key] !== undefined && data[key] !== "")
              data[key] = String(Number(data[key]) / 100);
          }
          void runCurrent(
            () => request<Operation>("preview/", "POST", { ...data, confirmed }),
            publishOperation,
            "pricing.calculateError",
          );
        }}
      >
        {boundProjectId ? (
          <input type="hidden" name="project_id" value={boundProjectId} />
        ) : (
          <label>
            {t("pricing.projectId")}
            <select
              name="project_id"
              required
              value={projectId}
              onChange={(event) => setProjectId(event.target.value)}
            >
              <option value="">{t("projects.chooseProject")}</option>

              {projectOptions.map((project) => (
                <option key={project.id} value={project.id}>
                  {projectLabel(project)}
                </option>
              ))}
            </select>
          </label>
        )}
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
          <input
            name="effective_date"
            type="date"
            defaultValue={new Date().toISOString().slice(0, 10)}
            required
          />
        </label>
        <label>
          {t("pricing.fxId")}
          <input name="fx_snapshot_id" />
        </label>
        <label>
          {t("pricing.discount")}
          <input
            name="discount_pct"
            type="number"
            step="0.1"
            min="0"
            max="100"
            defaultValue="0"
            required
          />
        </label>
        {selectedMode === "TARGET_GROSS_MARGIN_PROJECT" && (
          <label>
            {t("pricing.margin")}
            <input
              name="target_margin"
              type="number"
              step="0.1"
              min="0"
              max="100"
              defaultValue="35"
              required
            />
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
            placeholder={t("pricing.reasonPlaceholder")}
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
        <OperationDecision
          boundProject={boundProject}
          currentUserId={currentUserId}
          busy={busy}
          onApply={() => void apply()}
          onReject={() => void apply(true)}
          operation={operation}
          owner={owner}
          projectLabel={
            boundProjectId
              ? undefined
              : projectOptions.find((p) => p.id === operation.project_id)
                ? projectLabel(projectOptions.find((p) => p.id === operation.project_id)!)
                : t("projects.loadError")
          }
          reasonReady={reason.trim().length > 0}
        />
      )}
      <h2>{t("pricing.history")}</h2>
      <button type="button" disabled={busy} onClick={() => void reload()}>
        {t("pricing.reload")}
      </button>
      {Array.isArray(history) &&
        history
          .filter((item) => !boundProjectId || item.project_id === boundProjectId)
          .map((item) => (
            <article className="operation-history__item" key={item.id}>
              <p>
                <strong>{formatMoney(item.project_gross, item.currency)}</strong>{" "}
                <span className="status-chip" data-status={item.state.toLowerCase()}>
                  {t(
                    item.state === "PENDING"
                      ? "pricing.pending"
                      : item.state === "APPLIED"
                        ? "pricing.applied"
                        : item.state === "REJECTED"
                          ? "pricing.rejected"
                          : "pricing.notApplied",
                  )}
                </span>
              </p>
              <p className="operation-history__meta">
                {item.revision_code} · {item.reason} · {formatDateTime(item.created_at)}
              </p>
              <button
                type="button"
                disabled={busy}
                onClick={() => {
                  invalidate();
                  setOperation(item);
                  setReason(item.reason);
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
