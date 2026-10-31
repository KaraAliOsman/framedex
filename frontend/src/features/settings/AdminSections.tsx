import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ApiError, apiFetchBlob } from "../../api/apiMutator";
import {
  companyGet,
  companySave,
  companyUsers,
  companyUserUpdate,
  companyInvite,
  companyInvitationRevoke,
  companyNumbering,
  quotationNumberingGet,
  quotationNumberingSave,
  projectsList,
  projectsRetrieve,
  getCompanyDocumentPreviewUrl,
} from "../../api/generated/dekopen";
import type { Company, CompanyUser, OrgBrandingWriteRequest } from "../../api/generated/models";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { planIncludes, planName, seatsText, useOrganizationPlan } from "../../app/organizationPlan";
import { actionErrorDetail } from "../errors";
import { formatDate } from "../money";
import {
  Button,
  BlockedState,
  DeniedState,
  EmptyState,
  ErrorState,
  LoadingState,
  StatusBadge,
  ValidatedForm,
  useConfirm,
} from "../../ui";

export const roleNames: Record<string, string> = {
  OWNER: "Dueño",
  ESTIMATOR: "Estimador",
  WORKSHOP_MANAGER: "Jefe de taller",
  OPERATOR: "Operario",
  INSTALLER: "Instalador",
};

/** Without the Empresa roles, each person is named by what they do. */
const SEAT_NAMES: Record<string, string> = {
  OWNER: "Dueño o socio",
  ESTIMATOR: "Oficina",
  WORKSHOP_MANAGER: "Taller",
  OPERATOR: "Operario",
  INSTALLER: "Instalador",
};

const SEAT_DUTIES: Record<string, string> = {
  OWNER: "Socio: ve y hace todo, también el plan y los cobros.",
  ESTIMATOR: "Oficina: cotiza, vende y cobra.",
  WORKSHOP_MANAGER: "Taller: produce, compra y despacha.",
};

