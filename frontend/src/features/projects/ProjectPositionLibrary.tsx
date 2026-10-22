import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { engineSystems, projectDesignOptions } from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import type { DesignOperationRequest } from "../../api/generated/models";
import { domainLabel } from "../../i18n/domainLabels";
import { parseDecimalInput } from "../../format";
import { Loading } from "../../ui";
import { EditorFlyout } from "../canvas/EditorFlyout";
import { StarterGallery } from "../canvas/StarterGallery";
import { starterNominalSize, type StarterDefinition } from "../canvas/designLibrary";
import { resolveMembers } from "../canvas/members";
import { sourcedStarter } from "../canvas/starterAuthority";
import "../canvas/EditorLayout.css";

export function ProjectPositionLibrary({
  orgId,
  initialSystem,
  busy,
  error,
  onClose,
  onPropose,
}: {
  orgId: string;
  initialSystem?: string;
  busy: boolean;
  error?: string;
  onClose(): void;
  onPropose(ops: DesignOperationRequest[], title: string): Promise<boolean>;
}): JSX.Element {
  const [systemId, setSystemId] = useState(initialSystem ?? "");
  const [glass, setGlass] = useState("");
  const [color, setColor] = useState("");
  const [location, setLocation] = useState("");
  const [width, setWidth] = useState("");
  const [height, setHeight] = useState("");
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
    queryKey: ["project-design-options", orgId, systemId],
    enabled: Boolean(systemId),
    queryFn: async () => {
      const response = await projectDesignOptions(systemId, options);
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
  });
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
          quantity: 1,
        },
      ],
      "Agregar posición desde la biblioteca",
    );
    if (prepared) onClose();
  }
  return (
    <EditorFlyout title="Biblioteca de posiciones" onClose={onClose} className="project-library">
      <fieldset disabled={busy} className="project-library-fields">
        <label>
          Serie
          <select
            aria-label="Serie"
            value={systemId}
            onChange={(event) => {
              setSystemId(event.target.value);
              setGlass("");
              setColor("");
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
          <Loading label="Cargando biblioteca compatible" />
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
                <p>
                  La receta propone estas medidas. Revísalas antes de agregar; el motor comprobará
                  la serie y sus límites.
                </p>
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
                          {value.spec || "Composición por completar"} · {value.sku}
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
                  Revisar posición con el motor
                </button>
              </>
            )}
          </>
        )}
      </fieldset>
    </EditorFlyout>
  );
}
