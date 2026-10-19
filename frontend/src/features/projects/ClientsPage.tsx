import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError } from "../../api/apiMutator";
import {
  clientDirectory,
  clientDossier,
  clientMerge,
  clientMergePreview,
  clientNoteAdd,
  clientsCreate,
  clientsDeactivate,
  clientsRetrieve,
  clientsUpdate,
} from "../../api/generated/dekopen";
import type { ClientWriteRequest, ClientMergePreview } from "../../api/generated/models";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { UnsavedChangesGuard } from "../../app/UnsavedChangesGuard";
import {
  BlockedState,
  Button,
  DeniedState,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  StatusBadge,
  ValidatedForm,
  useConfirm,
} from "../../ui";
import { ClientEditor, customerKinds } from "./ClientEditor";
import { SimilarClients } from "./SimilarClients";
import { CustomerHistory } from "./CustomerHistory";
import "./clients.css";

export function customerError(error: unknown): string {
  if (error instanceof ApiError) {
    const value = error.payload as { error?: { detail?: string } };
    if (value.error?.detail) return value.error.detail;
  }
  return "No se pudo completar la acción. Revisa la conexión y vuelve a cargar la ficha antes de reintentar.";
}

export function ClientsPage(): JSX.Element {
  const org = useAuthSession().me?.active_organization;
  if (!org || !["OWNER", "ESTIMATOR", "WORKSHOP_MANAGER"].includes(org.role))
    return (
      <DeniedState reason="El dueño, estimador o jefe de taller consulta clientes. Pide acceso al dueño de tu organización." />
    );
  return (
    <ClientsWorkspace key={org.id} orgId={org.id} canWrite={org.role !== "WORKSHOP_MANAGER"} />
  );
}

