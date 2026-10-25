import { lazy, Suspense, useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, Navigate, useSearchParams } from "react-router-dom";

import {
  catalogFamilyTemplates,
  catalogReferenceSeries,
  catalogSeriesCreate,
  catalogSystemList,
} from "../../api/generated/dekopen";
import type {
  FamilyTemplate,
  ReferenceSeries,
  SeriesCell,
  SeriesSheet,
  SystemResponse,
  TemplateGlazingInputRequest,
  TemplateHardwareInputRequest,
  TemplateProfileInputRequest,
  TemplateSystemInputRequest,
} from "../../api/generated/models";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { Button, DeniedState, Dialog, Loading } from "../../ui";
import { Icon } from "../../ui/Icon";
import { ValidatedForm } from "../../ui/FormValidation";
import { SeriesSheetView } from "./SeriesSheetView";
import { usageLabel } from "./seriesSheetModel";
import "./series-catalog.css";
import { SeriesTrialDialog } from "./SeriesTrialDialog";

const AdvancedCatalog = lazy(async () => ({
  default: (await import("./CatalogPage")).CatalogPage,
}));
const ImportReviewPage = lazy(async () => ({
  default: (await import("./CatalogImportReviewPage")).CatalogImportReviewPage,
}));
const SetupWizard = lazy(async () => ({
  default: (await import("./SeriesSetupWizard")).SeriesSetupWizard,
}));

function manufacturerKey(value: string | null | undefined): string {
  return (value ?? "").trim().replace(/\s+/g, " ").toLocaleLowerCase("es-CL");
}

/** Different versions keep their identity; the home shows one series entry. */
export function catalogGroups(
  systems: SystemResponse[],
): { name: string; series: SystemResponse[][] }[] {
  const brands = new Map<string, { name: string; entries: Map<string, SystemResponse[]> }>();
  for (const system of systems) {
    const brand = manufacturerKey(system.manufacturer) || "?";
    if (!brands.has(brand))
      brands.set(brand, { name: system.manufacturer?.trim() || "Tu taller", entries: new Map() });
    const entry = brands.get(brand)!;
    const key = system.code.toLocaleLowerCase("es-CL");
    entry.entries.set(key, [...(entry.entries.get(key) ?? []), system]);
  }
  return [...brands.values()]
    .map((brand) => ({
      name: brand.name,
      series: [...brand.entries.values()].map((versions) =>
        [...versions].sort((a, b) => b.version - a.version),
      ),
    }))
    .sort((a, b) => a.name.localeCompare(b.name, "es-CL"));
}

/** The suggested family template a reference series starts from: same
 * material and opening family. Its values stay «sugeridos» until confirmed. */
export function templateForReference(
  reference: ReferenceSeries,
  templates: FamilyTemplate[],
): FamilyTemplate | undefined {
  const seed = reference.seed;
  if (!seed.system_family || !seed.material) return undefined;
  return templates.find((template) => {
    const system = template.system as { material?: string; system_family?: string };
    return system.material === seed.material && system.system_family === seed.system_family;
  });
}

/** What a library series contributes to a new workshop series: its identity
 * and, when the library cites a cutting sheet, the profiles, bead and rules.
 * Prices stay the workshop's own. */
export function referenceSeriesInput(reference: ReferenceSeries | null): {
  rules?: TemplateSystemInputRequest;
  profiles?: TemplateProfileInputRequest[];
  glazing?: TemplateGlazingInputRequest[];
  hardware?: TemplateHardwareInputRequest[];
} {
  if (!reference) return {};
  const rules = {
    ...(reference.seed.depth_mm ? { depth_mm: reference.seed.depth_mm } : {}),
    ...(reference.seed.chamber_count
      ? { chamber_count: Number(reference.seed.chamber_count) }
      : {}),
    ...((reference.technical?.rules as Record<string, unknown> | undefined) ?? {}),
  };
  const technical = reference.technical;
  return {
    ...(Object.keys(rules).length ? { rules: rules as TemplateSystemInputRequest } : {}),
    ...(technical
      ? {
          profiles: technical.profiles.map(
            ({ source: _source, pages: _pages, ...row }) => row as TemplateProfileInputRequest,
          ),
          glazing: technical.glazing.map(
            ({ source: _source, pages: _pages, ...row }) => row as TemplateGlazingInputRequest,
          ),
          hardware: (technical.hardware as Array<Record<string, unknown>>).map(
            ({ source: _source, pages: _pages, ...row }) =>
              row as unknown as TemplateHardwareInputRequest,
          ),
        }
      : {}),
  };
}

