import { useEffect, useRef, useState } from "react";
import { flushSync } from "react-dom";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ApiError } from "../../api/apiMutator";
import { UnsavedChangesGuard } from "../../app/UnsavedChangesGuard";
import {
  clientsList,
  projectsList,
  projectsCreate,
  projectsRetrieve,
  projectsUpdate,
  projectsClone,
  positionsDestroy,
} from "../../api/generated/dekopen";
import type {
  ClientResponse,
  ProjectResponse,
  ProjectWriteRequest,
  PositionResponse,
} from "../../api/generated/models";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { t, type TranslationKey } from "../../i18n/es-CL";
import "./projects.css";
import { PositionThumb } from "./PositionThumb";
import { ProjectBom } from "./ProjectPositionEditor";
import { ProjectQuotationPanel } from "./ProjectQuotationPanel";
import { ProjectImportsPanel } from "./ProjectImportsPanel";
import { ProjectPaymentsPanel } from "./ProjectPaymentsPanel";

const fields = [
  ["name", "projects.name", "text", 255],
  ["client_name", "projects.client", "text", 255],
  ["client_rut", "projects.rut", "text", 50],
  ["client_email", "projects.email", "email", undefined],
  ["client_phone", "projects.phone", "tel", 50],
  ["delivery_address", "projects.address", "textarea", undefined],
  ["notes_commercial", "projects.commercialNotes", "textarea", undefined],
  ["notes_internal", "projects.internalNotes", "textarea", undefined],
] as const;

const statuses: Record<ProjectResponse["status"], TranslationKey> = {
  DRAFT: "projects.draft",
  QUOTED: "projects.quoted",
  APPROVED: "projects.approved",
  IN_PRODUCTION: "projects.production",
  COMPLETED: "projects.completed",
  CANCELLED: "projects.cancelled",
};

function metadata(project?: ProjectResponse): ProjectWriteRequest {
  return {
    name: project?.name ?? "",
    client_id: project?.client_id ?? null,
    client_name: project?.client_name ?? "",
    client_rut: project?.client_rut ?? "",
    client_email: project?.client_email ?? "",
    client_phone: project?.client_phone ?? "",
    delivery_address: project?.delivery_address ?? "",
    notes_commercial: project?.notes_commercial ?? "",
    notes_internal: project?.notes_internal ?? "",
  };
}

type Draft = {
  value: ProjectWriteRequest;
  expectedUpdatedAt?: string;
};

function ProjectMetadataForm({
  draft,
  clients,
  disabled,
  onChange,
  onSave,
  onCancel,
}: {
  draft: Draft;
  clients: ClientResponse[];
  disabled: boolean;
  onChange(value: Draft): void;
  onSave(): void;
  onCancel(): void;
}): JSX.Element {
  return (
    <form
      className="project-metadata-form"
      onSubmit={(event) => {
        event.preventDefault();
        if (!disabled) onSave();
      }}
    >
      <fieldset disabled={disabled}>
        <legend>{t("projects.metadata")}</legend>
        {clients.length > 0 && (
          <label>
            {t("clients.pick")}
            <select
              name="client_id"
              value={draft.value.client_id ?? ""}
              onChange={(event) => {
                const picked = clients.find((item) => item.id === event.target.value) ?? null;
                const previous = clients.find((item) => item.id === draft.value.client_id) ?? null;
                // Replace an auto-filled address when the selection changes; keep
                // one the user typed (it differs from the previous pick's address).
                const autoFilled =
                  !draft.value.delivery_address ||
                  (previous !== null && draft.value.delivery_address === previous.address);
                onChange({
                  ...draft,
                  value: {
                    ...draft.value,
                    client_id: picked?.id ?? null,
                    ...(picked
                      ? {
                          client_name: picked.name,
                          client_rut: picked.rut,
                          client_email: picked.email,
                          client_phone: picked.phone,
                          delivery_address: autoFilled
                            ? picked.address
                            : draft.value.delivery_address,
                        }
                      : {}),
                  },
                });
              }}
            >
              <option value="">{t("clients.none")}</option>
              {clients
                .filter((item) => item.is_active || item.id === draft.value.client_id)
                .map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                    {item.rut ? ` · ${item.rut}` : ""}
                  </option>
                ))}
            </select>
          </label>
        )}
        {fields.map(([name, label, type, maxLength]) => {
          const props = {
            name,
            value: draft.value[name] ?? "",
            required: name === "name" || name === "client_name",
            maxLength,
            onChange: (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
              onChange({
                ...draft,
                value: { ...draft.value, [name]: event.target.value },
              }),
          };
          return (
            <label key={name}>
              {t(label)}
              {type === "textarea" ? <textarea {...props} /> : <input {...props} type={type} />}
            </label>
          );
        })}
        <button type="submit">{t("projects.save")}</button>
      </fieldset>
      <button type="button" disabled={disabled} onClick={onCancel}>
        {t("projects.cancel")}
      </button>
    </form>
  );
}