export function CompanyCard({
  orgId,
  canEdit,
  onSaved,
  revision,
}: {
  orgId: string;
  canEdit: boolean;
  onSaved?: (company: Company, previous: string) => void;
  revision?: { previous?: string; updated: string };
}): JSX.Element {
  const auth = useAuthSession(),
    confirm = useConfirm();
  const options = useMemo(() => ({ headers: { "X-Organization-ID": orgId } }), [orgId]);
  const [draft, setDraft] = useState<Company | null>(null),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  const query = useQuery({
    queryKey: ["company", orgId],
    queryFn: async ({ signal }) => {
      const r = await companyGet({ ...options, signal });
      if (r.status !== 200) throw new ApiError(r.status, r.data);
      return r.data;
    },
  });
  useEffect(() => {
    if (query.data) setDraft(query.data);
  }, [query.data]);
  useEffect(() => {
    if (revision)
      setDraft((previous) =>
        previous !== null && previous.updated_at === revision.previous
          ? { ...previous, updated_at: revision.updated }
          : previous,
      );
  }, [revision]);
  if (query.isPending) return <LoadingState label="Cargando empresa" />;
  if (query.isError)
    return (
      <ErrorState
        body="No pudimos consultar la empresa. Reintenta la conexión."
        onRetry={() => void query.refetch()}
      />
    );
  return (
    <section className="settings-card">
      <h2>Identidad legal y moneda</h2>
      <p>
        Estos datos identifican al emisor de documentos nuevos. La moneda se propone al calcular;
        los acuerdos emitidos conservan su moneda. Las tarifas de trabajo conservan su moneda base
        {draft?.base_currency ? ` ${draft.base_currency}` : ""}.
      </p>
      {!canEdit && <p>El dueño puede cambiar la identidad legal y la política de acceso.</p>}
      {message && <p role="status">{message}</p>}
      {message && <Button onClick={() => void query.refetch()}>Recargar empresa</Button>}
      {draft && (
        <ValidatedForm
          className="settings-company-form"
          onSubmit={(event) => {
            event.preventDefault();
            void (async () => {
              if (busy || !canEdit) return;
              if (
                !(await confirm({
                  title: "Guardar empresa",
                  body: `Se usará ${draft.name} y moneda ${draft.currency} para nuevos trabajos.${draft.require_mfa ? " Todos deberán verificar segundo factor para entrar." : " El dueño conserva segundo factor obligatorio."}`,
                }))
              )
                return;
              setBusy(true);
              setMessage("");
              try {
                const r = await companySave(
                  {
                    name: draft.name,
                    tax_id: draft.tax_id,
                    currency: draft.currency,
                    require_mfa: draft.require_mfa,
                    expected_updated_at: draft.updated_at,
                  },
                  options,
                );
                if (r.status !== 200) throw new ApiError(r.status, r.data);
                setDraft(r.data);
                onSaved?.(r.data, draft.updated_at);
                await auth.refreshContext();
                setMessage("Empresa guardada para nuevos trabajos.");
              } catch (error) {
                setMessage(
                  actionErrorDetail(
                    error,
                    "No se guardó. Revisa el RUT y vuelve a cargar si otra persona editó la empresa.",
                  ),
                );
              } finally {
                setBusy(false);
              }
            })();
          }}
        >
          <fieldset disabled={busy || !canEdit}>
            <legend className="sr-only">Empresa</legend>
            <label>
              Razón social
              <input
                required
                maxLength={255}
                value={draft.name}
                onChange={(event) => setDraft({ ...draft, name: event.target.value })}
              />
            </label>
            <label>
              RUT legal
              <input
                required
                maxLength={50}
                value={draft.tax_id}
                onChange={(event) => setDraft({ ...draft, tax_id: event.target.value })}
              />
            </label>
            <label>
              Moneda por defecto
              <select
                value={draft.currency}
                onChange={(event) =>
                  setDraft({ ...draft, currency: event.target.value as Company["currency"] })
                }
              >
                <option value="CLP">Peso chileno · CLP</option>
                <option value="USD">Dólar estadounidense · USD</option>
              </select>
            </label>
            <label>
              <input
                type="checkbox"
                checked={draft.require_mfa}
                onChange={(event) => setDraft({ ...draft, require_mfa: event.target.checked })}
              />
              Exigir segundo factor a todos los usuarios
            </label>
            <p className="settings-defaults">
              Por defecto: segundo factor obligatorio para el dueño y opcional para los demás. Esta
              política se aplica en la API y la base de datos.
            </p>
          </fieldset>
          {canEdit && (
            <Button type="submit" variant="primary" disabled={busy}>
              Guardar empresa
            </Button>
          )}
        </ValidatedForm>
      )}
    </section>
  );
}

function UserRow({
  user,
  orgId,
  onSaved,
  roles,
  names,
}: {
  user: CompanyUser;
  orgId: string;
  onSaved: () => Promise<unknown>;
  /** The roles the plan offers; a role kept from a larger plan stays listed. */
  roles: string[];
  names: Record<string, string>;
}): JSX.Element {
  const confirm = useConfirm();
  const [role, setRole] = useState(user.role),
    [active, setActive] = useState(user.is_active),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    setRole(user.role);
    setActive(user.is_active);
  }, [user]);
  return (
    <ValidatedForm
      className="settings-user"
      onSubmit={(event) => {
        event.preventDefault();
        void (async () => {
          if (
            busy ||
            !(await confirm({
              title: "Cambiar acceso",
              body: `${user.email}: ${names[role]} · ${active ? "activo" : "desactivado"}. El cambio se aplica en su siguiente petición y queda auditado.`,
            }))
          )
            return;
          setBusy(true);
          setError("");
          try {
            await companyUserUpdate(
              user.id,
              { role, is_active: active, expected_updated_at: user.updated_at },
              { headers: { "X-Organization-ID": orgId } },
            );
            await onSaved();
          } catch (error) {
            setError(
              actionErrorDetail(
                error,
                "No se cambió el acceso. Conserva al menos un dueño activo y recarga si hubo otra edición.",
              ),
            );
          } finally {
            setBusy(false);
          }
        })();
      }}
    >
      <strong>{user.email}</strong>
      <label>
        Hace
        <select
          value={role}
          disabled={busy}
          onChange={(event) => setRole(event.target.value as CompanyUser["role"])}
        >
          {Object.entries(names)
            .filter(([value]) => roles.includes(value) || value === user.role)
            .map(([value, label]) => (
              <option value={value} key={value}>
                {label}
              </option>
            ))}
        </select>
      </label>
      <label>
        <input
          type="checkbox"
          disabled={busy}
          checked={active}
          onChange={(event) => setActive(event.target.checked)}
        />
        Activo
      </label>
      <Button type="submit" disabled={busy || (role === user.role && active === user.is_active)}>
        Guardar acceso
      </Button>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
    </ValidatedForm>
  );
}