export function SeriesCatalogPage(): JSX.Element {
  const { status, me, session } = useAuthSession();
  const [params] = useSearchParams();
  const organization = me?.active_organization;
  if (status !== "ready") return <Loading label="Cargando el catálogo" />;
  if (!organization || !["OWNER", "WORKSHOP_MANAGER", "ESTIMATOR"].includes(organization.role))
    return <DeniedState reason="Tu rol no permite abrir el catálogo." />;
  if (params.has("import") && params.get("advanced") !== "1")
    return (
      <Suspense fallback={<Loading label="Cargando la revisión del manual" />}>
        <ImportReviewPage
          key={`${session?.user.id}:${organization.id}:${params.get("import")}`}
          orgId={organization.id}
          importId={params.get("import")!}
          canWrite={organization.role !== "ESTIMATOR"}
        />
      </Suspense>
    );
  if (
    params.get("advanced") !== "1" &&
    ["import", "reference", "record", "resource", "shelf", "create"].some((key) => params.has(key))
  ) {
    const legacy = new URLSearchParams(params);
    legacy.set("advanced", "1");
    return <Navigate to={`/catalogs/systems?${legacy}`} replace />;
  }
  if (params.get("advanced") === "1")
    return (
      <Suspense fallback={<Loading label="Cargando ajustes de la serie" />}>
        <AdvancedCatalog key={params.toString()} />
      </Suspense>
    );
  return (
    <SeriesCatalogHome
      key={`${session?.user.id}:${organization.id}`}
      orgId={organization.id}
      canEdit={organization.role !== "ESTIMATOR"}
      isOwner={organization.role === "OWNER"}
    />
  );
}

