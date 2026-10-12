import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { collectionReminderPrepare, collectionReminderSend } from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import { actionErrorDetail } from "../errors";
import { ErrorState, LoadingState, useConfirm } from "../../ui";
import { MailHistory } from "../notifications/MailPanels";

export function CollectionReminder({
  orgId,
  projectId,
}: {
  orgId: string;
  projectId: string;
}): JSX.Element {
  const options = { headers: { "X-Organization-ID": orgId } };
  const query = useQuery({
    queryKey: ["collection-reminder", orgId, projectId],
    retry: false,
    queryFn: async () => {
      const result = await collectionReminderPrepare(projectId, options);
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      return result.data;
    },
  });
  const confirm = useConfirm();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [sent, setSent] = useState(false);
  async function send() {
    if (
      !query.data ||
      !(await confirm({
        title: "Enviar recordatorio de pago",
        body: `Se enviará el mensaje revisado a ${query.data.recipient}. El saldo se comprobará de nuevo antes de enviar.`,
        confirmLabel: "Enviar recordatorio",
      }))
    )
      return;
    setBusy(true);
    setMessage("");
    try {
      const result = await collectionReminderSend(
        projectId,
        { reminder_id: query.data.id, confirmed: true },
        options,
      );
      if (result.status !== 202) throw new ApiError(result.status, result.data);
      setSent(true);
    } catch (error) {
      setMessage(actionErrorDetail(error, "No se preparó el envío. Revisa el saldo y reintenta."));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="collection-reminder" aria-label="Recordatorio de cobranza">
      <h3>Mensaje preparado para el cliente</h3>
      {query.isPending ? (
        <LoadingState label="Preparando el recordatorio con la IA" />
      ) : query.isError ? (
        <ErrorState
          title="No se preparó el mensaje"
          body={actionErrorDetail(
            query.error,
            "Reintenta preparar el borrador con el saldo vigente. No se envió correo.",
          )}
          onRetry={() => void query.refetch()}
        />
      ) : (
        <>
          <p>
            Preparado por la IA · montos y fechas del acuerdo sellado. Revísalo antes de enviarlo.
          </p>
          <p>Para: {query.data.recipient}</p>
          <p>{query.data.reference}</p>
          <p className="collection-reminder__body">{query.data.body}</p>
          {!sent && !query.data.sent && (
            <button type="button" disabled={busy} onClick={() => void send()}>
              Revisar y enviar recordatorio
            </button>
          )}
          {(sent || query.data.sent) && (
            <p role="status">
              Envío registrado. Consulta su estado en el historial de correos del proyecto.
            </p>
          )}
        </>
      )}
      {message && (
        <p className="form-error" role="status">
          {message}
        </p>
      )}
      {(sent || query.data?.sent) && <MailHistory orgId={orgId} projectId={projectId} />}
    </section>
  );
}
