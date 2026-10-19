import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "../../api/apiMutator";
import {
  companyDesignDefaults,
  companyDesignDefaultsSave,
  engineSystems,
  projectDesignOptions,
  projectsUpdate,
} from "../../api/generated/dekopen";
import type { DesignDefaults, ProjectResponse } from "../../api/generated/models";
import { domainLabel } from "../../i18n/domainLabels";
import { Button } from "../../ui";
import { Icon } from "../../ui/Icon";
import "./design-defaults.css";

type Key = "system_id" | "color" | "glass_article_sku";
type Effective = Partial<Record<Key, { value: string; source: "company" | "project" }>>;

function useSystems(orgId: string) {
  return useQuery({
    queryKey: ["project-systems", orgId],
    queryFn: async () => {
      const response = await engineSystems({ headers: { "X-Organization-ID": orgId } });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data.systems;
    },
    retry: false,
    staleTime: 60_000,
  });
}

function useOptions(orgId: string, systemId: string | undefined) {
  return useQuery({
    queryKey: ["project-design-options", orgId, systemId],
    enabled: Boolean(systemId),
    queryFn: async () => {
      const response = await projectDesignOptions(systemId!, {
        headers: { "X-Organization-ID": orgId },
      });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
    retry: false,
    staleTime: 60_000,
  });
}

/** Human labels for a set of usual values (used in summaries). */
export function useDefaultLabels(orgId: string, values: Partial<Record<Key, string>>) {
  const systems = useSystems(orgId);
  const options = useOptions(orgId, values.system_id);
  const system = systems.data?.find((item) => item.id === values.system_id);
  const finish = options.data?.finish_authority?.colors.find((item) => item.code === values.color);
  const glass = options.data?.glass_specs.find((item) => item.sku === values.glass_article_sku);
  return {
    system_id: system ? system.name : values.system_id ? "Serie no disponible" : null,
    color: values.color ? (finish?.name ?? domainLabel(values.color)) : null,
    glass_article_sku: values.glass_article_sku ? (glass?.spec ?? values.glass_article_sku) : null,
  } as Record<Key, string | null>;
}

/** Series, finish and glass pickers; in project scope an empty choice means
 * «como la empresa» and shows the inherited value. */
function DefaultsForm({
  orgId,
  initial,
  inherited,
  busy,
  onSave,
  onCancel,
}: {
  orgId: string;
  initial: Partial<Record<Key, string>>;
  inherited?: Record<Key, string | null>;
  busy: boolean;
  onSave(values: DesignDefaults): void;
  onCancel?: () => void;
}): JSX.Element {
  const [values, setValues] = useState<Partial<Record<Key, string>>>(initial);
  const systems = useSystems(orgId);
  const systemForOptions = values.system_id || undefined;
  const options = useOptions(orgId, systemForOptions);
  const finishes = options.data?.finish_authority?.colors.length
    ? options.data.finish_authority.colors.map((item) => ({ code: item.code, name: item.name }))
    : (options.data?.colors ?? []).map((code) => ({ code, name: domainLabel(code) }));
  const glasses = (options.data?.glass_specs ?? []).filter((item) => item.compatible !== false);
  const project = inherited !== undefined;
  const inheritLabel = (key: Key) =>
    inherited?.[key] ? `Como la empresa · ${inherited[key]}` : "Como la empresa";
  function set(key: Key, value: string): void {
    setValues((current) => {
      const next = { ...current, [key]: value };
      // A different series invalidates the finish and glass chosen for the old one.
      if (key === "system_id" && value !== current.system_id) {
        delete next.color;
        delete next.glass_article_sku;
      }
      return next;
    });
  }
  return (
    <form
      noValidate
      className="design-defaults-form"
      onSubmit={(event) => {
        event.preventDefault();
        onSave({
          system_id: values.system_id ?? "",
          color: values.color ?? "",
          glass_article_sku: values.glass_article_sku ?? "",
        });
      }}
    >
      <label className="ui-field">
        <span className="ui-field__label">Serie</span>
        <select
          className="ui-field__input"
          value={values.system_id ?? ""}
          onChange={(event) => set("system_id", event.target.value)}
        >
          <option value="">{project ? inheritLabel("system_id") : "Elegir en cada ventana"}</option>
          {(systems.data ?? []).map((system) => (
            <option key={system.id} value={system.id}>
              {system.name}
              {system.is_demo && !system.name.includes("DEMO") ? " · DEMO" : ""}
            </option>
          ))}
        </select>
      </label>
      <label className="ui-field">
        <span className="ui-field__label">Acabado</span>
        <select
          className="ui-field__input"
          value={values.color ?? ""}
          disabled={!systemForOptions}
          onChange={(event) => set("color", event.target.value)}
        >
          <option value="">
            {project
              ? inheritLabel("color")
              : systemForOptions
                ? "El primero de la serie"
                : "Elige la serie"}
          </option>
          {finishes.map((finish) => (
            <option key={finish.code} value={finish.code}>
              {finish.name}
            </option>
          ))}
        </select>
      </label>
      <label className="ui-field">
        <span className="ui-field__label">Vidrio</span>
        <select
          className="ui-field__input"
          value={values.glass_article_sku ?? ""}
          disabled={!systemForOptions}
          onChange={(event) => set("glass_article_sku", event.target.value)}
        >
          <option value="">
            {project
              ? inheritLabel("glass_article_sku")
              : systemForOptions
                ? "El que derive el sistema"
                : "Elige la serie"}
          </option>
          {glasses.map((glass) => (
            <option key={glass.sku} value={glass.sku}>
              {glass.spec ?? glass.sku}
            </option>
          ))}
        </select>
      </label>
      <div className="design-defaults-form__actions">
        <Button type="submit" variant="primary" loading={busy}>
          Guardar
        </Button>
        {onCancel ? (
          <Button type="button" onClick={onCancel} disabled={busy}>
            Cancelar
          </Button>
        ) : null}
      </div>
    </form>
  );
}

/** Empresa › Valores habituales. */
export function CompanyDesignDefaults({
  orgId,
  canEdit,
}: {
  orgId: string;
  canEdit: boolean;
}): JSX.Element {
  const client = useQueryClient();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const query = useQuery({
    queryKey: ["company-design-defaults", orgId],
    queryFn: async () => {
      const response = await companyDesignDefaults({ headers: { "X-Organization-ID": orgId } });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
    retry: false,
  });
  const labels = useDefaultLabels(orgId, query.data?.values ?? {});
  async function save(values: DesignDefaults): Promise<void> {
    setBusy(true);
    setMessage("");
    try {
      const response = await companyDesignDefaultsSave(
        { values },
        { headers: { "X-Organization-ID": orgId } },
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      client.setQueryData(["company-design-defaults", orgId], response.data);
      void client.invalidateQueries({ queryKey: ["project", orgId] });
      setMessage("Guardado. Se usará en las próximas ventanas; las existentes no cambian.");
    } catch {
      setMessage("No se pudo guardar. Revisa que la serie siga disponible y vuelve a intentarlo.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="settings-card design-defaults" aria-labelledby="design-defaults-title">
      <h2 id="design-defaults-title">Valores habituales</h2>
      <p className="design-defaults__lead">
        Cada ventana nueva parte con esta serie, acabado y vidrio. Una obra puede cambiarlos y una
        ventana puede ser la excepción.
      </p>
      {query.isPending ? null : query.isError ? (
        <p role="alert">No se pudieron leer los valores habituales.</p>
      ) : canEdit ? (
        <DefaultsForm
          key={JSON.stringify(query.data.values)}
          orgId={orgId}
          initial={query.data.values}
          busy={busy}
          onSave={(values) => void save(values)}
        />
      ) : (
        <dl className="design-defaults__summary">
          <div>
            <dt>Serie</dt>
            <dd>{labels.system_id ?? "Se elige en cada ventana"}</dd>
          </div>
          <div>
            <dt>Acabado</dt>
            <dd>{labels.color ?? "El primero de la serie"}</dd>
          </div>
          <div>
            <dt>Vidrio</dt>
            <dd>{labels.glass_article_sku ?? "El que derive el sistema"}</dd>
          </div>
        </dl>
      )}
      {message ? <p role="status">{message}</p> : null}
    </section>
  );
}

/** «Habitual de esta obra»: one line with the inherited values and their origin. */
export function ProjectDesignDefaults({
  project,
  orgId,
  editable,
  onChanged,
}: {
  project: ProjectResponse;
  orgId: string;
  editable: boolean;
  onChanged(): Promise<unknown>;
}): JSX.Element | null {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const effective = (project.effective_design_defaults ?? {}) as Effective;
  const values = Object.fromEntries(
    Object.entries(effective).map(([key, item]) => [key, item?.value]),
  ) as Partial<Record<Key, string>>;
  const labels = useDefaultLabels(orgId, values);
  const company = useQuery({
    queryKey: ["company-design-defaults", orgId],
    enabled: open,
    queryFn: async () => {
      const response = await companyDesignDefaults({ headers: { "X-Organization-ID": orgId } });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
    retry: false,
  });
  const companyLabels = useDefaultLabels(orgId, company.data?.values ?? {});
  useEffect(() => setOpen(false), [project.id]);
  const own = (project.design_defaults ?? {}) as Partial<Record<Key, string>>;
  const overridden = Object.values(own).some(Boolean);
  const parts = (["system_id", "color", "glass_article_sku"] as Key[])
    .map((key) => labels[key])
    .filter(Boolean);
  if (!parts.length && !editable) return null;
  async function save(next: DesignDefaults): Promise<void> {
    setBusy(true);
    setError("");
    try {
      const response = await projectsUpdate(
        project.id,
        { design_defaults: next, expected_updated_at: project.updated_at },
        { headers: { "X-Organization-ID": orgId } },
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      setOpen(false);
      await onChanged();
    } catch (caught) {
      setError(
        caught instanceof ApiError && (caught.status === 409 || caught.status === 412)
          ? "Otra persona cambió la obra. Recarga antes de guardar."
          : "No se pudieron guardar los valores de la obra.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="project-defaults">
      <p className="project-defaults__line">
        <span className="project-defaults__label">Habitual de esta obra</span>
        <span>
          {parts.length ? parts.join(" · ") : "Sin valores habituales; se eligen en cada ventana"}
        </span>
        <span className="project-defaults__source">
          {overridden ? "Ajustado para esta obra" : parts.length ? "De la empresa" : ""}
        </span>
        {editable && !open ? (
          <button
            type="button"
            className="ui-button ui-button--ghost ui-button--compact"
            onClick={() => setOpen(true)}
          >
            <Icon name="edit" size={16} />
            Cambiar
          </button>
        ) : null}
        {editable && overridden && !open ? (
          <button
            type="button"
            className="ui-button ui-button--ghost ui-button--compact"
            disabled={busy}
            onClick={() => void save({ system_id: "", color: "", glass_article_sku: "" })}
          >
            Volver a lo de la empresa
          </button>
        ) : null}
      </p>
      {open ? (
        <DefaultsForm
          orgId={orgId}
          initial={own}
          inherited={companyLabels}
          busy={busy}
          onCancel={() => setOpen(false)}
          onSave={(next) => void save(next)}
        />
      ) : null}
      {open ? (
        <p className="project-defaults__note">Solo afecta a las ventanas nuevas de esta obra.</p>
      ) : null}
      {error ? <p role="alert">{error}</p> : null}
    </div>
  );
}