export function ProjectPages(): JSX.Element {
  const auth = useAuthSession();
  const { id } = useParams();
  const org = auth.me?.active_organization;
  const userId = auth.session?.user.id;

  if (!org || !userId || !["OWNER", "ESTIMATOR", "WORKSHOP_MANAGER"].includes(org.role)) {
    return <p role="alert">{t("projects.denied")}</p>;
  }

  const identity = `${userId}:${org.id}:${org.role}`;
  return (
    <ProjectWorkspace
      key={`${identity}:${id ?? "list"}`}
      identity={identity}
      orgId={org.id}
      id={id}
      canWrite={org.role === "OWNER" || org.role === "ESTIMATOR"}
    />
  );
}

type View = {
  items: ProjectResponse[];
  project: ProjectResponse | null;
};

function ProjectWorkspace({
  identity,
  orgId,
  id,
  canWrite,
}: {
  identity: string;
  orgId: string;
  id?: string;
  canWrite: boolean;
}): JSX.Element {
  const navigate = useNavigate();
  const [draft, setDraft] = useState<Draft | null>(null);
  const [quotationDirty, setQuotationDirty] = useState(false);
  const [paymentsDirty, setPaymentsDirty] = useState(false);
  const [importsDirty, setImportsDirty] = useState(false);
  const [search, setSearch] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [mustReload, setMustReload] = useState(false);
  const lifetime = useRef<AbortController | null>(null);
  const locked = useRef(false);

  useEffect(() => {
    const controller = new AbortController();
    lifetime.current = controller;
    return () => controller.abort();
  }, []);

  const query = useQuery<View>({
    queryKey: ["project-pages", identity, id ?? "list"],
    queryFn: async ({ signal }) => {
      const options = {
        signal,
        headers: { "X-Organization-ID": orgId },
      };
      if (id) {
        const response = await projectsRetrieve(id, options);
        if (response.status !== 200) {
          throw new ApiError(response.status, response.data);
        }
        return { project: response.data, items: [] };
      }
      const response = await projectsList(options);
      if (response.status !== 200) {
        throw new ApiError(response.status, response.data);
      }
      return { project: null, items: response.data.items };
    },
    retry: false,
    gcTime: 0,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  // The picker only materializes when the metadata form opens — fetch then,
  // so the list page never pays for it.
  const clientsQuery = useQuery<ClientResponse[]>({
    queryKey: ["clients", identity],
    enabled: draft !== null,
    queryFn: async ({ signal }) => {
      const response = await clientsList({
        signal,
        headers: { "X-Organization-ID": orgId },
      });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data.items;
    },
    retry: false,
    gcTime: 0,
    refetchOnWindowFocus: false,
  });

  async function save(): Promise<void> {
    const controller = lifetime.current;
    if (!draft || !controller || controller.signal.aborted || locked.current || mustReload) return;

    locked.current = true;
    setBusy(true);
    setError("");
    const submitted = draft;
    const options = {
      signal: controller.signal,
      headers: { "X-Organization-ID": orgId },
    };

    try {
      if (id) {
        if (!submitted.expectedUpdatedAt) throw new Error("Missing concurrency token");
        const response = await projectsUpdate(
          id,
          {
            ...submitted.value,
            expected_updated_at: submitted.expectedUpdatedAt,
          },
          options,
        );
        if (response.status !== 200) {
          throw new ApiError(response.status, response.data);
        }
        if (controller.signal.aborted) return;
        setDraft(null);
        setNotice(t("projects.saved"));
        void query.refetch();
      } else {
        const response = await projectsCreate(submitted.value, options);
        if (response.status !== 201) {
          throw new ApiError(response.status, response.data);
        }
        if (controller.signal.aborted) return;
        flushSync(() => setDraft(null));
        navigate(`/projects/${encodeURIComponent(response.data.id)}`);
      }
    } catch (caught) {
      if (controller.signal.aborted) return;
      const status = caught instanceof ApiError ? caught.status : null;
      setError(
        t(
          status === 409 || status === 412
            ? "projects.conflict"
            : status === 403
              ? "projects.denied"
              : status === 400 || status === 422
                ? "projects.invalid"
                : "projects.uncertain",
        ),
      );
      setMustReload(status !== 400 && status !== 422);
    } finally {
      if (!controller.signal.aborted) {
        locked.current = false;
        setBusy(false);
      }
    }
  }

  async function reload(): Promise<void> {
    if (draft && !window.confirm(t("projects.discard"))) return;
    setDraft(null);
    const result = await query.refetch();
    if (lifetime.current?.signal.aborted) return;
    if (!result.isError) {
      setMustReload(false);
      setError("");
    }
  }

  async function deletePosition(position: PositionResponse): Promise<void> {
    const controller = lifetime.current;
    if (
      !controller ||
      controller.signal.aborted ||
      locked.current ||
      !window.confirm(t("projects.deleteConfirm"))
    )
      return;
    locked.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const response = await positionsDestroy(
        position.id,
        { expected_updated_at: position.updated_at },
        { headers: { "X-Organization-ID": orgId }, signal: controller.signal },
      );
      if (response.status !== 204) throw new ApiError(response.status, response.data);
      if (controller.signal.aborted) return;
      setNotice(t("projects.deleted"));
      await query.refetch();
    } catch (caught) {
      if (!controller.signal.aborted)
        setError(
          t(
            caught instanceof ApiError && caught.status === 409
              ? "projects.conflict"
              : "projects.saveError",
          ),
        );
    } finally {
      if (!controller.signal.aborted) {
        locked.current = false;
        setBusy(false);
      }
    }
  }

  async function clone(project: ProjectResponse): Promise<void> {
    const controller = lifetime.current;
    if (!controller || controller.signal.aborted || locked.current || mustReload) return;
    if (
      (draft !== null || quotationDirty || paymentsDirty || importsDirty) &&
      !window.confirm(t("projects.leaveUnsaved"))
    )
      return;
    locked.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const response = await projectsClone(
        project.id,
        { expected_updated_at: project.updated_at },
        { headers: { "X-Organization-ID": orgId }, signal: controller.signal },
      );
      if (response.status !== 201) throw new ApiError(response.status, response.data);
      if (controller.signal.aborted) return;
      flushSync(() => {
        setQuotationDirty(false);
        setPaymentsDirty(false);
        setImportsDirty(false);
      });
      navigate(`/projects/${response.data.id}`);
    } catch (caught) {
      if (controller.signal.aborted) return;
      const status = caught instanceof ApiError ? caught.status : null;
      setError(t(status === 409 ? "projects.conflict" : "projects.uncertain"));
      setMustReload(true);
    } finally {
      if (!controller.signal.aborted) {
        locked.current = false;
        setBusy(false);
      }
    }
  }

  if (query.isPending) return <p role="status">{t("projects.loading")}</p>;
  if (query.isError) {
    return (
      <section className="projects-page">
        <p role="alert">{t("projects.loadError")}</p>
        <button onClick={() => void reload()}>{t("projects.reload")}</button>
      </section>
    );
  }

  const { project, items } = query.data;
  const disabled = busy || query.isFetching || mustReload;
  const editable = canWrite && project?.status === "DRAFT" && !project.pricing_current;
  const needle = search.toLocaleLowerCase("es-CL");
  const visible = items.filter((item) =>
    `${item.code} ${item.name} ${item.client_name}`.toLocaleLowerCase("es-CL").includes(needle),
  );

  return (
    <section className="projects-page" aria-busy={busy || query.isFetching}>
      <UnsavedChangesGuard
        dirty={draft !== null || quotationDirty || paymentsDirty || importsDirty}
        message={t("projects.leaveUnsaved")}
      />
      <h1>{project ? `${project.code} · ${project.name}` : t("projects.title")}</h1>
      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}
      {mustReload && (
        <button disabled={busy} onClick={() => void reload()}>
          {t("projects.reload")}
        </button>
      )}

      {draft ? (
        <ProjectMetadataForm
          draft={draft}
          clients={clientsQuery.data ?? []}
          disabled={disabled}
          onChange={setDraft}
          onSave={() => void save()}
          onCancel={() => {
            if (window.confirm(t("projects.discard"))) setDraft(null);
          }}
        />
      ) : (
        <div className="projects-actions">
          {project && <Link to="/projects">{t("projects.back")}</Link>}
          {editable && (
            <button
              disabled={disabled}
              onClick={() =>
                setDraft({
                  value: metadata(project!),
                  expectedUpdatedAt: project!.updated_at,
                })
              }
            >
              {t("projects.edit")}
            </button>
          )}
          {project && canWrite && (
            <button disabled={disabled} onClick={() => void clone(project)}>
              {t("projects.cloneDraft")}
            </button>
          )}
          {!project && canWrite && (
            <button disabled={disabled} onClick={() => setDraft({ value: metadata() })}>
              {t("projects.create")}
            </button>
          )}
        </div>
      )}

      {project ? (
        <>
          <p>{t(statuses[project.status])}</p>
          {canWrite && !editable && (
            <p className="project-locked" role="status">
              {t(project.status === "DRAFT" ? "projects.lockedPriced" : "projects.lockedQuoted")}
            </p>
          )}
          {!draft && (
            <dl className="project-metadata">
              {fields
                .filter(([name]) => name !== "name")
                .map(([name, label]) => (
                  <div key={name}>
                    <dt>{t(label)}</dt>
                    <dd>{project[name] || "—"}</dd>
                  </div>
                ))}
              <div>
                <dt>{t("projects.updated")}</dt>
                <dd>
                  <time dateTime={project.updated_at}>
                    {new Date(project.updated_at).toLocaleString("es-CL")}
                  </time>
                </dd>
              </div>
              <div>
                <dt>{t("projects.positions")}</dt>
                <dd>{project.position_count}</dd>
              </div>
              {project.pricing_current ? (
                <>
                  <div>
                    <dt>{t("projects.net")}</dt>
                    <dd>{project.total_price_net}</dd>
                  </div>
                  <div>
                    <dt>{t("projects.tax")}</dt>
                    <dd>{project.total_price_tax}</dd>
                  </div>
                  <div>
                    <dt>{t("projects.total")}</dt>
                    <dd>{project.total_price_gross}</dd>
                  </div>
                </>
              ) : (
                <div>
                  <dt>{t("projects.total")}</dt>
                  <dd>{t("projects.unpriced")}</dd>
                </div>
              )}
            </dl>
          )}
          <ProjectQuotationPanel
            project={project}
            orgId={orgId}
            canWrite={canWrite}
            onChanged={() => query.refetch()}
            onDirtyChange={setQuotationDirty}
          />
          <ProjectPaymentsPanel
            projectId={project.id}
            orgId={orgId}
            canWrite={canWrite}
            onDirtyChange={setPaymentsDirty}
          />
          <ProjectImportsPanel
            projectId={project.id}
            orgId={orgId}
            canWrite={canWrite && editable}
            onChanged={() => query.refetch()}
            onDirtyChange={setImportsDirty}
          />
          <section>
            <div className="projects-actions">
              <h2>{t("projects.positions")}</h2>
              {editable && (
                <Link className="primary-action" to={`/projects/${project.id}/positions/new`}>
                  {t("projects.addPosition")}
                </Link>
              )}
              {canWrite &&
                project.status === "DRAFT" &&
                !project.pricing_current &&
                project.position_count > 0 && (
                  <Link to={`/projects/${project.id}/pricing`}>{t("projects.priceProject")}</Link>
                )}
            </div>
            {project.position_count === 0 && <p>{t("projects.noPositions")}</p>}
            {project.positions?.map((position) => (
              <article className="project-position" key={position.id}>
                <PositionThumb design={position.design} />
                <div className="project-position-body">
                  <div className="projects-actions">
                    <strong>
                      {position.position_index}. {position.location_tag || t("projects.position")}
                    </strong>
                    <span>
                      {position.design.nominal_width_mm} × {position.design.nominal_height_mm} mm
                    </span>
                    <span>
                      {t("pricing.quantity")}: {position.quantity}
                    </span>
                    {editable && (
                      <Link to={`/projects/${project.id}/positions/${position.id}/edit`}>
                        {t("projects.openPosition")}
                      </Link>
                    )}
                    {editable && (
                      <Link to={`/projects/${project.id}/positions/new?copy=${position.id}`}>
                        {t("projects.duplicatePosition")}
                      </Link>
                    )}
                    {editable && (
                      <button disabled={disabled} onClick={() => void deletePosition(position)}>
                        {t("projects.deletePosition")}
                      </button>
                    )}
                  </div>
                  <ProjectBom result={position.bom} />
                </div>
              </article>
            ))}
          </section>
        </>
      ) : (
        <>
          <label>
            {t("projects.search")}
            <input value={search} onChange={(event) => setSearch(event.target.value)} />
          </label>
          <div className="projects-table">
            <table>
              <caption>{t("projects.title")}</caption>
              <thead>
                <tr>
                  <th scope="col">{t("projects.name")}</th>
                  <th scope="col">{t("projects.client")}</th>
                  <th scope="col">{t("projects.status")}</th>
                  <th scope="col">{t("projects.positions")}</th>
                  <th scope="col">{t("projects.updated")}</th>
                  <th scope="col">{t("projects.total")}</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((item) => (
                  <tr key={item.id}>
                    <td>
                      {draft ? (
                        `${item.code} · ${item.name}`
                      ) : (
                        <Link to={`/projects/${encodeURIComponent(item.id)}`}>
                          {item.code} · {item.name}
                        </Link>
                      )}
                    </td>
                    <td>{item.client_name}</td>
                    <td>{t(statuses[item.status])}</td>
                    <td>{item.position_count}</td>
                    <td>
                      <time dateTime={item.updated_at}>
                        {new Date(item.updated_at).toLocaleString("es-CL")}
                      </time>
                    </td>
                    <td>
                      {item.pricing_current ? item.total_price_gross : t("projects.unpriced")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {visible.length === 0 && <p>{t("projects.empty")}</p>}
        </>
      )}
    </section>
  );
}
