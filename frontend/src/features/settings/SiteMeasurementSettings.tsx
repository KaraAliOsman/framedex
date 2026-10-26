import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { companySiteMeasurement, companySiteMeasurementSave } from "../../api/generated/dekopen";
import type { SiteMeasurementEnum } from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { ErrorState, LoadingState } from "../../ui";

const OPTIONS: { value: SiteMeasurementEnum; title: string; body: string }[] = [
  {
    value: "QUOTED",
    title: "Las medidas de la cotización son de fabricación",
    body: "Para talleres que miden antes de cotizar. Al aprobar la obra puedes liberar la OT sin otra confirmación.",
  },
  {
    value: "REQUIRED",
    title: "Confirmar la medida en obra antes de fabricar",
    body: "Cada ventana necesita su medición en obra confirmada. Si cambia, se abre una revisión nueva con su precio.",
  },
];

/** How the workshop measures; each issued revision keeps the rule it was issued under. */
export function SiteMeasurementSettings({
  orgId,
  canEdit,
}: {
  orgId: string;
  canEdit: boolean;
}): JSX.Element {
  const queryClient = useQueryClient();
  const options = { headers: { "X-Organization-ID": orgId } };
  const queryKey = ["company-site-measurement", orgId];
  const query = useQuery({
    queryKey,
    queryFn: async ({ signal }) => {
      const response = await companySiteMeasurement({ ...options, signal });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data.site_measurement;
    },
  });
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function choose(value: SiteMeasurementEnum) {
    const previous = query.data;
    setBusy(true);
    setMessage("");
    queryClient.setQueryData(queryKey, value);
    try {
      const response = await companySiteMeasurementSave({ site_measurement: value }, options);
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      queryClient.setQueryData(queryKey, response.data.site_measurement);
      setMessage("Guardado. Se aplica a las próximas revisiones; las emitidas conservan su regla.");
    } catch {
      queryClient.setQueryData(queryKey, previous);
      setMessage("No se pudo guardar. Solo el dueño cambia cómo mide el taller.");
    } finally {
      setBusy(false);
    }
  }

  if (query.isPending) return <LoadingState label="Consultando cómo mide el taller" />;
  if (query.isError)
    return (
      <ErrorState
        body="No pudimos consultar cómo mide el taller."
        onRetry={() => void query.refetch()}
      />
    );
  return (
    <section className="settings-card" aria-label="Medición en obra">
      <h2>Medición en obra</h2>
      <fieldset className="site-measurement" disabled={!canEdit || busy}>
        <legend className="sr-only">Cómo mide el taller</legend>
        {OPTIONS.map((option) => (
          <label key={option.value} className="site-measurement__option">
            <input
              type="radio"
              name="site-measurement"
              value={option.value}
              checked={query.data === option.value}
              onChange={() => void choose(option.value)}
            />
            <span>
              <strong>{option.title}</strong>
              <span>{option.body}</span>
            </span>
          </label>
        ))}
      </fieldset>
      {!canEdit && <p>Solo el dueño cambia esta regla.</p>}
      {message && <p role="status">{message}</p>}
    </section>
  );
}
