import { useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { fiscalSimulate, fiscalSimulations } from "../../api/generated/dekopen";
import type { ProjectInvoice, FiscalSimulationStatusEnum } from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { actionErrorDetail } from "../errors";
import { DateOnly, ErrorState, LoadingState } from "../../ui";
import { ValidatedForm } from "../../ui/FormValidation";

export const fiscalLabels: Record<string, string> = {
  ACCEPTED: "Aceptado",
  WARNINGS: "Aceptado con reparos",
  REJECTED: "Rechazado",
  PENDING: "En revisión",
};

export function FiscalSimulationPanel({
  orgId,
  projectId,
  invoices,
  canWrite,
  enabled,
}: {
  orgId: string;
  projectId: string;
  invoices: ProjectInvoice[];
  canWrite: boolean;
  enabled: boolean;
}): JSX.Element {
  const options = { headers: { "X-Organization-ID": orgId } };
  const query = useQuery({
    queryKey: ["fiscal-simulations", orgId, projectId],
    queryFn: async () => {
      const result = await fiscalSimulations(projectId, options);
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      return result.data.items;
    },
  });
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  async function simulate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const [invoice_id, credit_note_id] = String(form.get("document")).split(":");
    if (!invoice_id) return;
    setBusy(true);
    setMessage("");
    try {
      const result = await fiscalSimulate(
        projectId,
        {
          invoice_id,
          ...(credit_note_id ? { credit_note_id } : {}),
          operation_key: crypto.randomUUID(),
          scenario: String(form.get("scenario")) as FiscalSimulationStatusEnum,
        },
        options,
      );
      if (result.status !== 201) throw new ApiError(result.status, result.data);
      await query.refetch();
      setMessage(result.data.detail);
    } catch (error) {
      setMessage(actionErrorDetail(error, "No se completó la prueba. Reintenta."));
    } finally {
      setBusy(false);
    }
  }
  return (
    <details className="collection-simulations">
      <summary>Pruebas del adaptador SII</summary>
      <p>
        Simulación explícita: no envía documentos a SII, no usa CAF ni genera timbre electrónico.
        Los folios de prueba están separados.
      </p>
      {query.isPending ? (
        <LoadingState label="Consultando las pruebas fiscales" />
      ) : query.isError ? (
        <ErrorState
          title="No se cargaron las pruebas"
          body="Reintenta consultar la evidencia conservada."
          onRetry={() => void query.refetch()}
        />
      ) : query.data.length ? (
        <ul>
          {query.data.map((item) => (
            <li key={item.id}>
              <span className="ui-value">{item.folio}</span> · Simulado ·{" "}
              {fiscalLabels[item.status]} · <DateOnly value={item.created_at} />
              <p>{item.detail}</p>
            </li>
          ))}
        </ul>
      ) : (
        <p>No hay pruebas tributarias para este proyecto.</p>
      )}
      {canWrite && enabled && invoices.length > 0 ? (
        <ValidatedForm className="payments-form" onSubmit={simulate}>
          <label>
            Documento
            <select name="document">
              {invoices.flatMap((invoice) => [
                <option key={invoice.id} value={invoice.id}>
                  {invoice.invoice_code} ·{" "}
                  {invoice.document_kind === "BOLETA" ? "Boleta interna" : "Factura interna"}
                </option>,
                ...(invoice.credit_note
                  ? [
                      <option
                        key={invoice.credit_note.id}
                        value={`${invoice.id}:${invoice.credit_note.id}`}
                      >
                        {invoice.credit_note.credit_code} · Nota de crédito interna
                      </option>,
                    ]
                  : []),
              ])}
            </select>
          </label>
          <label>
            Respuesta a probar
            <select name="scenario">
              <option value="ACCEPTED">Aceptado</option>
              <option value="WARNINGS">Aceptado con reparos</option>
              <option value="REJECTED">Rechazado</option>
            </select>
          </label>
          <button type="submit" disabled={busy}>
            Simular respuesta SII
          </button>
        </ValidatedForm>
      ) : (
        <p>
          {!enabled
            ? "El dueño desactivó las pruebas en Ajustes › Cobranza e integraciones."
            : !canWrite
              ? "El dueño o estimador puede registrar una prueba."
              : "Emite un documento interno para probar el adaptador."}
        </p>
      )}
      {message && <p role="status">{message}</p>}
    </details>
  );
}