function ClientsWorkspace({ orgId, canWrite }: { orgId: string; canWrite: boolean }): JSX.Element {
  const { id } = useParams();
  const navigate = useNavigate();
  const confirm = useConfirm();
  const options = useMemo(() => ({ headers: { "X-Organization-ID": orgId } }), [orgId]);
  const [search, setSearch] = useState("");
  const [q, setQ] = useState("");
  const [active, setActive] = useState(false);
  const [balance, setBalance] = useState(false);
  const [offset, setOffset] = useState(0);
  const [draft, setDraft] = useState<ClientWriteRequest | null>(null);
  const [expected, setExpected] = useState<string>();
  const [editing, setEditing] = useState<string>();
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [target, setTarget] = useState("");
  const [targetSearch, setTargetSearch] = useState("");
  const [mergeReview, setMergeReview] = useState<ClientMergePreview | null>(null);
  const [reason, setReason] = useState("");
  const [note, setNote] = useState("");
  const [noteKey, setNoteKey] = useState(() => crypto.randomUUID());
  useEffect(() => {
    const timer = setTimeout(() => {
      setQ(search);
      setOffset(0);
    }, 250);
    return () => clearTimeout(timer);
  }, [search]);
  useEffect(() => {
    setMergeReview(null);
    setTarget("");
    setReason("");
    setNote("");
    setError("");
    setNoteKey(crypto.randomUUID());
  }, [id]);
  const directory = useQuery({
    queryKey: ["clients", orgId, q, active, balance, offset],
    queryFn: async ({ signal }) => {
      const result = await clientDirectory(
        { q, with_active_projects: active, with_balance: balance, offset, limit: 50 },
        { ...options, signal },
      );
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      return result.data;
    },
  });
  const destinations = useQuery({
    queryKey: ["client-merge-destinations", orgId, targetSearch],
    enabled: canWrite && Boolean(id),
    queryFn: async ({ signal }) => {
      const result = await clientDirectory({ q: targetSearch, limit: 100 }, { ...options, signal });
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      return result.data;
    },
  });
  const dossier = useQuery({
    queryKey: ["client-dossier", orgId, id],
    enabled: Boolean(id) && canWrite,
    queryFn: async ({ signal }) => {
      const result = await clientDossier(id!, { ...options, signal });
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      return result.data;
    },
  });
  const master = useQuery({
    queryKey: ["client-master", orgId, id],
    enabled: Boolean(id) && !canWrite,
    queryFn: async ({ signal }) => {
      const result = await clientsRetrieve(id!, { ...options, signal });
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      return result.data;
    },
  });
  const client = dossier.data?.client ?? master.data;
  const refresh = async () => {
    await Promise.all([
      directory.refetch(),
      ...(id ? [canWrite ? dossier.refetch() : master.refetch()] : []),
    ]);
  };
  async function run(action: () => Promise<void>): Promise<void> {
    if (busy) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
    } catch (caught) {
      setError(customerError(caught));
    } finally {
      setBusy(false);
    }
  }
  const create = () => {
    setEditing(undefined);
    setExpected(undefined);
    setDraft({
      name: "",
      party_kind: "COMPANY",
      rut: "",
      giro: "",
      address: "",
      comuna: "",
      contacts: [],
      addresses: [],
    });
  };
  const edit = () => {
    if (!client) return;
    setEditing(client.id);
    setExpected(client.updated_at);
    setDraft({
      name: client.name,
      rut: client.rut,
      party_kind: client.party_kind ?? "UNKNOWN",
      giro: client.giro ?? "",
      address: client.address,
      comuna: client.comuna ?? "",
      contacts:
        client.contacts?.map(({ id, name, contact_role, email, phone, is_primary }) => ({
          id,
          name,
          contact_role,
          email,
          phone,
          is_primary,
        })) ?? [],
      addresses:
        client.addresses?.map(({ id, label, address, comuna }) => ({
          id,
          label,
          address,
          comuna,
        })) ?? [],
    });
  };
  return (
    <section className="customers" aria-busy={busy} data-density="office">
      <UnsavedChangesGuard
        dirty={draft !== null}
        message="Tienes cambios sin guardar en el cliente."
      />
      <PageHeader
        title="Clientes"
        context="Ficha e historia de obras"
        actions={
          canWrite && !draft ? (
            <Button variant="primary" onClick={create}>
              Nuevo cliente
            </Button>
          ) : undefined
        }
      />
      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      {draft && !editing ? (
        <SimilarClients orgId={orgId} name={draft.name ?? ""} rut={draft.rut ?? ""} />
      ) : null}
      {draft ? (
        <ClientEditor
          value={draft}
          setValue={setDraft}
          busy={busy}
          historicalRut={editing ? client?.rut : undefined}
          onCancel={() => setDraft(null)}
          onSave={() =>
            void run(async () => {
              const result = editing
                ? await clientsUpdate(editing, { ...draft, expected_updated_at: expected }, options)
                : await clientsCreate(draft, options);
              if (result.status !== 200 && result.status !== 201)
                throw new ApiError(result.status, result.data);
              setDraft(null);
              navigate(`/clients/${result.data.id}`);
              setNotice("Ficha guardada. Los proyectos emitidos conservan sus datos.");
              await refresh();
            })
          }
        />
      ) : (
        <div className="customer-desk">
          <aside className="customer-directory" aria-label="Buscar clientes">
            <label>
              Nombre o RUT
              <input value={search} onChange={(event) => setSearch(event.target.value)} />
            </label>
            <label>
              <input
                type="checkbox"
                checked={active}
                onChange={(event) => {
                  setActive(event.target.checked);
                  setOffset(0);
                }}
              />
              Con proyectos activos
            </label>
            {canWrite && (
              <label>
                <input
                  type="checkbox"
                  checked={balance}
                  onChange={(event) => {
                    setBalance(event.target.checked);
                    setOffset(0);
                  }}
                />
                Con saldo
              </label>
            )}
            {directory.isPending ? (
              <LoadingState label="Buscando clientes" />
            ) : directory.isError ? (
              <ErrorState
                body="No pudimos consultar la lista. Reintenta la conexión."
                onRetry={() => void directory.refetch()}
              />
            ) : (
              <>
                <p className="customer-hint">
                  <span className="customer-number">{directory.data.total}</span> clientes
                  encontrados
                </p>
                <ul className="customer-list">
                  {directory.data.items.map((item) => (
                    <li key={item.id}>
                      <Link
                        to={`/clients/${item.id}`}
                        aria-current={id === item.id ? "page" : undefined}
                      >
                        <strong>{item.name}</strong>
                        <span className="customer-number">{item.rut || "RUT sin registrar"}</span>
                        <span>
                          {item.has_active_projects
                            ? "Obras activas"
                            : item.is_active
                              ? "Disponible"
                              : "Inactivo"}
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
                {!directory.data.items.length && (
                  <EmptyState
                    title="Sin clientes en esta búsqueda"
                    body="Cambia los filtros o registra un cliente para crear su primera obra."
                  />
                )}
                <div className="customer-actions">
                  <Button
                    disabled={offset === 0}
                    onClick={() => setOffset(Math.max(0, offset - 50))}
                  >
                    Anterior
                  </Button>
                  <Button
                    disabled={directory.data.next_offset === null}
                    onClick={() => setOffset(directory.data!.next_offset!)}
                  >
                    Siguiente
                  </Button>
                </div>
              </>
            )}
          </aside>
          <article className="customer-dossier" aria-label="Ficha de cliente">
            {!id ? (
              <EmptyState
                title="Elige un cliente"
                body="Abre su ficha para consultar contactos, direcciones e historia."
              />
            ) : (canWrite ? dossier : master).isPending ? (
              <LoadingState label="Cargando ficha e historia" />
            ) : (canWrite ? dossier : master).isError ? (
              <ErrorState
                body="No pudimos cargar esta ficha. Revisa tu acceso y vuelve a intentar."
                onRetry={() => void refresh()}
              />
            ) : client ? (
              <>
                <header className="customer-heading">
                  <div>
                    <p className="ui-spec-label">{customerKinds[client.party_kind ?? "UNKNOWN"]}</p>
                    <h2>{client.name}</h2>
                    <p>
                      {client.rut || "RUT sin registrar"}
                      {client.giro ? ` · ${client.giro}` : ""}
                    </p>
                  </div>
                  {canWrite && !client.merged_into_id && (
                    <div className="customer-actions">
                      <Button disabled={busy} onClick={edit}>
                        Editar ficha
                      </Button>
                      {client.is_active && (
                        <Button
                          disabled={busy}
                          onClick={() =>
                            void run(async () => {
                              if (
                                await confirm({
                                  title: "Desactivar cliente",
                                  body: "Se conservarán sus proyectos y documentos. El cliente saldrá del selector de nuevas obras.",
                                  danger: true,
                                })
                              ) {
                                await clientsDeactivate(client.id, options);
                                await refresh();
                              }
                            })
                          }
                        >
                          Desactivar
                        </Button>
                      )}
                    </div>
                  )}
                </header>
                {client.rut_valid === false && (
                  <BlockedState
                    reason="El RUT histórico no pasa la validación. Verifica el dígito antes de usarlo en nuevos documentos."
                    action={
                      canWrite && !client.merged_into_id ? (
                        <Button onClick={edit}>Corregir ficha</Button>
                      ) : undefined
                    }
                  />
                )}
                {client.merged_into_id && (
                  <BlockedState
                    reason="Esta ficha fue fusionada. Su historia se conserva y se reúne en la ficha destino."
                    action={
                      <Link className="ui-button" to={`/clients/${client.merged_into_id}`}>
                        Abrir ficha consolidada
                      </Link>
                    }
                  />
                )}
                <div className="customer-identity">
                  <section>
                    <h3>Contactos</h3>
                    {client.contacts?.length ? (
                      <ul>
                        {client.contacts.map((contact) => (
                          <li key={contact.id}>
                            <strong>{contact.name || "Contacto sin nombre"}</strong>
                            {contact.contact_role && ` · ${contact.contact_role}`}{" "}
                            {contact.is_primary && <StatusBadge label="Principal" tone="neutral" />}
                            <p>{[contact.email, contact.phone].filter(Boolean).join(" · ")}</p>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p>Sin contactos. Edita la ficha para registrar correo o teléfono.</p>
                    )}
                  </section>
                  <section>
                    <h3>Direcciones de obra</h3>
                    {client.addresses?.length ? (
                      <ul>
                        {client.addresses.map((address) => (
                          <li key={address.id}>
                            <strong>{address.label}</strong>
                            <p>
                              {address.address}
                              {address.comuna ? `, ${address.comuna}` : ""}
                            </p>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p>Sin direcciones de obra. Decláralas al editar la ficha.</p>
                    )}
                    {client.address && (
                      <p className="customer-hint">
                        Facturación: {client.address}
                        {client.comuna ? `, ${client.comuna}` : ""}
                      </p>
                    )}
                  </section>
                </div>
                {canWrite ? (
                  dossier.data && <CustomerHistory history={dossier.data} />
                ) : (
                  <DeniedState reason="Tu rol consulta contactos y obras desde Proyectos. El dueño o estimador consulta pagos, saldo y notas." />
                )}
                {canWrite && !client.merged_into_id && (
                  <>
                    <ValidatedForm
                      className="customer-note"
                      onSubmit={(event) => {
                        event.preventDefault();
                        void run(async () => {
                          await clientNoteAdd(
                            client.id,
                            { body: note, operation_key: noteKey },
                            options,
                          );
                          setNote("");
                          setNoteKey(crypto.randomUUID());
                          await dossier.refetch();
                        });
                      }}
                    >
                      <label>
                        Agregar nota al historial
                        <textarea
                          required
                          maxLength={4000}
                          value={note}
                          onChange={(event) => setNote(event.target.value)}
                        />
                      </label>
                      <Button type="submit" disabled={busy || !note.trim()}>
                        Registrar nota
                      </Button>
                    </ValidatedForm>
                    <details className="customer-merge">
                      <summary>Fusionar una ficha duplicada</summary>
                      <p>
                        Revisa el destino y el efecto. Se conserva la historia de ambas fichas; solo
                        se completan campos vacíos.
                      </p>
                      <label>
                        Buscar ficha destino
                        <input
                          value={targetSearch}
                          onChange={(event) => {
                            setTargetSearch(event.target.value);
                            setTarget("");
                            setMergeReview(null);
                          }}
                        />
                      </label>
                      {destinations.isError && (
                        <ErrorState
                          body="No pudimos buscar fichas de destino."
                          onRetry={() => void destinations.refetch()}
                        />
                      )}
                      <label>
                        Ficha destino
                        <select
                          aria-label="Ficha destino"
                          value={target}
                          onChange={(event) => {
                            setTarget(event.target.value);
                            setMergeReview(null);
                          }}
                        >
                          <option value="">Elige un cliente de los resultados</option>
                          {destinations.data?.items
                            .filter((item) => item.id !== client.id && !item.merged_into_id)
                            .map((item) => (
                              <option key={item.id} value={item.id}>
                                {item.name}
                                {item.rut ? ` · ${item.rut}` : ""}
                              </option>
                            ))}
                        </select>
                      </label>
                      <Button
                        disabled={busy || !target}
                        onClick={() =>
                          void run(async () => {
                            const result = await clientMergePreview(
                              client.id,
                              { target_id: target },
                              options,
                            );
                            if (result.status !== 200)
                              throw new ApiError(result.status, result.data);
                            setMergeReview(result.data);
                          })
                        }
                      >
                        Revisar fusión
                      </Button>
                      {mergeReview && (
                        <>
                          <p>{mergeReview.consequence}</p>
                          {mergeReview.blockers.map((blocker) => (
                            <BlockedState key={blocker} reason={blocker} action={null} />
                          ))}
                          <dl>
                            {mergeReview.adopted_fields.map((field) => (
                              <div key={field.field}>
                                <dt>
                                  {
                                    (
                                      {
                                        rut: "RUT",
                                        email: "Correo",
                                        phone: "Teléfono",
                                        address: "Facturación",
                                        giro: "Giro",
                                        comuna: "Comuna",
                                        party_kind: "Tipo",
                                      } as Record<string, string>
                                    )[field.field]
                                  }
                                </dt>
                                <dd>{customerKinds[field.after ?? ""] ?? field.after}</dd>
                              </div>
                            ))}
                          </dl>
                          <p>
                            {mergeReview.added_contacts.length} contactos y{" "}
                            {mergeReview.added_addresses.length} direcciones se añadirán a{" "}
                            {mergeReview.target.name}.
                          </p>
                          <label>
                            Motivo de la fusión
                            <textarea
                              value={reason}
                              maxLength={2000}
                              onChange={(event) => setReason(event.target.value)}
                            />
                          </label>
                          <Button
                            disabled={busy || !!mergeReview.blockers.length || !reason.trim()}
                            onClick={() =>
                              void run(async () => {
                                if (
                                  !(await confirm({
                                    title: "Confirmar fusión",
                                    body: `La ficha ${mergeReview.source.name} quedará cerrada en ${mergeReview.target.name}. Esta decisión queda auditada.`,
                                  }))
                                )
                                  return;
                                const result = await clientMerge(
                                  client.id,
                                  {
                                    target_id: target,
                                    reason,
                                    confirmed: true,
                                    expected_source_updated_at: mergeReview.source.updated_at,
                                    expected_target_updated_at: mergeReview.target.updated_at,
                                  },
                                  options,
                                );
                                if (result.status !== 200)
                                  throw new ApiError(result.status, result.data);
                                navigate(`/clients/${result.data.id}`);
                                setMergeReview(null);
                                setNotice("Fusión registrada. La ficha conserva toda la historia.");
                                await refresh();
                              })
                            }
                          >
                            Confirmar fusión
                          </Button>
                        </>
                      )}
                    </details>
                  </>
                )}
              </>
            ) : null}
          </article>
        </div>
      )}
    </section>
  );
}
