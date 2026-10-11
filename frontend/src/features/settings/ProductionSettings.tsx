import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  productionWorkCenters,
  productionWorkCentersCreate,
  catalogProcessProfileList,
} from "../../api/generated/dekopen";
import { WorkCenterRequestKindEnum } from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { Button, ErrorState, LoadingState, ValidatedForm, useConfirm } from "../../ui";
import { centerKindLabel } from "../production/labels";
import { actionErrorDetail } from "../errors";

export function ProductionSettings({
  orgId,
  canEdit,
}: {
  orgId: string;
  canEdit: boolean;
}): JSX.Element {
  const confirm = useConfirm(),
    options = { headers: { "X-Organization-ID": orgId } };
  const [code, setCode] = useState(""),
    [name, setName] = useState(""),
    [kind, setKind] = useState<WorkCenterRequestKindEnum>("CUT"),
    [order, setOrder] = useState(0),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  const query = useQuery({
    queryKey: ["settings-stations", orgId],
    queryFn: async ({ signal }) => {
      const [centers, profiles] = await Promise.all([
        productionWorkCenters({ ...options, signal }),
        catalogProcessProfileList({ ...options, signal }),
      ]);
      if (centers.status !== 200) throw new ApiError(centers.status, centers.data);
      if (profiles.status !== 200) throw new ApiError(profiles.status, profiles.data);
      return { centers: centers.data.centers, profiles: profiles.data.items };
    },
  });
  if (query.isPending) return <LoadingState label="Consultando estaciones y rutas" />;
  if (query.isError)
    return (
      <ErrorState
        body="No pudimos consultar estaciones y rutas."
        onRetry={() => void query.refetch()}
      />
    );
  return (
    <section className="settings-card">
      <h3>Estaciones y ruta de fabricación</h3>
      <p>
        Las estaciones activas aparecen en el puesto del operario. La ruta se declara por serie en
        Catálogo y se sella en cada OT; no se altera al cambiar estos ajustes.
      </p>
      <ul>
        {query.data.centers.map((center) => (
          <li key={center.id}>
            {center.name} · {centerKindLabel(center.kind)} · {center.active ? "Activa" : "Inactiva"}
            {canEdit && (
              <Button
                onClick={() => {
                  setCode(center.code);
                  setName(center.name);
                  setKind(center.kind as WorkCenterRequestKindEnum);
                  setOrder(center.display_order);
                }}
              >
                Editar estación
              </Button>
            )}
          </li>
        ))}
      </ul>
      {!query.data.centers.length && (
        <p>Sin estaciones. Declara los puestos que existen en tu taller.</p>
      )}
      {canEdit && (
        <ValidatedForm
          className="settings-station-form"
          onSubmit={(event) => {
            event.preventDefault();
            void (async () => {
              if (
                busy ||
                !(await confirm({
                  title: "Guardar estación",
                  body: `${name} estará disponible para ${centerKindLabel(kind)}. Las OT emitidas conservan su ruta.`,
                }))
              )
                return;
              setBusy(true);
              setMessage("");
              try {
                await productionWorkCentersCreate(
                  { code, name, kind, display_order: order },
                  options,
                );
                await query.refetch();
                setCode("");
                setName("");
                setMessage("Estación guardada.");
              } catch (error) {
                setMessage(
                  actionErrorDetail(
                    error,
                    "No se pudo guardar la estación. Revisa los campos y la conexión.",
                  ),
                );
              } finally {
                setBusy(false);
              }
            })();
          }}
        >
          <label>
            Código de estación
            <input
              required
              maxLength={50}
              value={code}
              onChange={(event) => setCode(event.target.value)}
            />
          </label>
          <label>
            Nombre
            <input
              required
              maxLength={200}
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </label>
          <label>
            Proceso
            <select
              value={kind}
              onChange={(event) => setKind(event.target.value as WorkCenterRequestKindEnum)}
            >
              {Object.values(WorkCenterRequestKindEnum).map((kind) => (
                <option key={kind} value={kind}>
                  {centerKindLabel(kind)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Orden en el tablero
            <input
              type="number"
              required
              step={1}
              value={order}
              onChange={(event) => setOrder(event.target.valueAsNumber)}
            />
          </label>
          <Button type="submit" disabled={busy}>
            Guardar estación
          </Button>
        </ValidatedForm>
      )}
      {message && <p role="status">{message}</p>}
      <h3>Rutas disponibles para las series</h3>
      <ul>
        {query.data.profiles.map((profile) => (
          <li key={profile.id}>
            {profile.label} · versión {profile.version}
          </li>
        ))}
      </ul>
      <Link className="ui-button" to="/catalogs/systems">
        Configurar ruta de una serie
      </Link>
    </section>
  );
}
