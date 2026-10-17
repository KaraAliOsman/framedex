import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { engineSystems, projectDesignOptions } from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import type { DesignOperationRequest } from "../../api/generated/models";
import { domainLabel } from "../../i18n/domainLabels";
import { parseDecimalInput } from "../../format";
import { DimLoader } from "../../ui";
import { EditorFlyout } from "../canvas/EditorFlyout";
import { StarterGallery } from "../canvas/StarterGallery";
import { starterNominalSize, type StarterDefinition } from "../canvas/designLibrary";
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
            <StarterGallery
              options={catalog.data}
              allowedOpenings={catalog.data.compatible_openings}
              members={resolveMembers(catalog.data)}
              disabled={busy}
              onPick={(choice) => {
                setDefinition(choice);
                const nominal = choice.nominal ?? starterNominalSize(choice.key);
                setWidth(String(nominal.widthMm));
                setHeight(String(nominal.heightMm));
              }}
            />
            {definition && (
              <>
                <p>Ajusta las medidas. Vidrio y acabado se heredan cuando son compatibles.</p>
                <label>
                  Ancho de fabricación (mm)
                  <input
                    inputMode="decimal"
                    value={width}
                    onChange={(event) => setWidth(event.target.value)}
                  />
                </label>
                <label>
                  Alto de fabricación (mm)
                  <input
                    inputMode="decimal"
                    value={height}
                    onChange={(event) => setHeight(event.target.value)}
                  />
                </label>
                <label>
                  Vidrio
                  <select
                    aria-label="Vidrio"
                    value={glass}
                    onChange={(event) => setGlass(event.target.value)}
                  >
                    <option value="">Elige un vidrio</option>
                    {catalog.data.glass_specs
                      .filter((value) => value.compatible !== false)
                      .map((value) => (
                        <option key={value.sku} value={value.sku}>
                          {value.spec || "Composición sin dato"} · {value.sku}
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
                    {catalog.data.colors.map((value) => (
                      <option key={value} value={value}>
                        {domainLabel(value)}
                      </option>
                    ))}
                  </select>
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
                <label>
                  Ubicación
                  <input
                    maxLength={120}
                    value={location}
                    onChange={(event) => setLocation(event.target.value)}
                  />
                </label>
                <button
                  type="button"
                  disabled={!w || !h || !glass || !color || busy}
                  onClick={() => void propose()}
                >
                  Agregar a la obra
                </button>
              </>
            )}
          </>
        )}
      </fieldset>
    </EditorFlyout>
  );
}
