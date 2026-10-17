import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { engineSystems, projectDesignOptions } from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import type { DesignOperationRequest } from "../../api/generated/models";
import { domainLabel } from "../../i18n/domainLabels";
import { parseDecimalInput } from "../../format";
import { DimLoader } from "../../ui";
import { Icon } from "../../ui/Icon";
import { EditorFlyout } from "../canvas/EditorFlyout";
import { StarterGallery, StarterThumb } from "../canvas/StarterGallery";
import { starterSize, starterTitle, type StarterDefinition } from "../canvas/designLibrary";
import { resolveMembers } from "../canvas/members";
import { sourcedStarter } from "../canvas/starterAuthority";
import "../canvas/EditorLayout.css";

export function ProjectPositionLibrary({
  orgId,
  initialSystem,
  initialGlass,
  initialColor,
  busy,
  error,
  onClose,
  onPropose,
}: {
  orgId: string;
  initialSystem?: string;
  initialGlass?: string;
  initialColor?: string;
  busy: boolean;
  error?: string;
  onClose(): void;
  onPropose(ops: DesignOperationRequest[], title: string): Promise<boolean>;
}): JSX.Element {
  const [systemId, setSystemId] = useState(initialSystem ?? "");
  const [glass, setGlass] = useState(initialGlass ?? "");
  const [color, setColor] = useState(initialColor ?? "");
  const [location, setLocation] = useState("");
  const [width, setWidth] = useState("");
  const [height, setHeight] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [definition, setDefinition] = useState<StarterDefinition | null>(null);
  const widthInput = useRef<HTMLInputElement>(null);
  const selectionPreview = useMemo(() => {
    if (!definition) return null;
    const size = starterSize(definition);
    return definition.build(size.widthMm, size.heightMm);
  }, [definition]);
  useEffect(() => {
    if (!definition) return;
    widthInput.current?.focus({ preventScroll: true });
    widthInput.current?.closest("fieldset")?.scrollTo({ top: 0 });
  }, [definition]);
  const options = { headers: { "X-Organization-ID": orgId } };
  const systems = useQuery({
    queryKey: ["project-systems", orgId],
    queryFn: async () => {
      const response = await engineSystems(options);
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data.systems;
    },
  });
  const catalog = useQuery({
    queryKey: ["design-options", orgId, systemId],
    enabled: Boolean(systemId),
    queryFn: async () => {
      const response = await projectDesignOptions(systemId, options);
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
  });
  useEffect(() => {
    if (systemId || !systems.data) return;
    let previous = "";
    try {
      previous = localStorage.getItem(`dekopen:last-system:${orgId}`) ?? "";
    } catch {
      /* Storage is optional. */
    }
    if (previous && systems.data.some((system) => system.id === previous)) setSystemId(previous);
    else if (systems.data.length === 1) setSystemId(systems.data[0]!.id);
  }, [systemId, systems.data, orgId]);
  useEffect(() => {
    if (!catalog.data) return;
    const compatible = catalog.data.glass_specs.filter((item) => item.compatible !== false);
    setGlass((current) =>
      compatible.some((item) => item.sku === current) ? current : (compatible[0]?.sku ?? ""),
    );
    setColor((current) =>
      catalog.data.colors.includes(current) ? current : (catalog.data.colors[0] ?? ""),
    );
  }, [catalog.data]);
  const w = parseDecimalInput(width, 2),
    h = parseDecimalInput(height, 2);
  async function propose(): Promise<void> {
    if (!definition || !w || !h || !catalog.data) return;
    const product = sourcedStarter(definition.build(Number(w), Number(h)), catalog.data);
    const prepared = await onPropose(
      [
        {
          op: "add_design_position",
          system_id: systemId,
          product: { ...product },
          glass_sku: glass,
          color,
          location,
          quantity,
        },
      ],
      "Agregar ventana",
    );
    if (prepared) {
      try {
        localStorage.setItem(`dekopen:last-system:${orgId}`, systemId);
      } catch {
        /* Storage is optional. */
      }
      onClose();
    }
  }
  return (
    <EditorFlyout title="Agregar ventana o puerta" onClose={onClose} className="project-library">
      <fieldset disabled={busy} className="project-library-fields">
        <label>
          Serie
          <select
            aria-label="Serie"
            value={systemId}
            onChange={(event) => {
              setSystemId(event.target.value);
              setDefinition(null);
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
        {systems.isError || catalog.isError ? (
          <p role="alert">
            No se pudo cargar la biblioteca.{" "}
            <button
              type="button"
              onClick={() => {
                void systems.refetch();
                void catalog.refetch();
              }}
            >
              Reintentar
            </button>
          </p>
        ) : null}
        {systems.isPending || (Boolean(systemId) && catalog.isPending) ? (
          <DimLoader label="Cargando biblioteca compatible" />
        ) : null}
        {catalog.data && (
          <>
            {error && <p role="alert">{error}</p>}
            {!definition && (
              <StarterGallery
                options={catalog.data}
                allowedOpenings={catalog.data.compatible_openings}
                members={resolveMembers(catalog.data)}
                disabled={busy}
                onPick={(choice) => {
                  setDefinition(choice);
                  const nominal = starterSize(choice);
                  setWidth(String(nominal.widthMm));
                  setHeight(String(nominal.heightMm));
                }}
              />
            )}
            {definition && (
              <div className="project-library-choice">
                <header>
                  <Icon name="check" size={18} />
                  <strong>{starterTitle(definition)}</strong>
                  <span>Medidas de fabricación en mm</span>
                </header>
                <div className="project-library-selected">
                  {selectionPreview && (
                    <div className="project-library-preview">
                      <StarterThumb
                        product={selectionPreview}
                        members={resolveMembers(catalog.data)}
                        leaves={definition.previewLeaves}
                      />
                    </div>
                  )}
                  <button
                    type="button"
                    className="ui-button ui-button--small"
                    onClick={() => setDefinition(null)}
                  >
                    Cambiar diseño
                  </button>
                </div>
                <div className="project-library-measures">
                  <label>
                    Ancho
                    <input
                      ref={widthInput}
                      inputMode="decimal"
                      value={width}
                      onChange={(event) => setWidth(event.target.value)}
                    />
                  </label>
                  <label>
                    Alto
                    <input
                      inputMode="decimal"
                      value={height}
                      onChange={(event) => setHeight(event.target.value)}
                    />
                  </label>
                  <label>
                    Cantidad
                    <input
                      type="number"
                      min={1}
                      max={9999}
                      value={quantity}
                      onChange={(event) =>
                        setQuantity(Math.max(1, Math.min(9999, Number(event.target.value) || 1)))
                      }
                    />
                  </label>
                </div>
                <label>
                  Ubicación <span className="project-library-optional">opcional</span>
                  <input
                    placeholder="Por ejemplo: cocina"
                    maxLength={120}
                    value={location}
                    onChange={(event) => setLocation(event.target.value)}
                  />
                </label>
                <details className="project-library-materials" open={!glass || !color || undefined}>
                  <summary>
                    Vidrio y acabado{" "}
                    <span>
                      {!glass || !color
                        ? "Completa los materiales para continuar"
                        : "Se conservan los compatibles de la obra"}
                    </span>
                  </summary>
                  <label>
                    Vidrio
                    <select
                      aria-label="Vidrio"
                      value={glass}
                      onChange={(event) => setGlass(event.target.value)}
                    >
                      <option value="">Elige un vidrio</option>
                      {catalog.data.glass_specs
                        .filter((item) => item.compatible !== false)
                        .map((item) => (
                          <option key={item.sku} value={item.sku}>
                            {item.spec || item.sku}
                          </option>
                        ))}
                    </select>
                  </label>
                  <label>
                    Color o acabado
                    <select
                      aria-label="Color o acabado"
                      value={color}
                      onChange={(event) => setColor(event.target.value)}
                    >
                      <option value="">Elige un acabado</option>
                      {catalog.data.colors.map((item) => (
                        <option key={item} value={item}>
                          {domainLabel(item)}
                        </option>
                      ))}
                    </select>
                  </label>
                </details>
                {!glass || !color ? (
                  <p role="status">
                    {!glass && !color
                      ? "Esta serie necesita un vidrio y un acabado compatibles."
                      : !glass
                        ? "Esta serie necesita un vidrio compatible."
                        : "Esta serie necesita un acabado compatible."}{" "}
                    Si no aparecen opciones, completa la serie en Catálogo.
                  </p>
                ) : null}
              </div>
            )}
          </>
        )}
      </fieldset>
      {definition && catalog.data ? (
        <footer className="project-library-actions">
          <button
            className="ui-button ui-button--primary"
            type="button"
            disabled={!w || !h || !glass || !color || busy}
            onClick={() => void propose()}
          >
            <Icon name="plus" size={17} />
            {busy ? "Preparando ventana…" : "Agregar a la obra"}
          </button>
        </footer>
      ) : null}
    </EditorFlyout>
  );
}
