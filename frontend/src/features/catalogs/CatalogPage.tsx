import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { ApiError } from "../../api/apiMutator";
import { UnsavedChangesGuard } from "../../app/UnsavedChangesGuard";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { t } from "../../i18n/es-CL";
import { CatalogImportsPanel } from "./CatalogImportsPanel";
import { SectionPreviewSvg } from "../canvas/SectionPreviewSvg";
import {
  catalogApi,
  initialDraft,
  initialSectionDraft,
  schemas,
  sectionPreviewFromDraft,
  writeFromDraft,
  type CatalogData,
  type Field,
  type HardwareComponent,
  type Resource,
  type Row,
  type SectionDraft,
} from "./catalogModel";
import "./catalogs.css";

type Label = Parameters<typeof t>[0];
// All suffixes below are supplied in the translation block.
const ct = (key: string) => t(`catalog.${key}` as Label);
const resources: Resource[] = ["systems", "articles", "glazing", "hardware-kits"];

function failure(error: unknown): string {
  if (!(error instanceof ApiError)) return ct("errorNetwork");
  if (error.status === 401 || error.status === 403) return ct("errorPermission");
  if (error.status === 404) return ct("errorMissing");
  if (error.status === 409) return ct("errorConflict");
  if (error.status === 400) return ct("errorValidation");
  return ct("errorNetwork");
}

function itemName(resource: Resource, row: Row<Resource>, data: CatalogData): string {
  if (resource === "glazing" && "bead_article_id" in row) {
    const article = data.articles.find((item) => item.id === row.bead_article_id);
    return `${article?.name ?? ct("beadUnavailable")} · ${row.glass_thickness_mm} ${ct("mm")}`;
  }
  return "name" in row ? row.name : ct("record");
}

function itemCode(row: Row<Resource>): string {
  return "sku" in row ? row.sku : "code" in row ? row.code : "";
}

function systemReadinessLabel(system: Row<"systems">): string {
  if (!system.readiness) return ct("readinessUnknown");

  return system.readiness.quote_ready
    ? ct("readyFixed")
    : system.readiness.reasons.map((reason) => ct(`readiness.${reason}`)).join(" · ");
}

export function CatalogPage(): JSX.Element {
  const { status, me, session } = useAuthSession();
  const organization = me?.active_organization;
  if (status !== "ready") return <p role="status">{ct("loading")}</p>;
  if (!organization || !["OWNER", "WORKSHOP_MANAGER", "ESTIMATOR"].includes(organization.role))
    return <p role="alert">{ct("permission")}</p>;

  return (
    <CatalogWorkspace
      key={`${session?.user.id}:${organization.id}:${organization.role}`}
      orgId={organization.id}
      role={organization.role}
    />
  );
}

