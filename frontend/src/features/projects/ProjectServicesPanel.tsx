import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { projectExtraServices, projectExtraServicesSave } from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import { actionErrorDetail } from "../errors";
import { formatMoney } from "../../format";
import {
  definitions,
  extraLines,
  extraBasisLabels,
  extraUnit,
  extraQuantity,
  extraTariff,
  hasRounding,
  type ExtraSelection,
} from "./extraModel";
import "./extras.css";

export function ProjectServicesPanel({
  projectId,
  orgId,
  canWrite,
}: {
  projectId: string;
  orgId: string;
  canWrite: boolean;
}): JSX.Element {
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ["project-services", orgId, projectId],
    queryFn: async () => {
      const result = await projectExtraServices(projectId, {
        headers: { "X-Organization-ID": orgId },
      });
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      return result.data;
    },
  });
  const [draft, setDraft] = useState<ExtraSelection[] | null>(null);
  const [undo, setUndo] = useState<ExtraSelection[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const choices = definitions(query.data?.definitions);
  const saved = (query.data?.selections ?? []) as ExtraSelection[];
  const selections = draft ?? saved;
  const editable = canWrite && !query.data?.locked;
  async function save(next: ExtraSelection[]) {
    if (!query.data) return;
    setBusy(true);
    setError("");
    try {
      const result = await projectExtraServicesSave(
        projectId,
        { selections: next, expected_updated_at: query.data.updated_at },
        { headers: { "X-Organization-ID": orgId } },
      );
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      setUndo(saved);
      setDraft(null);
      client.setQueryData(["project-services", orgId, projectId], result.data);
      await client.invalidateQueries({ queryKey: ["project", orgId, projectId] });
    } catch (cause) {
      setError(actionErrorDetail(cause, "No pudimos guardar los servicios."));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="project-services" aria-label="Servicios del proyecto">
      <h3>Servicios del proyecto</h3>
      {query.isPending ? (
        <p role="status">Cargando servicios…</p>
      ) : query.isError ? (
        <p role="alert">
          No pudimos cargar los servicios.{" "}
          <button onClick={() => void query.refetch()}>Reintentar</button>
        </p>
      ) : (
        <>
          {query.data.locked && (
            <p>Servicios de la revisión cerrada. Crea una revisión para cambiarlos.</p>
          )}
          {!canWrite && <p>Tu rol permite consultar los servicios.</p>}
          {!choices.length && (
            <p>
              Sin servicios declarados.{" "}
              <Link to="/settings/general">Configura tarifas y plantillas en Ajustes</Link>.
            </p>
          )}
          <ul className="extra-selected">
            {choices.map((item) => {
              const selection = selections.find((selected) => selected.code === item.code);
              return (
                <li key={item.code}>
                  <label>
                    <input
                      type="checkbox"
                      disabled={!editable || busy}
                      checked={Boolean(selection)}
                      onChange={(event) => {
                        setDraft(
                          event.target.checked
                            ? [
                                ...selections,
                                { code: item.code, zone: item.basis === "ZONE" ? null : undefined },
                              ]
                            : selections.filter((selected) => selected.code !== item.code),
                        );
                        setError("");
                      }}
                    />
                    <strong>
                      {item.name}
                      {item.synthetic && " · DEMO"}
                    </strong>
                  </label>
                  <small>
                    {extraBasisLabels[item.basis]} · {item.source}
                  </small>
                  {selection && item.basis === "ZONE" && (
                    <label>
                      Zona
                      <select
                        disabled={!editable || busy}
                        value={selection.zone ?? ""}
                        onChange={(event) =>
                          setDraft(
                            selections.map((selected) =>
                              selected.code === item.code
                                ? { ...selected, zone: event.target.value }
                                : selected,
                            ),
                          )
                        }
                      >
                        <option value="">Elige la zona de entrega</option>
                        {Object.keys(item.zones ?? {}).map((zone) => (
                          <option key={zone}>{zone}</option>
                        ))}
                      </select>
                    </label>
                  )}
                </li>
              );
            })}
          </ul>
          {draft ? (
            <p role="status">
              Cambios por guardar. El motor calculará sus cantidades y precio al guardar.
            </p>
          ) : (
            <ul className="extra-selected">
              {extraLines(query.data.lines).map((item) => (
                <li key={item.code} className="extra-equation">
                  <span>{item.name}</span>
                  {extraQuantity(item.quantity)} {extraUnit(item.unit)} ×{" "}
                  {extraTariff(item.unit_price ?? item.selling_rate, query.data.currency)} ={" "}
                  <strong>{formatMoney(item.amount, query.data.currency)}</strong>
                  {hasRounding(item.rounding) && (
                    <small>
                      Ajuste incluido: {extraQuantity(item.rounding!)} {query.data.currency}
                    </small>
                  )}
                </li>
              ))}
            </ul>
          )}
          {!selections.length && (
            <p>
              No has seleccionado servicios. Revisa si corresponde instalación, sellado, retiro o
              flete antes de cotizar.
            </p>
          )}
          {query.data.reason && <p role="alert">{query.data.reason}</p>}
          {editable && (
            <div className="inspector-actions">
              <button
                type="button"
                disabled={busy || draft === null}
                onClick={() => void save(selections)}
              >
                {busy ? "Guardando…" : "Guardar servicios"}
              </button>
              {draft !== null && (
                <button type="button" disabled={busy} onClick={() => setDraft(null)}>
                  Descartar cambios
                </button>
              )}
              {undo && (
                <button type="button" disabled={busy} onClick={() => void save(undo)}>
                  Deshacer
                </button>
              )}
            </div>
          )}
        </>
      )}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
