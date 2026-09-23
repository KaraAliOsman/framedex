import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { ApiError } from "../../api/apiMutator";
import { UnsavedChangesGuard } from "../../app/UnsavedChangesGuard";
import {
  clientsCreate,
  clientsDeactivate,
  clientsList,
  clientsUpdate,
} from "../../api/generated/dekopen";
import type { ClientResponse } from "../../api/generated/models";
import type { PatchedClientUpdateRequest } from "../../api/generated/models/patchedClientUpdateRequest";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { t } from "../../i18n/es-CL";
import "./projects.css";

const clientFields = [
  ["name", "clients.name", "text", 255],
  ["rut", "clients.rut", "text", 50],
  ["email", "clients.email", "email", undefined],
  ["phone", "clients.phone", "tel", 50],
  ["address", "clients.address", "textarea", undefined],
  ["notes", "clients.notes", "textarea", undefined],
] as const;

type Draft = {
  value: PatchedClientUpdateRequest;
  expectedUpdatedAt?: string;
};

function empty(): Draft {
  return {
    value: { name: "", rut: "", email: "", phone: "", address: "", notes: "" },
  };
}

function filled(client: ClientResponse): Draft {
  return {
    value: {
      name: client.name,
      rut: client.rut,
      email: client.email,
      phone: client.phone,
      address: client.address,
      notes: client.notes,
    },
    expectedUpdatedAt: client.updated_at,
  };
}

/** Client registry: the same contact data a project header asks for lives
 * once here; the project form picks a client and keeps its own snapshot. */
export function ClientsPage(): JSX.Element {
  const auth = useAuthSession();
  const org = auth.me?.active_organization;

  if (!org || !["OWNER", "ESTIMATOR", "WORKSHOP_MANAGER"].includes(org.role)) {
    return <p role="alert">{t("projects.denied")}</p>;
  }
  return (
    <ClientsWorkspace
      key={org.id}
      orgId={org.id}
      canWrite={org.role === "OWNER" || org.role === "ESTIMATOR"}
    />
  );
}

function ClientsWorkspace({ orgId, canWrite }: { orgId: string; canWrite: boolean }): JSX.Element {
  const [draft, setDraft] = useState<Draft | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const lifetime = useRef<AbortController | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    lifetime.current = controller;
    return () => controller.abort();
  }, []);

  const query = useQuery<ClientResponse[]>({
    queryKey: ["clients", orgId],
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
    if (!draft || !controller || controller.signal.aborted) return;
    setBusy(true);
    setError("");
    setNotice("");
    const options = { signal: controller.signal, headers: { "X-Organization-ID": orgId } };
    try {
      if (editing) {
        const response = await clientsUpdate(
          editing,
          { ...draft.value, expected_updated_at: draft.expectedUpdatedAt },
          options,
        );
        if (response.status !== 200) throw new ApiError(response.status, response.data);
        setNotice(t("clients.saved"));
      } else {
        const response = await clientsCreate(
          {
            name: draft.value.name ?? "",
            rut: draft.value.rut ?? "",
            email: draft.value.email ?? "",
            phone: draft.value.phone ?? "",
            address: draft.value.address ?? "",
            notes: draft.value.notes ?? "",
          },
          options,
        );
        if (response.status !== 201) throw new ApiError(response.status, response.data);
        setNotice(t("clients.saved"));
      }
      if (controller.signal.aborted) return;
      setDraft(null);
      setEditing(null);
      void query.refetch();
    } catch (caught) {
      if (controller.signal.aborted) return;
      const status = caught instanceof ApiError ? caught.status : null;
      setError(
        t(
          status === 409
            ? "projects.conflict"
            : status === 400 || status === 422
              ? "projects.invalid"
              : "projects.uncertain",
        ),
      );
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  }

  async function deactivate(client: ClientResponse): Promise<void> {
    const controller = lifetime.current;
    if (!controller || controller.signal.aborted || !window.confirm(t("clients.deactivateConfirm")))
      return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const response = await clientsDeactivate(client.id, {
        signal: controller.signal,
        headers: { "X-Organization-ID": orgId },
      });
      if (response.status !== 204) throw new ApiError(response.status, response.data);
      if (controller.signal.aborted) return;
      setNotice(t("clients.deactivated"));
      void query.refetch();
    } catch (caught) {
      if (!controller.signal.aborted)
        setError(t(caught instanceof ApiError ? "projects.uncertain" : "projects.uncertain"));
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  }

  if (query.isPending) return <p role="status">{t("projects.loading")}</p>;
  if (query.isError) {
    return (
      <section className="projects-page">
        <p role="alert">{t("projects.loadError")}</p>
        <button onClick={() => void query.refetch()}>{t("projects.reload")}</button>
      </section>
    );
  }

  const needle = search.toLocaleLowerCase("es-CL");
  const visible = query.data.filter((item) =>
    `${item.name} ${item.rut} ${item.email}`.toLocaleLowerCase("es-CL").includes(needle),
  );

  return (
    <section className="projects-page" aria-busy={busy || query.isFetching}>
      <UnsavedChangesGuard dirty={draft !== null} message={t("projects.leaveUnsaved")} />
      <h1>{t("clients.title")}</h1>
      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}

      {draft ? (
        <form
          className="project-metadata-form"
          onSubmit={(event) => {
            event.preventDefault();
            if (!busy) void save();
          }}
        >
          <fieldset disabled={busy}>
            <legend>{t(editing ? "clients.edit" : "clients.new")}</legend>
            {clientFields.map(([name, label, type, maxLength]) => {
              const props = {
                name,
                value: (draft.value[name] as string | undefined) ?? "",
                required: name === "name",
                maxLength,
                onChange: (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
                  setDraft({
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
          <button
            type="button"
            disabled={busy}
            onClick={() => {
              if (window.confirm(t("projects.discard"))) {
                setDraft(null);
                setEditing(null);
              }
            }}
          >
            {t("projects.cancel")}
          </button>
        </form>
      ) : (
        <div className="projects-actions">
          <label>
            {t("projects.search")}
            <input value={search} onChange={(event) => setSearch(event.target.value)} />
          </label>
          {canWrite && (
            <button disabled={busy} onClick={() => setDraft(empty())}>
              {t("clients.new")}
            </button>
          )}
        </div>
      )}

      {!draft && (
        <div className="projects-table">
          <table>
            <caption>{t("clients.title")}</caption>
            <thead>
              <tr>
                <th scope="col">{t("clients.name")}</th>
                <th scope="col">{t("clients.rut")}</th>
                <th scope="col">{t("clients.email")}</th>
                <th scope="col">{t("clients.phone")}</th>
                <th scope="col">{t("clients.status")}</th>
                {canWrite && <th scope="col">{t("clients.actions")}</th>}
              </tr>
            </thead>
            <tbody>
              {visible.map((item) => (
                <tr key={item.id}>
                  <td>{item.name}</td>
                  <td>{item.rut || "—"}</td>
                  <td>{item.email || "—"}</td>
                  <td>{item.phone || "—"}</td>
                  <td>{t(item.is_active ? "clients.active" : "clients.inactive")}</td>
                  {canWrite && (
                    <td>
                      <button
                        disabled={busy}
                        onClick={() => {
                          setEditing(item.id);
                          setDraft(filled(item));
                        }}
                      >
                        {t("projects.edit")}
                      </button>
                      {item.is_active && (
                        <button disabled={busy} onClick={() => void deactivate(item)}>
                          {t("clients.deactivate")}
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
              {visible.length === 0 && (
                <tr>
                  <td colSpan={canWrite ? 6 : 5}>{t("clients.empty")}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