function CatalogWorkspace({ orgId, role }: { orgId: string; role: string }): JSX.Element {
  const api = useMemo(() => catalogApi(orgId), [orgId]);
  const [data, setData] = useState<CatalogData | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [resource, setResource] = useState<Resource>("systems");
  const [editor, setEditor] = useState<{ resource: Resource; id?: string } | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [reload, setReload] = useState(0);
  const lifetime = useRef<AbortController | null>(null);
  // Catalog CRUD accepts OWNER/WORKSHOP_MANAGER — an estimator reads the
  // catalog and writes only through the import-review flow.
  const canEdit = role === "OWNER" || role === "WORKSHOP_MANAGER";

  useEffect(() => {
    const controller = new AbortController();
    lifetime.current = controller;
    setLoading(true);
    setError("");
    void Promise.all([
      api.list("systems", controller.signal),
      api.list("articles", controller.signal),
      api.list("glazing", controller.signal),
      api.list("hardware-kits", controller.signal),
    ])
      .then(([systems, articles, glazing, kits]) => {
        if (controller.signal.aborted) return;
        setData({ systems, articles, glazing, "hardware-kits": kits });
        setSelected((previous) =>
          previous && systems.some((system) => system.id === previous)
            ? previous
            : (systems[0]?.id ?? null),
        );
        if (!systems.length) setResource("hardware-kits");
      })
      .catch((caught) => {
        if (!controller.signal.aborted) setError(failure(caught));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [api, reload]);

  function accept<R extends Resource>(kind: R, saved: Row<R>) {
    if (lifetime.current?.signal.aborted) return;
    setData((current) => {
      if (!current) return current;
      return {
        ...current,
        [kind]: [...current[kind].filter((row) => row.id !== saved.id), saved],
      };
    });
    if (kind === "systems") {
      setSelected(saved.id);
      setResource("systems");
    }
    setEditor(null);
    setNotice(ct("saved"));
  }

  const [reviewing, setReviewing] = useState<string | null>(null);
  async function reviewRow<R extends Resource>(kind: R, id: string) {
    setReviewing(id);
    setNotice("");
    try {
      accept(kind, await api.review(kind, id));
      setNotice(ct("reviewed"));
    } catch (caught) {
      setNotice(failure(caught));
    } finally {
      if (!lifetime.current?.signal.aborted) setReviewing(null);
    }
  }

  function removed(kind: Resource, id: string) {
    if (lifetime.current?.signal.aborted) return;
    setEditor(null);
    setNotice(ct("deleted"));
    // Reload relationships after deletion: the server decides referential behavior.
    if (kind === "systems" && id === selected) setSelected(null);
    setReload((value) => value + 1);
  }

  if (loading) return <p role="status">{ct("loading")}</p>;
  if (error || !data) {
    return (
      <section className="catalog">
        <p role="alert">{error || ct("errorNetwork")}</p>
        <button type="button" onClick={() => setReload((value) => value + 1)}>
          {ct("retry")}
        </button>
      </section>
    );
  }

  const currentSystem = data.systems.find((system) => system.id === selected);
  const term = search.trim().toLocaleLowerCase("es-CL");
  const visibleSystems = data.systems.filter((system) =>
    `${system.name} ${system.code}`.toLocaleLowerCase("es-CL").includes(term),
  );
  const rows: Row<Resource>[] =
    resource === "systems"
      ? currentSystem
        ? [currentSystem]
        : []
      : data[resource].filter((row) => row.system_id === selected);
  const editingRow = editor?.id
    ? data[editor.resource].find((row) => row.id === editor.id)
    : undefined;

  return (
    <section className="catalog">
      <header className="catalog-heading">
        <div>
          <h1>{ct("title")}</h1>
          <p>{ct("subtitle")}</p>
        </div>
        {canEdit && (
          <button
            type="button"
            disabled={editor !== null}
            onClick={() => {
              setNotice("");
              setEditor({ resource: "systems" });
            }}
          >
            {ct("newSystem")}
          </button>
        )}
      </header>

      <p className="catalog-status" role="status" aria-live="polite">
        {notice}
      </p>

      <CatalogImportsPanel
        orgId={orgId}
        canWrite={role === "OWNER" || role === "ESTIMATOR"}
        systems={data.systems
          .filter((system) => !system.is_global)
          .map((system) => ({ id: system.id, name: system.name, code: system.code }))}
        onConfirmed={() => setReload((value) => value + 1)}
      />

      <div className="catalog-layout">
        <aside className="catalog-master" aria-label={ct("systems")}>
          <label>
            {ct("search")}
            <input
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>
          <ul>
            {visibleSystems.map((system) => (
              <li key={system.id}>
                <button
                  type="button"
                  className="catalog-system"
                  aria-current={selected === system.id ? "true" : undefined}
                  disabled={editor !== null}
                  onClick={() => {
                    setSelected(system.id);
                    setNotice("");
                  }}
                >
                  <strong>{system.name}</strong>
                  <span>
                    {system.code} · {ct(`option.${system.material}`)}
                  </span>
                  <small>
                    {system.is_global ? ct("global") : ct("own")}
                    {system.is_demo ? ` · ${ct("demo")}` : ""}
                    {" · "}

                    <span>{systemReadinessLabel(system)}</span>
                  </small>
                </button>
              </li>
            ))}
          </ul>
          {!visibleSystems.length && <p>{ct("noSystems")}</p>}
          <button
            type="button"
            aria-current={selected === null ? "true" : undefined}
            disabled={editor !== null}
            onClick={() => {
              setSelected(null);
              setResource("hardware-kits");
              setNotice("");
            }}
          >
            {ct("unassignedKits")}
          </button>
        </aside>

        <section className="catalog-detail" aria-label={ct("detail")}>
          <header>
            <h2>{currentSystem?.name ?? ct("unassignedKits")}</h2>
            {currentSystem && (
              <p>
                <strong>Estado del sistema:</strong> {systemReadinessLabel(currentSystem)}
                {" · "}
                {currentSystem.is_active ? ct("active") : ct("inactive")}
              </p>
            )}
            {currentSystem?.is_global && <p>{ct("globalHelp")}</p>}
            {currentSystem?.is_demo && <p>{ct("demoHelp")}</p>}
          </header>

          <nav className="catalog-tabs" aria-label={ct("sections")}>
            {resources.map((kind) => (
              <button
                key={kind}
                type="button"
                aria-pressed={resource === kind}
                disabled={editor !== null || (selected === null && kind !== "hardware-kits")}
                onClick={() => {
                  setResource(kind);
                  setNotice("");
                }}
              >
                {ct(kind)}
              </button>
            ))}
          </nav>

          <div className="catalog-toolbar">
            <h3>{ct(resource)}</h3>
            {resource !== "systems" && canEdit && (
              <button
                type="button"
                disabled={editor !== null || (selected === null && resource !== "hardware-kits")}
                onClick={() => {
                  setNotice("");
                  setEditor({ resource });
                }}
              >
                {ct("create")}
              </button>
            )}
          </div>

          {!rows.length ? (
            <p className="catalog-empty">{ct("empty")}</p>
          ) : (
            <div className="catalog-table-scroll">
              <table>
                <caption className="catalog-sr-only">{ct(resource)}</caption>
                <thead>
                  <tr>
                    <th scope="col">{ct("field.name")}</th>
                    <th scope="col">{ct("field.code")}</th>
                    <th scope="col">{ct("state")}</th>
                    <th scope="col">{ct("actions")}</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.id}>
                      <th scope="row">{itemName(resource, row, data)}</th>
                      <td>{itemCode(row)}</td>
                      <td>
                        {row.read_only !== false ? ct("readOnly") : ct("own")}
                        {"is_active" in row && (
                          <span> · {ct(row.is_active ? "active" : "inactive")}</span>
                        )}
                        {"data_provenance" in row &&
                          row.data_provenance === "LEGACY_UNVERIFIED" && (
                            <span className="catalog-provenance-legacy">
                              {" · "}
                              {ct("provenanceLegacy")}
                            </span>
                          )}
                      </td>
                      <td>
                        <button
                          type="button"
                          aria-label={`${ct(row.read_only === false && canEdit ? "edit" : "view")} ${itemName(resource, row, data)}`}
                          disabled={editor !== null}
                          onClick={() => {
                            setNotice("");
                            setEditor({ resource, id: row.id });
                          }}
                        >
                          {ct(row.read_only === false && canEdit ? "edit" : "view")}
                          <span className="catalog-sr-only"> {itemName(resource, row, data)}</span>
                        </button>
                        {canEdit &&
                          "data_provenance" in row &&
                          row.data_provenance === "LEGACY_UNVERIFIED" &&
                          row.read_only === false && (
                            <button
                              type="button"
                              aria-label={`${ct("markReviewed")} ${itemName(resource, row, data)}`}
                              disabled={editor !== null || reviewing !== null}
                              onClick={() => void reviewRow(resource, row.id)}
                            >
                              {reviewing === row.id ? ct("reviewing") : ct("markReviewed")}
                              <span className="catalog-sr-only">
                                {" "}
                                {itemName(resource, row, data)}
                              </span>
                            </button>
                          )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {editor && (
            <CatalogEditor
              key={`${editor.resource}:${editor.id ?? "new"}`}
              resource={editor.resource}
              row={editingRow}
              data={data}
              systemId={selected}
              api={api}
              locked={!canEdit}
              onSaved={(saved) => accept(editor.resource, saved)}
              onDeleted={(id) => removed(editor.resource, id)}
              onClose={() => setEditor(null)}
            />
          )}
        </section>
      </div>
    </section>
  );
}

type EditorProps = {
  resource: Resource;
  row?: Row<Resource>;
  data: CatalogData;
  systemId: string | null;
  api: ReturnType<typeof catalogApi>;
  locked: boolean;
  onSaved: (row: Row<Resource>) => void;
  onDeleted: (id: string) => void;
  onClose: () => void;
};

function CatalogEditor({
  resource,
  row,
  data,
  systemId,
  api,
  locked,
  onSaved,
  onDeleted,
  onClose,
}: EditorProps): JSX.Element {
  const [draft, setDraft] = useState(() => initialDraft(resource, row, systemId));
  const [contents, setContents] = useState<Array<HardwareComponent & { key: string }>>(() =>
    row && "contents" in row
      ? row.contents.map((component) => ({ ...component, key: crypto.randomUUID() }))
      : [],
  );
  const [sectionDraft, setSectionDraft] = useState<SectionDraft>(() =>
    initialSectionDraft(row && "section" in row ? row.section : null),
  );
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [uncertainCreate, setUncertainCreate] = useState(false);
  const [error, setError] = useState("");
  const errorRef = useRef<HTMLParagraphElement>(null);
  const firstControl = useRef<HTMLHeadingElement>(null);
  const alive = useRef(true);
  const inFlight = useRef(false);
  const readOnly = locked || (row !== undefined && row.read_only !== false);
  const beadOptions = data.articles.filter(
    (article) => article.system_id === draft.system_id && article.role === "GLAZING_BEAD",
  );
  const noBeads = resource === "glazing" && beadOptions.length === 0;

  useEffect(() => {
    alive.current = true;
    firstControl.current?.focus();
    return () => {
      alive.current = false;
    };
  }, []);

  useEffect(() => {
    if (error) errorRef.current?.focus();
  }, [error]);

  function change(name: string, value: string) {
    setDirty(true);
    setError("");
    setDraft((current) => ({
      ...current,
      [name]: value,
      ...(name === "system_id" ? { bead_article_id: "" } : {}),
    }));
  }

  function changeSection(next: (current: SectionDraft) => SectionDraft) {
    setDirty(true);
    setError("");
    setSectionDraft(next);
  }

  function close() {
    if (!dirty || window.confirm(ct("discard"))) onClose();
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (readOnly || inFlight.current || noBeads || uncertainCreate) return;
    let body;
    try {
      body = writeFromDraft(resource, draft, contents, sectionDraft);
    } catch {
      setError(ct("errorValidation"));
      return;
    }
    inFlight.current = true;
    setBusy(true);
    setError("");
    try {
      const saved = await api.save(resource, body, row?.id, row?.revision);
      if (alive.current) {
        setDirty(false);
        onSaved(saved);
      }
    } catch (caught) {
      if (alive.current) {
        const uncertain = !row && (!(caught instanceof ApiError) || caught.status >= 500);
        setUncertainCreate(uncertain);
        setError(uncertain ? ct("uncertainCreate") : failure(caught));
      }
    } finally {
      inFlight.current = false;
      if (alive.current) setBusy(false);
    }
  }

  async function remove() {
    if (!row || readOnly || inFlight.current || !window.confirm(ct("confirmDelete"))) return;
    inFlight.current = true;
    setBusy(true);
    setError("");
    try {
      await api.remove(resource, row.id, row.revision);
      if (alive.current) {
        setDirty(false);
        onDeleted(row.id);
      }
    } catch (caught) {
      if (alive.current) setError(failure(caught));
    } finally {
      inFlight.current = false;
      if (alive.current) setBusy(false);
    }
  }

  function control(field: Field) {
    const value = draft[field.name] ?? "";
    const id = `catalog-${resource}-${field.name}`;
    const options: Array<{ value: string; label: string }> =
      field.kind === "system"
        ? data.systems.map((system) => ({
            value: system.id,
            label: `${system.name} · ${system.code}${system.is_global ? ` · ${ct("global")}` : ""}`,
          }))
        : field.kind === "bead"
          ? beadOptions.map((article) => ({
              value: article.id,
              label: `${article.name} · ${article.sku}`,
            }))
          : field.kind === "boolean"
            ? [
                { value: "true", label: ct("active") },
                { value: "false", label: ct("inactive") },
              ]
            : (field.options ?? []).map((option) => ({
                value: option,
                label: ct(`option.${option}`),
              }));
    const select = ["system", "bead", "boolean", "select"].includes(field.kind);
    const unknownOption =
      select && value !== "" && !options.some((option) => option.value === value);
    return (
      <label key={field.name} htmlFor={id}>
        <span>
          {ct(`field.${field.name}`)}
          {field.optional && <small> · {ct("optional")}</small>}
        </span>
        {select ? (
          <select
            id={id}
            name={field.name}
            value={value}
            required={!field.optional}
            disabled={field.kind === "system" && row !== undefined}
            onChange={(event) => change(field.name, event.target.value)}
          >
            <option value="">
              {field.kind === "system" && field.optional ? ct("noSystem") : ct("choose")}
            </option>
            {unknownOption && (
              <option value={value} disabled>
                {ct("unavailableValue")}
              </option>
            )}
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        ) : (
          <input
            id={id}
            name={field.name}
            type="text"
            value={value}
            required={!field.optional}
            maxLength={field.maxLength}
            inputMode={
              field.kind === "decimal"
                ? "decimal"
                : field.kind === "integer"
                  ? "numeric"
                  : undefined
            }
            pattern={
              field.kind === "decimal"
                ? `-?[0-9]+([.,][0-9]{1,${field.places ?? 2}})?`
                : field.kind === "integer"
                  ? "-?[0-9]+"
                  : ".*\\S.*"
            }
            onChange={(event) => change(field.name, event.target.value)}
          />
        )}
      </label>
    );
  }

  return (
    <form className="catalog-editor" onSubmit={submit} aria-busy={busy}>
      <UnsavedChangesGuard dirty={dirty} message={ct("discard")} />
      <header className="catalog-toolbar">
        <h3 ref={firstControl} tabIndex={-1}>
          {ct(readOnly ? "view" : row ? "edit" : "create")} · {ct(resource)}
        </h3>
        <button type="button" disabled={busy} onClick={close}>
          {ct("close")}
        </button>
      </header>
      <p>{ct(readOnly ? "readOnlyHelp" : "humanValues")}</p>
      {row && resource !== "systems" && <p>{ct("parentFixed")}</p>}
      {noBeads && <p role="status">{ct("noBeads")}</p>}
      {uncertainCreate && !error && <p role="status">{ct("uncertainCreate")}</p>}
      {error && (
        <p ref={errorRef} tabIndex={-1} role="alert">
          {error}
        </p>
      )}

      <fieldset className="catalog-controls" disabled={busy || readOnly}>
        <legend className="catalog-sr-only">{ct("fields")}</legend>
        {schemas[resource].map((group) => (
          <fieldset className="catalog-group" key={group.title}>
            <legend>{ct(`group.${group.title}`)}</legend>
            <div className="catalog-fields">{group.fields.map(control)}</div>
          </fieldset>
        ))}

        {resource === "articles" && (
          <fieldset className="catalog-group">
            <legend>{ct("field.section")}</legend>
            <label>
              <input
                type="checkbox"
                checked={sectionDraft.enabled}
                onChange={(event) =>
                  changeSection((current) => ({ ...current, enabled: event.target.checked }))
                }
              />
              <span>{ct("section.declare")}</span>
            </label>
            {sectionDraft.enabled && (
              <>
                <div className="catalog-fields">
                  <label htmlFor={`catalog-${resource}-section-source`}>
                    <span>{ct("field.source")}</span>
                    <select
                      id={`catalog-${resource}-section-source`}
                      value={sectionDraft.source}
                      onChange={(event) =>
                        changeSection((current) => ({
                          ...current,
                          source: event.target.value as SectionDraft["source"],
                        }))
                      }
                    >
                      <option value="POLYGON">{ct("sectionSource.POLYGON")}</option>
                      <option value="DXF_REFERENCE">{ct("sectionSource.DXF_REFERENCE")}</option>
                    </select>
                  </label>
                  <label htmlFor={`catalog-${resource}-section-depth`}>
                    <span>{ct("field.depth_mm")}</span>
                    <input
                      id={`catalog-${resource}-section-depth`}
                      type="text"
                      required
                      inputMode="decimal"
                      pattern="-?[0-9]+([.,][0-9]{1,2})?"
                      value={sectionDraft.depth_mm}
                      onChange={(event) =>
                        changeSection((current) => ({
                          ...current,
                          depth_mm: event.target.value,
                        }))
                      }
                    />
                  </label>
                  <label htmlFor={`catalog-${resource}-section-ref`}>
                    <span>
                      {ct("field.drawing_ref")}
                      {sectionDraft.source !== "DXF_REFERENCE" && (
                        <small> · {ct("optional")}</small>
                      )}
                    </span>
                    <input
                      id={`catalog-${resource}-section-ref`}
                      type="text"
                      required={sectionDraft.source === "DXF_REFERENCE"}
                      maxLength={500}
                      value={sectionDraft.drawing_ref}
                      onChange={(event) =>
                        changeSection((current) => ({
                          ...current,
                          drawing_ref: event.target.value,
                        }))
                      }
                    />
                  </label>
                </div>
                <div className="catalog-table-scroll">
                  <table className="catalog-contents">
                    <caption className="catalog-sr-only">{ct("section.vertices")}</caption>
                    <thead>
                      <tr>
                        <th scope="col">{ct("field.x_mm")}</th>
                        <th scope="col">{ct("field.y_mm")}</th>
                        <th scope="col">{ct("actions")}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sectionDraft.vertices.map((vertex, index) => (
                        <tr key={vertex.key}>
                          {(["x_mm", "y_mm"] as const).map((key) => (
                            <td key={key}>
                              <input
                                aria-label={`${ct(`field.${key}`)} · ${ct("section.vertex")} ${index + 1}`}
                                type="text"
                                required
                                inputMode="decimal"
                                pattern="-?[0-9]+([.,][0-9]{1,2})?"
                                value={vertex[key]}
                                onChange={(event) => {
                                  const value = event.target.value;
                                  changeSection((current) => ({
                                    ...current,
                                    vertices: current.vertices.map((item) =>
                                      item.key === vertex.key ? { ...item, [key]: value } : item,
                                    ),
                                  }));
                                }}
                              />
                            </td>
                          ))}
                          <td>
                            <button
                              type="button"
                              aria-label={`${ct("remove")} ${ct("section.vertex")} ${index + 1}`}
                              disabled={sectionDraft.vertices.length <= 3}
                              onClick={() =>
                                changeSection((current) => ({
                                  ...current,
                                  vertices: current.vertices.filter(
                                    (item) => item.key !== vertex.key,
                                  ),
                                }))
                              }
                            >
                              {ct("remove")}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <button
                  type="button"
                  onClick={() =>
                    changeSection((current) => ({
                      ...current,
                      vertices: [
                        ...current.vertices,
                        { key: crypto.randomUUID(), x_mm: "", y_mm: "" },
                      ],
                    }))
                  }
                >
                  {ct("section.addVertex")}
                </button>
                <div className="catalog-table-scroll">
                  <table className="catalog-contents">
                    <caption className="catalog-sr-only">{ct("section.axes")}</caption>
                    <thead>
                      <tr>
                        <th scope="col">{ct("field.name")}</th>
                        <th scope="col">{ct("field.y_mm")}</th>
                        <th scope="col">{ct("actions")}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sectionDraft.axes.map((axis, index) => (
                        <tr key={axis.key}>
                          <td>
                            <input
                              aria-label={`${ct("field.name")} · ${ct("section.axis")} ${index + 1}`}
                              type="text"
                              maxLength={50}
                              value={axis.name}
                              onChange={(event) =>
                                changeSection((current) => ({
                                  ...current,
                                  axes: current.axes.map((item) =>
                                    item.key === axis.key
                                      ? { ...item, name: event.target.value }
                                      : item,
                                  ),
                                }))
                              }
                            />
                          </td>
                          <td>
                            <input
                              aria-label={`${ct("field.y_mm")} · ${ct("section.axis")} ${index + 1}`}
                              type="text"
                              inputMode="decimal"
                              pattern="-?[0-9]+([.,][0-9]{1,2})?"
                              value={axis.y_mm}
                              onChange={(event) =>
                                changeSection((current) => ({
                                  ...current,
                                  axes: current.axes.map((item) =>
                                    item.key === axis.key
                                      ? { ...item, y_mm: event.target.value }
                                      : item,
                                  ),
                                }))
                              }
                            />
                          </td>
                          <td>
                            <button
                              type="button"
                              aria-label={`${ct("remove")} ${ct("section.axis")} ${index + 1}`}
                              onClick={() =>
                                changeSection((current) => ({
                                  ...current,
                                  axes: current.axes.filter((item) => item.key !== axis.key),
                                }))
                              }
                            >
                              {ct("remove")}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <button
                  type="button"
                  onClick={() =>
                    changeSection((current) => ({
                      ...current,
                      axes: [...current.axes, { key: crypto.randomUUID(), name: "", y_mm: "" }],
                    }))
                  }
                >
                  {ct("section.addAxis")}
                </button>
              </>
            )}
            <SectionPreviewSvg
              section={sectionPreviewFromDraft(sectionDraft)}
              faceWidthMm={Number(draft.face_width_mm ?? 0)}
              material={draft.material || "PVC"}
            />
          </fieldset>
        )}

        {resource === "hardware-kits" && (
          <fieldset className="catalog-group">
            <legend>{ct("contents")}</legend>
            <div className="catalog-table-scroll">
              <table className="catalog-contents">
                <caption className="catalog-sr-only">{ct("contents")}</caption>
                <thead>
                  <tr>
                    {(["sku", "name", "qty", "unit"] as const).map((key) => (
                      <th key={key} scope="col">
                        {ct(`field.${key}`)}
                      </th>
                    ))}
                    <th scope="col">{ct("actions")}</th>
                  </tr>
                </thead>
                <tbody>
                  {contents.map((component, index) => (
                    <tr key={component.key}>
                      {(["sku", "name", "qty", "unit"] as const).map((key) => (
                        <td key={key}>
                          <input
                            aria-label={`${ct(`field.${key}`)} · ${ct("component")} ${index + 1}`}
                            type="text"
                            required
                            value={component[key]}
                            inputMode={key === "qty" ? "decimal" : undefined}
                            pattern={key === "qty" ? "(?=.*[1-9])[0-9]+([.,][0-9]+)?" : ".*\\S.*"}
                            onChange={(event) => {
                              const value = event.target.value;
                              setDirty(true);
                              setError("");
                              setContents((current) =>
                                current.map((item) =>
                                  item.key === component.key ? { ...item, [key]: value } : item,
                                ),
                              );
                            }}
                          />
                        </td>
                      ))}
                      <td>
                        <button
                          type="button"
                          aria-label={`${ct("removeComponent")} ${index + 1}`}
                          onClick={() => {
                            setDirty(true);
                            setContents((current) =>
                              current.filter((item) => item.key !== component.key),
                            );
                          }}
                        >
                          {ct("remove")}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {!contents.length && <p>{ct("emptyContents")}</p>}
            <button
              type="button"
              onClick={() => {
                setDirty(true);
                setContents((current) => [
                  ...current,
                  { key: crypto.randomUUID(), sku: "", name: "", qty: "", unit: "" },
                ]);
              }}
            >
              {ct("addComponent")}
            </button>
          </fieldset>
        )}
      </fieldset>

      <footer className="catalog-toolbar">
        <button
          type="submit"
          className="catalog-primary"
          disabled={busy || readOnly || noBeads || uncertainCreate || (row !== undefined && !dirty)}
        >
          {ct(busy ? "working" : "save")}
        </button>
        {row && (
          <button
            type="button"
            className="catalog-danger"
            disabled={busy || readOnly}
            onClick={() => void remove()}
          >
            {ct("delete")}
          </button>
        )}
        <button type="button" disabled={busy} onClick={close}>
          {ct("cancel")}
        </button>
      </footer>
    </form>
  );
}
