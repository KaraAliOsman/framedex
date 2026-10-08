import { type FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "../../api/apiMutator";
import {
  catalogSystemList,
  engineSystems,
  clientsCreate,
  clientsList,
  projectsCreate,
  projectsList,
} from "../../api/generated/dekopen";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { Wordmark } from "../../brand/Brand";
import {
  BlockedState,
  Button,
  DeniedState,
  EmptyState,
  ErrorState,
  LoadingState,
  StatusBadge,
  Stepper,
  ValidatedForm,
} from "../../ui";
import "./onboarding.css";
import { type ClientFields, type Draft, readDraft, storageKey } from "./draft";

const STEPS = ["Serie", "Cliente", "Obra", "Primera posición"] as const;
const emptyFields: ClientFields = { rut: "", email: "", phone: "" };

export function OnboardingPage(): JSX.Element {
  const auth = useAuthSession();
  const org = auth.me?.active_organization;
  const orgId = org?.id ?? "";
  const canWrite = org?.role === "OWNER" || org?.role === "ESTIMATOR";
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState<Draft>({});
  const [restoredFor, setRestoredFor] = useState("");
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const [error, setError] = useState<string | null>(null);
  const scope = useRef({ orgId });
  if (scope.current.orgId !== orgId) scope.current = { orgId };
  const step = draft.step ?? 0;
  const fields = draft.clientExtra ?? emptyFields;
  const options = useMemo(() => ({ headers: { "X-Organization-ID": orgId } }), [orgId]);
  const update = (value: Partial<Draft>): void => setDraft((current) => ({ ...current, ...value }));

  useEffect(() => {
    setDraft(readDraft(orgId));
    setRestoredFor(orgId);
    setError(null);
    setBusy(false);
    pending.current = false;
  }, [orgId]);
  useEffect(() => {
    if (orgId && restoredFor === orgId)
      sessionStorage.setItem(storageKey(orgId), JSON.stringify({ ...draft, schema: 2 }));
  }, [draft, orgId, restoredFor]);

  const systems = useQuery({
    queryKey: ["onboarding", "systems", orgId],
    enabled: Boolean(orgId) && canWrite,
    queryFn: async ({ signal }) => {
      const [response, available] = await Promise.all([
        catalogSystemList({ ...options, signal }),
        engineSystems({ ...options, signal }),
      ]);
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      if (available.status !== 200) throw new ApiError(available.status, available.data);
      const visible = new Set(available.data.systems.map((system) => system.id));
      return response.data.items
        .filter((system) => visible.has(system.id))
        .sort((a, b) => a.name.localeCompare(b.name, "es-CL"));
    },
  });
  const selected = systems.data?.find((system) => system.id === draft.systemId);
  const offered = systems.data ?? [];
  const seriesReady = Boolean(selected?.readiness.quote_ready);
  const done = [seriesReady, Boolean(draft.clientId), Boolean(draft.projectId), false];

  // A lost response may follow a committed record. Adopt only one fresh match
  // with every submitted field, within this attempt's window and organization.
  async function adopt(kind: "client" | "project", started: number): Promise<string | null> {
    const norm = (value?: string): string => (value ?? "").trim().toLowerCase();
    const fresh = (time: string): boolean => Math.abs(Date.parse(time) - started) <= 60_000;
    try {
      if (kind === "client") {
        const response = await clientsList(options);
        if (response.status !== 200) return null;
        const matches = response.data.items.filter(
          (row) =>
            fresh(row.updated_at) &&
            norm(row.name) === norm(draft.clientName) &&
            norm(row.rut) === norm(fields.rut) &&
            norm(row.email) === norm(fields.email) &&
            norm(row.phone) === norm(fields.phone),
        );
        return matches.length === 1 ? matches[0]!.id : null;
      }
      const response = await projectsList(options);
      if (response.status !== 200) return null;
      const matches = response.data.items.filter(
        (row) =>
          fresh(row.updated_at) &&
          row.client_id === draft.clientId &&
          norm(row.name) === norm(draft.projectName) &&
          norm(row.client_name) === norm(draft.clientName) &&
          norm(row.client_rut) === norm(fields.rut) &&
          norm(row.client_email) === norm(fields.email) &&
          norm(row.client_phone) === norm(fields.phone),
      );
      return matches.length === 1 ? matches[0]!.id : null;
    } catch {
      return null;
    }
  }

  async function create(
    event: FormEvent<HTMLFormElement>,
    kind: "client" | "project",
  ): Promise<void> {
    event.preventDefault();
    if (
      !canWrite ||
      pending.current ||
      (kind === "client"
        ? !draft.clientName?.trim()
        : !draft.projectName?.trim() || !draft.clientId)
    )
      return;
    pending.current = true;
    const attemptScope = scope.current;
    const started = Date.now();
    setBusy(true);
    setError(null);
    try {
      const response =
        kind === "client"
          ? await clientsCreate({ name: draft.clientName!.trim(), ...fields }, options)
          : await projectsCreate(
              {
                name: draft.projectName!.trim(),
                client_name: draft.clientName!.trim(),
                client_id: draft.clientId!,
                client_rut: fields.rut.trim(),
                client_email: fields.email.trim(),
                client_phone: fields.phone.trim(),
              },
              options,
            );
      if (response.status !== 201) throw new ApiError(response.status, response.data);
      if (attemptScope !== scope.current) return;
      update(
        kind === "client"
          ? { clientId: response.data.id, step: 2 }
          : { projectId: response.data.id, step: 3 },
      );
      if (kind === "project")
        void queryClient.invalidateQueries({ queryKey: ["project-switcher"] });
    } catch (caught) {
      if (attemptScope !== scope.current) return;
      const adopted =
        caught instanceof ApiError && caught.status < 500 ? null : await adopt(kind, started);
      if (attemptScope !== scope.current) return;
      if (adopted) {
        update(
          kind === "client" ? { clientId: adopted, step: 2 } : { projectId: adopted, step: 3 },
        );
        if (kind === "project")
          void queryClient.invalidateQueries({ queryKey: ["project-switcher"] });
      } else
        setError(
          "No se pudo guardar. Revisa los datos y la conexión antes de volver a intentarlo.",
        );
    } finally {
      if (attemptScope === scope.current) {
        pending.current = false;
        setBusy(false);
      }
    }
  }

  if (!canWrite)
    return (
      <DeniedState reason="El dueño o el estimador crea la primera obra y sus posiciones. Pide acceso al dueño de tu organización." />
    );
  return (
    <section className="onboarding" data-density="office" aria-labelledby="onboarding-title">
      <header className="onboarding-head">
        <Wordmark width={120} />
        <p className="ui-spec-label">{org?.name}</p>
        <h1 id="onboarding-title">Dibuja tu primera ventana</h1>
        <p className="onboarding-sub">
          Elige la serie y crea la obra. El editor calcula desde el catálogo y conserva la fuente de
          cada medida.
        </p>
      </header>
      <Stepper
        current={String(step)}
        steps={STEPS.map((label, index) => ({
          id: String(index),
          label,
          onSelect: () => {
            setError(null);
            update({ step: index });
          },
          disabledReason: busy
            ? "Espera a que termine el guardado."
            : index > step && !done.slice(0, index).every(Boolean)
              ? "Completa los pasos anteriores."
              : undefined,
        }))}
      />
      <section className="onboarding-card" aria-label={STEPS[step]}>
        {step === 0 ? (
          <>
            <h2>Serie de perfiles</h2>
            <p>
              Define qué aperturas y medidas puede calcular el motor. Los catálogos de prueba se
              identifican como DEMO.
            </p>
            {systems.isPending ? (
              <LoadingState label="Cargando series disponibles" />
            ) : systems.isError ? (
              <ErrorState
                title="No se pudieron cargar las series"
                body="La conexión al catálogo falló. Vuelve a intentar la consulta."
                onRetry={() => {
                  void systems.refetch();
                }}
              />
            ) : systems.data.length === 0 ? (
              <EmptyState
                title="No hay series disponibles"
                body="El dueño o encargado debe importar y revisar el catálogo del fabricante."
                action={
                  <Link className="ui-button" to="/catalogs/systems">
                    Abrir catálogo
                  </Link>
                }
              />
            ) : (
              <div className="onboarding-systems">
                {offered.map((system) => (
                  <button
                    className={`onboarding-system${draft.systemId === system.id ? " is-picked" : ""}`}
                    type="button"
                    aria-pressed={draft.systemId === system.id}
                    disabled={!system.readiness.quote_ready}
                    key={system.id}
                    onClick={() => update({ systemId: system.id })}
                  >
                    <span>
                      <strong>
                        {system.is_demo ? system.name.replace(/\s*·\s*DEMO\s*$/u, "") : system.name}
                      </strong>
                      {!system.readiness.quote_ready ? (
                        <span>
                          {system.readiness.levels?.flatMap((level) => level.blockers)[0]?.why ??
                            "Falta completar y revisar la autoridad de la serie. Abre el catálogo para resolverla."}
                        </span>
                      ) : null}
                    </span>
                    {system.is_demo ? (
                      <StatusBadge
                        label="DEMO"
                        tone="neutral"
                        title="Datos sintéticos para probar el flujo; no certifican fabricación."
                      />
                    ) : (
                      <StatusBadge
                        label={system.readiness.quote_ready ? "Disponible" : "Bloqueada"}
                        tone={system.readiness.quote_ready ? "success" : "warning"}
                      />
                    )}
                  </button>
                ))}
              </div>
            )}
            {seriesReady ? (
              <Button variant="primary" onClick={() => update({ step: 1 })}>
                Usar esta serie
              </Button>
            ) : null}
          </>
        ) : step === 1 ? (
          <>
            <h2>Cliente</h2>
            <p>
              La cotización y los documentos quedarán asociados a esta persona o empresa. Los datos
              de contacto pueden completarse después.
            </p>
            {draft.clientId ? (
              <>
                <p>{draft.clientName} · guardado</p>
                <Button variant="primary" onClick={() => update({ step: 2 })}>
                  Continuar con la obra
                </Button>
              </>
            ) : (
              <ValidatedForm
                className="auth-form"
                onSubmit={(event) => {
                  void create(event, "client");
                }}
              >
                <label htmlFor="onb-client-name">Nombre del cliente</label>
                <input
                  id="onb-client-name"
                  required
                  disabled={busy}
                  value={draft.clientName ?? ""}
                  onChange={(event) => update({ clientName: event.target.value })}
                />
                <details>
                  <summary>Datos de contacto</summary>
                  <div className="auth-form">
                    {(
                      [
                        ["rut", "RUT"],
                        ["email", "Correo"],
                        ["phone", "Teléfono"],
                      ] as const
                    ).map(([key, label]) => (
                      <label key={key}>
                        {label}
                        <input
                          type={key === "email" ? "email" : "text"}
                          disabled={busy}
                          value={fields[key]}
                          onChange={(event) =>
                            update({ clientExtra: { ...fields, [key]: event.target.value } })
                          }
                        />
                      </label>
                    ))}
                  </div>
                </details>
                <Button
                  type="submit"
                  variant="primary"
                  disabled={busy || !draft.clientName?.trim()}
                >
                  {busy ? "Guardando cliente" : "Guardar cliente"}
                </Button>
              </ValidatedForm>
            )}
          </>
        ) : step === 2 ? (
          <>
            <h2>Obra</h2>
            <p>
              Agrupa sus ventanas, cotización y órdenes de taller. Cada posición conservará su
              ubicación dentro de la obra.
            </p>
            {draft.projectId ? (
              <>
                <p>{draft.projectName} · guardada</p>
                <Button variant="primary" onClick={() => update({ step: 3 })}>
                  Continuar al dibujo
                </Button>
              </>
            ) : draft.clientId ? (
              <ValidatedForm
                className="auth-form"
                onSubmit={(event) => {
                  void create(event, "project");
                }}
              >
                <label htmlFor="onb-project-name">Nombre de la obra</label>
                <input
                  id="onb-project-name"
                  required
                  disabled={busy}
                  value={draft.projectName ?? ""}
                  onChange={(event) => update({ projectName: event.target.value })}
                />
                <p>Cliente: {draft.clientName}</p>
                <Button
                  type="submit"
                  variant="primary"
                  disabled={busy || !draft.projectName?.trim()}
                >
                  {busy ? "Guardando obra" : "Crear obra"}
                </Button>
              </ValidatedForm>
            ) : (
              <BlockedState
                reason="Falta el cliente de esta obra. Guárdalo antes de continuar."
                action={<Button onClick={() => update({ step: 1 })}>Completar cliente</Button>}
              />
            )}
          </>
        ) : (
          <>
            <h2>Primera posición</h2>
            <p>
              El editor abre el dibujo de la serie elegida. Declara tus medidas, apertura, vidrio y
              color; el motor valida la posición antes de guardarla.
            </p>
            {draft.projectId && seriesReady ? (
              <>
                <p>
                  {draft.projectName} · {selected?.name}
                  {selected?.is_demo && !/\bDEMO\b/u.test(selected.name) ? " · DEMO" : ""}
                </p>
                <Link
                  className="ui-button ui-button--primary"
                  to={`/projects/${draft.projectId}/positions/new?system=${encodeURIComponent(draft.systemId!)}`}
                >
                  Dibujar primera posición
                </Link>
              </>
            ) : (
              <BlockedState
                reason="Falta una obra guardada o la serie ya no está disponible para cotizar. Completa ese paso antes de abrir el dibujo."
                action={
                  <Button onClick={() => update({ step: draft.projectId ? 0 : 2 })}>
                    {draft.projectId ? "Revisar serie" : "Crear obra"}
                  </Button>
                }
              />
            )}
          </>
        )}
        {error ? (
          <p className="auth-notice auth-notice--error" role="alert">
            {error}
          </p>
        ) : null}
      </section>
      <footer className="onboarding-actions">
        <Button
          variant="ghost"
          disabled={step === 0 || busy}
          onClick={() => update({ step: Math.max(0, step - 1) })}
        >
          Volver
        </Button>
        <Link className="ui-button ui-button--ghost" to="/projects">
          Continuar después
        </Link>
      </footer>
    </section>
  );
}