export function UsersCard({ orgId, canEdit }: { orgId: string; canEdit: boolean }): JSX.Element {
  const confirm = useConfirm(),
    options = { headers: { "X-Organization-ID": orgId } };
  const plan = useOrganizationPlan(canEdit ? orgId : undefined);
  const [email, setEmail] = useState(""),
    [role, setRole] = useState<CompanyUser["role"]>("ESTIMATOR"),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState(""),
    [key, setKey] = useState(() => crypto.randomUUID());
  const query = useQuery({
    queryKey: ["company-users", orgId],
    enabled: canEdit,
    queryFn: async ({ signal }) => {
      const r = await companyUsers({ ...options, signal });
      if (r.status !== 200) throw new ApiError(r.status, r.data);
      return r.data;
    },
  });
  if (!canEdit)
    return (
      <DeniedState reason="Solo el dueño invita usuarios, cambia roles y desactiva accesos. Pídele que revise tu acceso." />
    );
  if (query.isPending || plan.isPending)
    return <LoadingState label="Cargando usuarios e invitaciones" />;
  if (query.isError || plan.isError)
    return (
      <ErrorState
        body="No pudimos consultar usuarios. Reintenta la conexión."
        onRetry={() => void Promise.all([query.refetch(), plan.refetch()])}
      />
    );
  const terms = plan.data;
  const withRoles = planIncludes(terms, "roles");
  const names = withRoles ? roleNames : SEAT_NAMES;
  const offered: string[] = terms.roles;
  // Office first when the plan offers it; the owner is the fallback.
  const chosen = (
    offered.includes(role) ? role : offered.includes("ESTIMATOR") ? "ESTIMATOR" : offered[0]
  ) as CompanyUser["role"];
  const refresh = () => Promise.all([query.refetch(), plan.refetch()]);
  // One person who does everything; a downgraded team keeps its people instead.
  const solo = terms.seats === 1 && terms.active_members <= 1;
  const canInvite = !solo && terms.seats_left !== 0;
  return (
    <section className="settings-card">
      <h2>{withRoles ? "Usuarios y roles" : "Equipo"}</h2>
      <p className="settings-plan-seats">
        Plan {planName(terms.code)} · {seatsText(terms)}
      </p>
      {solo ? (
        <div className="settings-solo">
          <p>
            Trabajas solo y ves todo: cotización, taller, vidrios, montaje y la impresión para el
            maestro. No hay roles que configurar.
          </p>
          <p>
            Para sumar a alguien de oficina o de taller, el plan Pro incluye hasta tres personas.
          </p>
          <Link className="ui-button" to="/settings/billing">
            Ver planes
          </Link>
        </div>
      ) : (
        <p>
          {withRoles
            ? "Cada persona entra con su rol. Los cambios de acceso se registran y la empresa siempre conserva al menos un dueño activo."
            : "Cada persona ve lo que necesita para su trabajo, sin configurar roles. Los cambios se registran y la empresa siempre conserva al menos un dueño activo."}
        </p>
      )}
      {query.data.items.length > 1 &&
        query.data.items.map((user) => (
          <UserRow
            key={user.id}
            user={user}
            orgId={orgId}
            onSaved={refresh}
            roles={offered}
            names={names}
          />
        ))}
      {!solo && !canInvite && (
        <p className="settings-plan-full" role="note">
          Tu plan ya ocupa {terms.seats === 1 ? "su única persona" : `sus ${terms.seats} personas`}.
          Revoca una invitación, desactiva un acceso o cambia de plan para sumar a alguien.
        </p>
      )}
      {canInvite && <h3>Invitar a la empresa</h3>}
      {canInvite && (
        <ValidatedForm
          className="settings-invite"
          onSubmit={(event) => {
            event.preventDefault();
            void (async () => {
              if (
                busy ||
                !(await confirm({
                  title: "Enviar invitación",
                  body: `Se enviará a ${email} una invitación como ${names[chosen]}. El enlace vence en siete días; la persona debe aceptar con ese correo.`,
                }))
              )
                return;
              setBusy(true);
              setMessage("");
              try {
                await companyInvite(
                  { email, role: chosen, operation_key: key, confirmed: true },
                  options,
                );
                setMessage(
                  "Invitación registrada en la bandeja de correo. Revisa su estado de entrega en Integraciones.",
                );
                setEmail("");
                setKey(crypto.randomUUID());
                await refresh();
              } catch (error) {
                setMessage(
                  actionErrorDetail(
                    error,
                    "No se pudo invitar. Revisa si el correo ya pertenece a la empresa o tiene una invitación pendiente.",
                  ),
                );
              } finally {
                setBusy(false);
              }
            })();
          }}
        >
          <label>
            Correo invitado
            <input
              type="email"
              required
              maxLength={255}
              disabled={busy}
              value={email}
              onChange={(event) => {
                setEmail(event.target.value);
                setKey(crypto.randomUUID());
              }}
            />
          </label>
          {withRoles ? (
            <label>
              Rol de ingreso
              <select
                disabled={busy}
                value={chosen}
                onChange={(event) => {
                  setRole(event.target.value as CompanyUser["role"]);
                  setKey(crypto.randomUUID());
                }}
              >
                {offered.map((value) => (
                  <option key={value} value={value}>
                    {roleNames[value]}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <fieldset className="settings-seat-choice">
              <legend>¿Qué hará?</legend>
              {offered.map((value) => (
                <label key={value}>
                  <input
                    type="radio"
                    name="seat"
                    value={value}
                    disabled={busy}
                    checked={chosen === value}
                    onChange={() => {
                      setRole(value as CompanyUser["role"]);
                      setKey(crypto.randomUUID());
                    }}
                  />
                  {SEAT_DUTIES[value] ?? names[value]}
                </label>
              ))}
            </fieldset>
          )}
          <Button type="submit" variant="primary" disabled={busy}>
            Invitar y enviar correo
          </Button>
        </ValidatedForm>
      )}
      {message && <p role="status">{message}</p>}
      {(!solo || query.data.invitations.length > 0) && <h3>Invitaciones</h3>}
      {!query.data.invitations.length ? (
        solo ? null : (
          <p>Sin invitaciones todavía.</p>
        )
      ) : (
        <ul className="settings-invitations">
          {query.data.invitations.map((invite) => (
            <li key={invite.id}>
              <strong>{invite.email}</strong>
              <span>
                {names[invite.role]} · vence {formatDate(invite.expires_at)}
              </span>
              <StatusBadge
                label={
                  invite.accepted_at
                    ? "Aceptada"
                    : invite.revoked_at
                      ? "Revocada"
                      : Date.parse(invite.expires_at) < Date.now()
                        ? "Vencida"
                        : "Pendiente"
                }
                tone="neutral"
              />
              {!invite.accepted_at && !invite.revoked_at && (
                <Button
                  disabled={busy}
                  onClick={() =>
                    void (async () => {
                      if (
                        !(await confirm({
                          title: "Revocar invitación",
                          body: "El enlace dejará de permitir el ingreso a la empresa.",
                        }))
                      )
                        return;
                      setBusy(true);
                      try {
                        await companyInvitationRevoke(invite.id, options);
                        await refresh();
                      } catch (error) {
                        setMessage(
                          actionErrorDetail(
                            error,
                            "No se pudo revocar la invitación. Recarga para revisar su estado.",
                          ),
                        );
                      } finally {
                        setBusy(false);
                      }
                    })()
                  }
                >
                  Revocar
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/** Company quotation numbering: «N.º 1» by default. The number is assigned
 * once, when a work first prepares a version to issue; its revisions keep it. */
export function QuotationNumberingCard({
  orgId,
  canEdit,
}: {
  orgId: string;
  canEdit: boolean;
}): JSX.Element {
  const headers = useMemo(() => ({ "X-Organization-ID": orgId }), [orgId]);
  const query = useQuery({
    queryKey: ["quotation-numbering", orgId],
    queryFn: async ({ signal }) => {
      const r = await quotationNumberingGet({ headers, signal });
      if (r.status !== 200) throw new ApiError(r.status, r.data);
      return r.data;
    },
  });
  const [prefix, setPrefix] = useState<string | null>(null);
  const [next, setNext] = useState<number | null>(null);
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  if (query.isPending) return <LoadingState label="Consultando numeración de cotizaciones" />;
  if (query.isError)
    return (
      <ErrorState
        body="No pudimos consultar la numeración de cotizaciones."
        onRetry={() => void query.refetch()}
      />
    );
  const data = query.data;
  const shownPrefix = prefix ?? data.prefix;
  const shownNext = next ?? data.next_number;
  const minimum = (data.highest_assigned ?? 0) + 1;
  const example = shownPrefix + String(shownNext || minimum);
  return (
    <section className="settings-card">
      <h2>Numeración de cotizaciones</h2>
      <p>
        Cada obra recibe su número al preparar la primera versión para emitir. Sus revisiones
        conservan el mismo número y los documentos emitidos nunca se renumeran.
      </p>
      <ValidatedForm
        className="settings-form"
        onSubmit={async (event) => {
          event.preventDefault();
          setBusy(true);
          setStatus("");
          try {
            const r = await quotationNumberingSave(
              { prefix: shownPrefix, next_number: shownNext },
              { headers },
            );
            if (r.status !== 200) throw new ApiError(r.status, r.data);
            setPrefix(null);
            setNext(null);
            await query.refetch();
            setStatus("Numeración guardada.");
          } catch (error) {
            setStatus(actionErrorDetail(error, "No se pudo guardar la numeración."));
          } finally {
            setBusy(false);
          }
        }}
      >
        <fieldset disabled={!canEdit || busy}>
          <label>
            Prefijo
            <input
              maxLength={20}
              value={shownPrefix}
              onChange={(event) => setPrefix(event.target.value)}
            />
            <small>Se imprime antes del número. Puede quedar vacío.</small>
          </label>
          <label>
            Próximo número
            <input
              type="number"
              min={minimum}
              step={1}
              required
              value={shownNext}
              onChange={(event) => setNext(event.target.valueAsNumber)}
            />
            <small>
              {data.highest_assigned
                ? `Debe ser mayor que el último asignado (${data.highest_assigned}).`
                : "Aún no hay cotizaciones numeradas."}
            </small>
          </label>
        </fieldset>
        <p>
          Así se verá la próxima: <strong>{example}</strong>
        </p>
        {status ? <p role="status">{status}</p> : null}
        {canEdit ? (
          <Button type="submit" variant="primary" loading={busy}>
            Guardar numeración
          </Button>
        ) : (
          <p>Solo el dueño cambia la numeración.</p>
        )}
      </ValidatedForm>
    </section>
  );
}

export function NumberingCard({ orgId }: { orgId: string }): JSX.Element {
  const query = useQuery({
    queryKey: ["company-numbering", orgId],
    queryFn: async ({ signal }) => {
      const r = await companyNumbering({ headers: { "X-Organization-ID": orgId }, signal });
      if (r.status !== 200) throw new ApiError(r.status, r.data);
      return r.data;
    },
  });
  if (query.isPending) return <LoadingState label="Consultando numeración" />;
  if (query.isError)
    return (
      <ErrorState body="No pudimos consultar numeración." onRetry={() => void query.refetch()} />
    );
  return (
    <section className="settings-card">
      <h2>Numeración</h2>
      <p>
        Solo lectura. Son referencias sin reservar: otro trabajo puede usar el siguiente número
        antes de tu emisión. Proyectos usa la secuencia global; OC, recepción y retazos usan la de
        esta empresa.
      </p>
      <dl className="settings-list">
        {query.data.items.map((row) => (
          <div className="settings-row" key={row.prefix}>
            <dt>
              {
                (
                  {
                    P: "Proyecto",
                    OC: "Orden de compra",
                    RT: "Retazo",
                    REC: "Recepción",
                  } as Record<string, string>
                )[row.prefix]
              }
            </dt>
            <dd className="settings-mono">
              {row.prefix}-{String(row.next_number).padStart(6, "0")}
            </dd>
          </div>
        ))}
      </dl>
      <p>
        Las cotizaciones usan su propia numeración, arriba. Las OT y documentos de cobro conservan
        el código reservado en su emisión.
      </p>
      <Button onClick={() => void query.refetch()}>Actualizar referencia</Button>
    </section>
  );
}

export function DocumentPreview({
  orgId,
  branding,
}: {
  orgId: string;
  branding: OrgBrandingWriteRequest;
}): JSX.Element {
  const options = useMemo(() => ({ headers: { "X-Organization-ID": orgId } }), [orgId]);
  const [project, setProject] = useState(""),
    [version, setVersion] = useState(""),
    [url, setUrl] = useState(""),
    [retry, setRetry] = useState(0),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(false);
  const projects = useQuery({
    queryKey: ["settings-preview-projects", orgId],
    queryFn: async ({ signal }) => {
      const r = await projectsList({ ...options, signal });
      if (r.status !== 200) throw new ApiError(r.status, r.data);
      return r.data.items;
    },
  });
  const detail = useQuery({
    queryKey: ["settings-preview-versions", orgId, project],
    enabled: Boolean(project),
    queryFn: async ({ signal }) => {
      const r = await projectsRetrieve(project, { ...options, signal });
      if (r.status !== 200) throw new ApiError(r.status, r.data);
      return r.data;
    },
  });
  const previewable = detail.data?.versions?.filter(
    (v) => v.snapshot_sha256 && ["SHOT09_V1", "SHOT10_V1"].includes(v.authority_version),
  );
  const canPreview = Boolean(previewable?.some((v) => v.id === version));
  useEffect(() => {
    if (!project && projects.data?.length)
      setProject(
        projects.data.find((p) => p.status !== "DRAFT" && p.pricing_current)?.id ??
          projects.data.find((p) => p.status !== "DRAFT")?.id ??
          projects.data[0]!.id,
      );
  }, [projects.data, project]);
  useEffect(() => {
    setVersion(
      detail.data?.versions?.find(
        (v) => v.snapshot_sha256 && ["SHOT09_V1", "SHOT10_V1"].includes(v.authority_version),
      )?.id ??
        detail.data?.versions?.[0]?.id ??
        "",
    );
  }, [detail.data]);
  useEffect(() => {
    if (!canPreview) {
      setUrl("");
      setLoading(false);
      setError("");
      return;
    }
    const controller = new AbortController();
    let objectUrl = "";
    setLoading(true);
    setError("");
    setUrl("");
    const timer = setTimeout(() => {
      void apiFetchBlob(getCompanyDocumentPreviewUrl(), {
        method: "POST",
        headers: { ...options.headers, "Content-Type": "application/json" },
        body: JSON.stringify({ version_id: version, branding }),
        signal: controller.signal,
      })
        .then(({ blob }) => {
          if (controller.signal.aborted) return;
          objectUrl = URL.createObjectURL(blob);
          setUrl(objectUrl);
          setLoading(false);
        })
        .catch((error) => {
          if (!controller.signal.aborted) {
            setError(
              actionErrorDetail(
                error,
                "Revisa los ajustes ingresados y elige una cotización con snapshot verificable.",
              ),
            );
            setLoading(false);
          }
        });
    }, 400);
    return () => {
      clearTimeout(timer);
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [options, version, branding, retry, detail.data, canPreview]);
  return (
    <section className="settings-preview" aria-label="Vista previa del PDF real">
      <h2>Documento de referencia</h2>
      <p>
        PDF real con tus cambios en preparación. Conserva precio y moneda de la revisión elegida;
        guardar los ajustes solo cambia emisiones nuevas.
      </p>
      {projects.isPending ? (
        <LoadingState label="Buscando obras para la vista previa" />
      ) : projects.isError ? (
        <ErrorState body="No pudimos buscar obras." onRetry={() => void projects.refetch()} />
      ) : projects.data.length === 0 ? (
        <EmptyState
          title="Sin cotización de referencia"
          body="Crea tu primera obra y emite una cotización. Luego podrás revisar este PDF con datos reales."
          action={
            <Link className="ui-button" to="/onboarding">
              Crear primera obra
            </Link>
          }
        />
      ) : (
        <>
          <label>
            Obra
            <select
              aria-label="Obra"
              value={project}
              onChange={(event) => {
                const selected = event.target.value;
                if (selected === project) return;
                setProject(selected);
                setVersion("");
              }}
            >
              {projects.data.map((p) => (
                <option value={p.id} key={p.id}>
                  {p.code} · {p.name}
                </option>
              ))}
            </select>
          </label>
          {detail.isPending ? (
            <LoadingState label="Consultando revisiones" />
          ) : detail.isError ? (
            <ErrorState
              body="No pudimos consultar esta obra."
              onRetry={() => void detail.refetch()}
            />
          ) : detail.data?.versions?.length ? (
            <label>
              Revisión de referencia
              <select value={version} onChange={(event) => setVersion(event.target.value)}>
                {detail.data.versions.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.revision_code.replace("REV-", "Revisión ")}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <BlockedState
              reason="Esta obra todavía no tiene una revisión emitida. El dueño o estimador debe revisar y emitir su cotización, o elegir otra obra."
              action={
                <Link className="ui-button" to={`/projects/${project}?section=documents`}>
                  Preparar cotización de esta obra
                </Link>
              }
            />
          )}
        </>
      )}
      {loading && <LoadingState label="Renderizando el PDF con tus ajustes" />}
      {version && !canPreview && (
        <BlockedState
          reason="Esta revisión histórica no tiene la trazabilidad requerida para generar una nueva vista previa. Elige una revisión emitida reciente; su documento original se conserva."
          action={
            <Link className="ui-button" to={`/projects/${project}?section=quote`}>
              Abrir cotización de la obra
            </Link>
          }
        />
      )}
      {error && <ErrorState body={error} onRetry={() => setRetry((previous) => previous + 1)} />}
      {url && (
        <>
          <iframe title="PDF real de referencia" src={url} />
          <a className="ui-button" href={url} target="_blank" rel="noreferrer">
            Abrir PDF completo
          </a>
        </>
      )}
    </section>
  );
}
