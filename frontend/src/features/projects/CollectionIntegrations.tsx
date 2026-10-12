import { useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { collectionIntegrations, collectionSettingsSave } from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import { actionErrorDetail } from "../errors";
import { ErrorState, LoadingState } from "../../ui";
import { ValidatedForm } from "../../ui/FormValidation";

export function CollectionIntegrations({ orgId }: { orgId: string }): JSX.Element {
  const options = { headers: { "X-Organization-ID": orgId } };
  const query = useQuery({
    queryKey: ["collection-integrations", orgId],
    queryFn: async () => {
      const result = await collectionIntegrations(options);
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      return result.data;
    },
  });
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setMessage("");
    try {
      const result = await collectionSettingsSave(
        {
          payment_link_days: Number(form.get("days")),
          simulation_enabled: form.has("simulation"),
          sii_active: form.has("active"),
          sii_certified: form.has("certified"),
        },
        options,
      );
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      await query.refetch();
      setMessage("Preferencias guardadas.");
    } catch (error) {
      setMessage(actionErrorDetail(error, "No se guardaron las preferencias. Reintenta."));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section
      className="settings-card"
      id="cobranza-integraciones"
      aria-labelledby="collection-settings-title"
    >
      <h3 id="collection-settings-title">Cobranza e integraciones</h3>
      {query.isPending ? (
        <LoadingState label="Consultando las integraciones" />
      ) : query.isError ? (
        <ErrorState
          title="No se pudo consultar la conexión"
          body="Las credenciales permanecen guardadas. Reintenta la consulta."
          onRetry={() => void query.refetch()}
        />
      ) : (
        <>
          <dl className="settings-list">
            <dt>Flow</dt>
            <dd>
              {query.data.flow_connected
                ? query.data.flow_environment === "production"
                  ? "Conectado · producción"
                  : "Conectado · sandbox"
                : "No conectado"}
            </dd>
            <dt>SII</dt>
            <dd>
              {query.data.sii_connected
                ? "Activo · certificación declarada y certificado vigente"
                : "No conectado"}
            </dd>
          </dl>
          <p>{query.data.flow_instructions}</p>
          <p>{query.data.sii_instructions}</p>
          <p>
            Los simuladores no mueven dinero ni consumen folios tributarios. Cada prueba conserva su
            marca en movimientos y documentos.
          </p>
          <ValidatedForm onSubmit={save} key={query.dataUpdatedAt}>
            <label>
              Vigencia de los enlaces (días)
              <input
                name="days"
                inputMode="numeric"
                data-precision="0"
                min="1"
                max="90"
                required
                defaultValue={query.data.payment_link_days}
              />
            </label>
            <label className="settings-check">
              <input
                type="checkbox"
                name="simulation"
                defaultChecked={query.data.simulation_enabled}
              />
              Permitir simuladores explícitos de Flow y SII
            </label>
            <label className="settings-check">
              <input type="checkbox" name="certified" defaultChecked={query.data.sii_certified} />
              La organización completó la certificación con SII
            </label>
            <label className="settings-check">
              <input type="checkbox" name="active" defaultChecked={query.data.sii_active} />
              Activar el adaptador SII productivo configurado en el servidor
            </label>
            <button type="submit" disabled={busy}>
              Guardar preferencias
            </button>
          </ValidatedForm>
        </>
      )}
      {message && <p role="status">{message}</p>}
      <a
        href="https://github.com/KaraAliOsman/framedex/blob/integracion/v1/docs/operations/ACTIVACION.md"
        target="_blank"
        rel="noreferrer"
      >
        Instrucciones de activación
      </a>
    </section>
  );
}
