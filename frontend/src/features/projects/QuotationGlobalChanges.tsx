import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  engineSystems,
  projectDesignOptions,
  projectOperationsPreview,
  projectOperationsApply,
  projectOperationsUndo,
} from "../../api/generated/dekopen";
import type {
  DesignOperationRequest,
  ProjectOpsPreviewResponse,
  ProjectResponse,
} from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { actionErrorDetail } from "../errors";
import { SimulationPreview } from "../assistant/SimulationPreview";
import { DimLoader } from "../../ui/Signature";
import { formatMoney } from "../money";
import { domainLabel } from "../../i18n/domainLabels";

type Kind = "glass" | "finish" | "system" | "handle";
type PriceSimulation = {
  position_id: string;
  price?: {
    net?: string | null;
    currency?: string;
    delta_net?: string | null;
    reason?: string | null;
  };
};

/** UI and AI submit the same registered apply_to_positions operation. */
export function QuotationGlobalChanges({
  project,
  orgId,
  canWrite,
  onChanged,
}: {
  project: ProjectResponse;
  orgId: string;
  canWrite: boolean;
  onChanged: () => Promise<unknown>;
}): JSX.Element {
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState<Kind>("glass");
  const [selection, setSelection] = useState<string[]>([]);
  const [all, setAll] = useState(true);
  const [systemId, setSystemId] = useState(project.positions?.[0]?.design.system_id ?? "");
  const [value, setValue] = useState("");
  const [preview, setPreview] = useState<ProjectOpsPreviewResponse | null>(null);
  const [key, setKey] = useState("");
  const [operationId, setOperationId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const options = { headers: { "X-Organization-ID": orgId } };
  const systems = useQuery({
    queryKey: ["project-systems", orgId],
    enabled: open,
    queryFn: async () => {
      const r = await engineSystems(options);
      if (r.status !== 200) throw new ApiError(r.status, r.data);
      return r.data.systems;
    },
  });
  const catalog = useQuery({
    queryKey: ["project-design-options", orgId, systemId],
    enabled: open && Boolean(systemId),
    queryFn: async () => {
      const r = await projectDesignOptions(systemId, options);
      if (r.status !== 200) throw new ApiError(r.status, r.data);
      return r.data;
    },
  });
  const revisionLocked = project.status !== "DRAFT";
  const editable = canWrite && !revisionLocked && !project.current_pricing_operation_id;
  function clear(): void {
    setPreview(null);
    setError("");
    setNotice("");
  }
  function intents(): DesignOperationRequest[] {
    let op: DesignOperationRequest;
    if (kind === "glass") op = { op: "set_glass", module: "*", sku: value };
    else if (kind === "system") op = { op: "set_system", system_id: value };
    else if (kind === "handle")
      op = {
        op: "set_handle_height",
        module: "*",
        bay: "*",
        height_mm: value.replace(",", "."),
        reference: "LEAF_BOTTOM",
        all_handles: true,
      };
    else {
      const combination = catalog.data?.finish_authority?.combinations.find(
        (item) => item.code === value,
      );
      op = {
        op: "set_finish",
        interior: combination?.interior ?? value,
        exterior: combination?.exterior ?? value,
      };
    }
    return [
      {
        op: "apply_to_positions",
        filter: all ? {} : { position_ids: selection },
        ops: [{ ...op }],
      },
    ];
  }
  async function simulate(): Promise<void> {
    setBusy(true);
    clear();
    setKey(crypto.randomUUID());
    try {
      const r = await projectOperationsPreview(project.id, { ops: intents() }, options);
      if (r.status !== 200) throw new ApiError(r.status, r.data);
      setPreview(r.data);
    } catch (error) {
      setError(
        actionErrorDetail(
          error,
          "El motor no pudo revisar este cambio. Revisa las posiciones y vuelve a simular.",
        ),
      );
    } finally {
      setBusy(false);
    }
  }
  async function apply(): Promise<void> {
    if (!preview || busy) return;
    setBusy(true);
    setError("");
    try {
      const r = await projectOperationsApply(
        project.id,
        { ops: intents(), before_sig: preview.before_sig, operation_key: key },
        options,
      );
      if (r.status !== 200) throw new ApiError(r.status, r.data);
      setOperationId(r.data.operation_id);
      setPreview(null);
      setNotice(
        "Cambios aplicados. Puedes deshacerlos mientras no haya una edición posterior. Revisa y aplica el precio antes de emitir.",
      );
      await onChanged();
    } catch (error) {
      setError(
        actionErrorDetail(
          error,
          "No se pudo aplicar. Revisa la conexión y vuelve a intentar la misma operación.",
        ),
      );
    } finally {
      setBusy(false);
    }
  }
  async function undo(): Promise<void> {
    setBusy(true);
    setError("");
    try {
      const r = await projectOperationsUndo(project.id, operationId, options);
      if (r.status !== 200) throw new ApiError(r.status, r.data);
      setOperationId("");
      clear();
      setNotice("Cambio global deshecho; se restauró la preparación anterior.");
      await onChanged();
    } catch (error) {
      setError(
        actionErrorDetail(
          error,
          "No se pudo deshacer. Revisa si hay cambios posteriores en la obra.",
        ),
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <details
      className="quotation-global"
      open={open}
      onToggle={(event) => setOpen(event.currentTarget.open)}
    >
      <summary>Cambios globales de las posiciones</summary>
      {!canWrite ? (
        <p>
          Solo un estimador o propietario puede cambiar las posiciones. Solicita acceso al
          propietario.
        </p>
      ) : revisionLocked ? (
        <p>
          La revisión está sellada. Abre una revisión sucesora para cambiar vidrio, acabado, serie o
          manilla.
        </p>
      ) : project.current_pricing_operation_id ? (
        <p>
          El precio está aplicado. Libera la edición de precios antes de preparar un cambio global.
        </p>
      ) : (project.positions?.length ?? 0) === 0 ? (
        <p>
          Agrega la primera posición para preparar un cambio global.{" "}
          <Link to={`/projects/${project.id}/positions/new`}>Agregar posición</Link>
        </p>
      ) : (
        <>
          <fieldset disabled={busy || !editable}>
            <legend>Destinos y cambio</legend>
            <label>
              <input
                type="checkbox"
                checked={all}
                onChange={(event) => {
                  setAll(event.target.checked);
                  clear();
                }}
              />
              Todas las posiciones
            </label>
            {!all ? (
              <div className="quotation-global-selection">
                {(project.positions ?? []).map((position) => (
                  <label key={position.id}>
                    <input
                      type="checkbox"
                      checked={selection.includes(position.id)}
                      onChange={(event) => {
                        setSelection(
                          event.target.checked
                            ? [...selection, position.id]
                            : selection.filter((id) => id !== position.id),
                        );
                        clear();
                      }}
                    />
                    Posición {position.position_index} · {position.location_tag || "Sin ubicación"}
                  </label>
                ))}
              </div>
            ) : null}
            <label>
              Cambiar
              <select
                value={kind}
                onChange={(event) => {
                  setKind(event.target.value as Kind);
                  setValue("");
                  clear();
                }}
              >
                <option value="glass">Vidrio</option>
                <option value="finish">Color o acabado</option>
                <option value="system">Serie</option>
                <option value="handle">Altura de manilla</option>
              </select>
            </label>
            {kind !== "system" && kind !== "handle" ? (
              <label>
                Catálogo de referencia
                <select
                  value={systemId}
                  onChange={(event) => {
                    setSystemId(event.target.value);
                    setValue("");
                    clear();
                  }}
                >
                  <option value="">Elige una serie</option>
                  {systems.data?.map((system) => (
                    <option key={system.id} value={system.id}>
                      {system.name}
                      {system.is_demo ? " · DEMO" : ""}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            {systems.isPending || (kind !== "system" && kind !== "handle" && catalog.isPending) ? (
              <p>
                <DimLoader label="Cargando el catálogo" /> Cargando el catálogo…
              </p>
            ) : systems.isError || catalog.isError ? (
              <div>
                <p role="alert">
                  No se pudo cargar el catálogo. Revisa la conexión y vuelve a intentar.
                </p>
                <button
                  type="button"
                  onClick={() => {
                    void systems.refetch();
                    void catalog.refetch();
                  }}
                >
                  Reintentar catálogo
                </button>
              </div>
            ) : null}
            {kind === "handle" ? (
              <label>
                Altura desde el borde inferior de la hoja (mm)
                <input
                  inputMode="decimal"
                  value={value}
                  onChange={(event) => {
                    setValue(event.target.value);
                    clear();
                  }}
                />
              </label>
            ) : (
              <label>
                {kind === "glass"
                  ? "Vidrio del catálogo"
                  : kind === "finish"
                    ? "Caras y acabado"
                    : "Nueva serie"}
                <select
                  value={value}
                  onChange={(event) => {
                    setValue(event.target.value);
                    clear();
                  }}
                >
                  <option value="">Elige una opción</option>
                  {kind === "glass"
                    ? catalog.data?.glass_specs
                        .filter((glass) => glass.compatible !== false)
                        .map((glass) => (
                          <option key={glass.sku} value={glass.sku}>
                            {glass.spec || "Composición sin dato"} · {glass.sku}
                          </option>
                        ))
                    : kind === "system"
                      ? systems.data?.map((system) => (
                          <option key={system.id} value={system.id}>
                            {system.name}
                            {system.is_demo ? " · DEMO" : ""}
                          </option>
                        ))
                      : catalog.data?.finish_authority
                        ? catalog.data.finish_authority.combinations.map((combination) => (
                            <option key={combination.code} value={combination.code}>
                              Interior{" "}
                              {catalog.data?.finish_authority?.colors.find(
                                (color) => color.code === combination.interior,
                              )?.name ?? domainLabel(combination.interior)}{" "}
                              · exterior{" "}
                              {catalog.data?.finish_authority?.colors.find(
                                (color) => color.code === combination.exterior,
                              )?.name ?? domainLabel(combination.exterior)}
                              {combination.synthetic ? " · DEMO" : ""}
                            </option>
                          ))
                        : catalog.data?.colors.map((color) => (
                            <option key={color} value={color}>
                              {domainLabel(color)}
                            </option>
                          ))}
                </select>
              </label>
            )}
            <p>
              El motor comprueba cada serie y su límite de fabricación. Los paños sin manilla se
              omiten al cambiar su altura.
            </p>
            <button
              type="button"
              disabled={!value || (!all && !selection.length) || busy}
              onClick={() => void simulate()}
            >
              Ver impacto del cambio
            </button>
          </fieldset>
        </>
      )}
      {busy ? (
        <p>
          <DimLoader label="Revisando cambios globales" /> Revisando el cambio…
        </p>
      ) : null}
      {error ? <p role="alert">{error}</p> : null}
      {notice ? <p role="status">{notice}</p> : null}
      {preview ? (
        <section className="quotation-global-preview">
          <h4>Impacto antes de aplicar</h4>
          {preview.diff.length === 0 ? (
            <p>Sin cambios: las posiciones ya tienen el valor elegido o no poseen manilla.</p>
          ) : (
            <>
              <p>
                Se modificarán {preview.diff.length} posiciones. Precio indicativo por posición,
                incluida su cantidad; la emisión usará el precio aplicado.
              </p>
              {preview.simulations.map((raw, index) => {
                const simulation = raw as PriceSimulation;
                const position = project.positions?.find((p) => p.id === simulation.position_id);
                return (
                  <details key={simulation.position_id}>
                    <summary>
                      Posición {position?.position_index ?? index + 1} ·{" "}
                      {position?.location_tag || "Sin ubicación"} · Δ neto{" "}
                      {simulation.price?.delta_net != null
                        ? formatMoney(
                            simulation.price.delta_net,
                            simulation.price.currency ?? project.currency,
                          )
                        : "Sin dato"}
                    </summary>
                    <SimulationPreview simulation={raw} organizationId={orgId} />
                  </details>
                );
              })}
              <button
                type="button"
                className="primary-action"
                disabled={busy || !editable}
                onClick={() => void apply()}
              >
                Aplicar cambio a {preview.diff.length} posiciones
              </button>
            </>
          )}
        </section>
      ) : null}
      {operationId ? (
        <button type="button" disabled={busy || !editable} onClick={() => void undo()}>
          Deshacer cambio global
        </button>
      ) : null}
    </details>
  );
}