function SeriesCatalogHome({
  orgId,
  canEdit,
  isOwner,
}: {
  orgId: string;
  canEdit: boolean;
  isOwner: boolean;
}): JSX.Element {
  const [params, setParams] = useSearchParams();
  const queryClient = useQueryClient();
  const queryKey = ["catalog-home", orgId];
  const selected = params.get("system");
  const options = { headers: { "X-Organization-ID": orgId } };
  const [search, setSearch] = useState("");
  const [adding, setAdding] = useState<"choose" | "template" | "library" | null>(null);
  const [saving, setSaving] = useState(false);
  const [failure, setFailure] = useState("");
  const [trial, setTrial] = useState<SeriesSheet | null>(null);
  const [showExamples, setShowExamples] = useState(false);
  // A library series chosen here or in the first-use guide (`?library=`).
  const [reference, setReference] = useState<ReferenceSeries | null>(null);
  const requestedReference = params.get("library");
  const systems = useQuery({
    queryKey,
    queryFn: async ({ signal }) => {
      const response = await catalogSystemList(
        { summary: true, is_demo: false, owned_only: true },
        { ...options, signal },
      );
      if (response.status !== 200) throw new Error("catalog");
      return response.data.items;
    },
  });
  const exampleSystems = useQuery({
    queryKey: ["catalog-examples", orgId],
    enabled: showExamples,
    queryFn: async ({ signal }) => {
      const response = await catalogSystemList(
        { summary: true, is_demo: true },
        { ...options, signal },
      );
      if (response.status !== 200) throw new Error("examples");
      return response.data.items;
    },
  });
  const templates = useQuery({
    queryKey: ["catalog-family-templates", orgId],
    enabled: adding === "template" || adding === "library" || requestedReference !== null,
    queryFn: async ({ signal }) => {
      const response = await catalogFamilyTemplates({ ...options, signal });
      if (response.status !== 200) throw new Error("templates");
      return response.data.items;
    },
  });
  const library = useQuery({
    queryKey: ["catalog-references", orgId],
    enabled: adding === "library" || requestedReference !== null,
    queryFn: async ({ signal }) => {
      const response = await catalogReferenceSeries({ ...options, signal });
      if (response.status !== 200) throw new Error("library");
      return response.data;
    },
  });

  useEffect(() => {
    if (!requestedReference || !library.data) return;
    const item = library.data.series.find((entry) => entry.id === requestedReference);
    setParams({}, { replace: true });
    if (!item) return;
    setReference(item);
    setAdding("template");
  }, [library.data, requestedReference, setParams]);

  function advanced(cell?: SeriesCell) {
    setParams({
      advanced: "1",
      ...(selected ? { system: selected } : {}),
      ...(cell ? { resource: cell.resource, record: cell.row_id, field: cell.field } : {}),
    });
  }
  function changed(sheet: SeriesSheet) {
    queryClient.setQueryData<SystemResponse[]>(queryKey, (current) => [
      ...(current ?? []).filter((item) => item.id !== sheet.id),
      sheet.tabs.rules,
    ]);
  }
  async function create(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving) return;
    const form = new FormData(event.currentTarget);
    const template = templates.data?.find((item) => item.id === form.get("template"));
    if (!template) return;
    setSaving(true);
    setFailure("");
    try {
      const response = await catalogSeriesCreate(
        {
          template_id: template.id,
          template_version: template.version,
          ...referenceSeriesInput(reference),
          name: String(form.get("name") ?? "").trim(),
          code: String(form.get("code") ?? "").trim(),
          ...(String(form.get("manufacturer") ?? "").trim()
            ? { manufacturer: String(form.get("manufacturer")).trim() }
            : {}),
        },
        options,
      );
      if (response.status !== 201) throw new Error("create");
      changed(response.data);
      queryClient.setQueryData(["series-sheet", orgId, response.data.id], response.data);
      setAdding(null);
      setReference(null);
      setParams({ system: response.data.id, setup: "1" });
    } catch {
      setFailure("No se pudo agregar la serie. Revisa sus datos y vuelve a intentarlo.");
    } finally {
      setSaving(false);
    }
  }

  if (selected)
    return (
      <>
        <SeriesSheetView
          key={selected}
          orgId={orgId}
          systemId={selected}
          canEdit={canEdit}
          onBack={() => setParams({})}
          onChanged={changed}
          onAdvanced={advanced}
          onTrial={setTrial}
          onSetup={canEdit ? () => setParams({ system: selected, setup: "1" }) : undefined}
        />
        {params.get("setup") === "1" && canEdit && (
          <Suspense fallback={<Loading label="Cargando el alta" />}>
            <SetupWizard
              key={`${orgId}:${selected}`}
              orgId={orgId}
              systemId={selected}
              isOwner={isOwner}
              onClose={() => setParams({ system: selected })}
            />
          </Suspense>
        )}
        {trial && (
          <SeriesTrialDialog
            orgId={orgId}
            sheet={trial}
            onClose={() => setTrial(null)}
            onComplete={() => {
              setTrial(null);
              advanced();
            }}
          />
        )}
      </>
    );

  const all = systems.data ?? [];
  const real = all.filter((system) => !system.is_demo);
  const term = search.trim().toLocaleLowerCase("es-CL");
  const matches = (system: SystemResponse) =>
    `${system.manufacturer ?? ""} ${system.name} ${system.code}`
      .toLocaleLowerCase("es-CL")
      .includes(term);
  const groups = catalogGroups(real.filter(matches));
  const examples = (exampleSystems.data ?? []).filter(
    (system) => system.is_demo && matches(system),
  );
  const count = catalogGroups(real).reduce((total, brand) => total + brand.series.length, 0);
  return (
    <section className="series-catalog" aria-label="Catálogo">
      <header className="series-catalog__header">
        <div>
          <h1>Catálogo</h1>
          <p>
            {count} {count === 1 ? "serie de tu taller" : "series de tu taller"}
          </p>
        </div>
        {canEdit && (
          <Button
            variant="primary"
            onClick={() => {
              setFailure("");
              setAdding("choose");
            }}
          >
            Agregar serie
          </Button>
        )}
      </header>
      <label className="ui-search-pill series-catalog__search">
        <Icon name="search" size={16} />
        <input
          type="search"
          aria-label="Buscar fabricante o serie"
          placeholder="Buscar fabricante o serie"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
      </label>
      {systems.isPending ? (
        <Loading label="Cargando tus series" />
      ) : systems.isError ? (
        <div>
          <p role="alert">No se pudo cargar el catálogo.</p>
          <Button onClick={() => void systems.refetch()}>Volver a intentar</Button>
        </div>
      ) : groups.length ? (
        groups.map((brand) => (
          <section className="series-catalog__brand" key={brand.name} aria-label={brand.name}>
            <header>
              <span className="series-sheet__monogram" aria-hidden="true">
                {brand.name.slice(0, 2).toLocaleUpperCase("es-CL")}
              </span>
              <h2>{brand.name}</h2>
            </header>
            <ul>
              {brand.series.map((versions) => {
                const current = versions.find((item) => item.is_active) ?? versions[0]!;
                return (
                  <li key={current.code}>
                    <button type="button" onClick={() => setParams({ system: current.id })}>
                      <span>
                        <strong>{current.name}</strong>
                        <small>
                          {current.code} · {current.material === "PVC" ? "PVC" : "Aluminio"}
                        </small>
                      </span>
                      <span className="series-catalog__state">
                        {current.usage ? usageLabel(current.usage) : "Completar serie"}
                      </span>
                      <span aria-hidden="true">›</span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </section>
        ))
      ) : (
        <div className="series-catalog__empty">
          <h2>{term ? "Ninguna serie coincide" : "Agrega la primera serie de tu taller"}</h2>
          <p>
            {term
              ? "Prueba otro nombre o código."
              : "Parte de la biblioteca, usa una plantilla o ingresa los datos de tu manual."}
          </p>
        </div>
      )}
      <details
        className="series-catalog__examples"
        onToggle={(event) => setShowExamples(event.currentTarget.open)}
      >
        <summary>Ejemplos{exampleSystems.data ? ` · ${examples.length}` : ""}</summary>
        <p>Series sintéticas para aprender a usar el catálogo.</p>
        {showExamples && exampleSystems.isPending ? (
          <Loading label="Cargando ejemplos" />
        ) : exampleSystems.isError ? (
          <div>
            <p role="alert">No se pudieron cargar los ejemplos.</p>
            <Button onClick={() => void exampleSystems.refetch()}>Volver a intentar</Button>
          </div>
        ) : (
          <>
            <ul>
              {examples.map((system) => (
                <li key={system.id}>
                  <Button variant="ghost" onClick={() => setParams({ system: system.id })}>
                    {system.name}
                  </Button>
                </li>
              ))}
            </ul>
            {showExamples && !examples.length && <p>Ningún ejemplo coincide con tu búsqueda.</p>}
          </>
        )}
      </details>
      <Link to="/catalogs/systems?advanced=1">Más ajustes del catálogo</Link>
      {adding && (
        <Dialog
          title={
            adding === "choose"
              ? "Agregar serie"
              : adding === "library"
                ? "Desde la biblioteca"
                : "Desde una plantilla"
          }
          onClose={() => {
            if (saving) return;
            setAdding(null);
            setReference(null);
          }}
        >
          {adding === "choose" ? (
            <div className="series-catalog__choices">
              <Button onClick={() => setAdding("library")}>Desde la biblioteca</Button>
              <Button onClick={() => setAdding("template")}>Desde una plantilla</Button>
              <Button onClick={() => setParams({ advanced: "1", create: "systems" })}>
                Desde cero
              </Button>
            </div>
          ) : adding === "library" ? (
            library.isPending ? (
              <Loading label="Cargando la biblioteca" />
            ) : library.isError ? (
              <p role="alert">No se pudo cargar la biblioteca. Cierra y vuelve a intentarlo.</p>
            ) : (
              <ul className="series-catalog__library">
                {library.data?.series.map((item) => (
                  <li key={item.id}>
                    <Button
                      onClick={() => {
                        // A series with a known family starts the guided setup;
                        // the rest open the full reference to resolve identity.
                        if (templates.data && templateForReference(item, templates.data)) {
                          setReference(item);
                          setAdding("template");
                        } else setParams({ advanced: "1", reference: item.id });
                      }}
                    >
                      {item.manufacturer} · {item.series_name}
                    </Button>
                  </li>
                ))}
              </ul>
            )
          ) : templates.isPending ? (
            <Loading label="Cargando las plantillas" />
          ) : templates.isError ? (
            <p role="alert">No se pudieron cargar las plantillas.</p>
          ) : (
            <ValidatedForm
              className="series-catalog__create"
              onSubmit={(event) => void create(event)}
            >
              <label>
                Fabricante
                <input
                  name="manufacturer"
                  maxLength={255}
                  defaultValue={reference?.seed.manufacturer ?? ""}
                />
              </label>
              <label>
                Nombre de la serie
                <input
                  name="name"
                  required
                  maxLength={150}
                  defaultValue={reference?.seed.name ?? ""}
                />
              </label>
              <label>
                Código
                <input
                  name="code"
                  required
                  maxLength={50}
                  defaultValue={reference?.seed.code ?? ""}
                />
              </label>
              <label>
                Plantilla
                <select
                  name="template"
                  required
                  defaultValue={
                    reference && templates.data
                      ? templateForReference(reference, templates.data)?.id
                      : undefined
                  }
                >
                  {templates.data?.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              {reference ? (
                <p>
                  {reference.technical
                    ? `Trae la identidad de ${reference.series_name} y su hoja de corte citada: ${reference.technical.profiles.length} perfiles, junquillo y reglas. ${reference.technical.note} Los precios son los de tu proveedor.`
                    : `La biblioteca aporta solo la identidad de ${reference.series_name}. Los perfiles, largos y precios salen del manual de tu fabricante o de tu planilla.`}
                </p>
              ) : null}
              <p>
                Los valores de la plantilla quedan como sugeridos. Después agrega tus perfiles y
                precios.
              </p>
              {failure && <p role="alert">{failure}</p>}
              <Button variant="primary" type="submit" loading={saving}>
                Crear serie
              </Button>
            </ValidatedForm>
          )}
        </Dialog>
      )}
    </section>
  );
}
