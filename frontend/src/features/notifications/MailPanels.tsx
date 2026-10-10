import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "../../api/apiMutator";
import {
  mailIntegrationStatus,
  mailList,
  mailRecover,
  paymentMailPreview,
  paymentMailSend,
} from "../../api/generated/dekopen";
import type { MailPreview, MailRecord } from "../../api/generated/models";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { formatDateTime } from "../../format";
import { actionErrorDetail } from "../errors";
import { BlockedState, Button, EmptyState, ErrorState, LoadingState, useConfirm } from "../../ui";
import "./mail.css";

const STATE: Record<string, string> = {
  QUEUED: "En cola",
  DISPATCHING: "Enviando",
  SENT: "Aceptado por el servidor",
  FAILED: "No enviado",
  UNCERTAIN: "Entrega sin confirmar",
};
const KIND: Record<string, string> = {
  QUOTE: "Cotización",
  PAYMENT: "Pago registrado",
  APPROVAL: "Aprobación recibida",
  ORDER_BLOCKED: "OT bloqueada",
  PURCHASE: "Orden de compra",
};

function pendingKey(key: string, source: MailPreview | undefined): string | null {
  if (!source) return null;
  try {
    const saved: unknown = JSON.parse(sessionStorage.getItem(key) ?? "null");
    if (!saved || typeof saved !== "object") return null;
    const record = saved as Record<string, unknown>;
    return typeof record.operation_key === "string" &&
      /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(record.operation_key) &&
      record.expected_source_id === source.source_id &&
      record.expected_recipient === source.recipient &&
      record.expected_document_sha256 === source.document_sha256
      ? record.operation_key
      : null;
  } catch {
    return null;
  }
}

export function MailFrame({ html, title }: { html: string; title: string }): JSX.Element {
  return <iframe className="mail-preview-frame" title={title} srcDoc={html} sandbox="" />;
}

export function PaymentMailComposer({
  orgId,
  projectId,
  paymentId,
  autoOpen = false,
}: {
  orgId: string;
  projectId: string;
  paymentId: string;
  autoOpen?: boolean;
}): JSX.Element {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(autoOpen);
  const [operationKey, setOperationKey] = useState<string>(() => crypto.randomUUID());
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState<MailRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const options = { headers: { "X-Organization-ID": orgId } };
  const intentStorageKey = `mail-intent:${orgId}:${projectId}:${paymentId}`;
  const query = useQuery({
    queryKey: ["mail-preview", orgId, projectId, paymentId],
    enabled: open,
    queryFn: async ({ signal }) => {
      const response = await paymentMailPreview(projectId, paymentId, { ...options, signal });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
  });
  useEffect(() => {
    setConfirmed(false);
    setOperationKey(pendingKey(intentStorageKey, query.data) ?? crypto.randomUUID());
  }, [intentStorageKey, query.data?.source_id, query.data?.recipient, query.data?.document_sha256]);
  async function send(): Promise<void> {
    if (!query.data?.document_sha256 || !confirmed || busy || query.isFetching) return;
    setBusy(true);
    setError(null);
    const body = {
      operation_key: operationKey,
      expected_source_id: query.data.source_id,
      expected_recipient: query.data.recipient,
      expected_document_sha256: query.data.document_sha256,
      confirmed: true,
    };
    try {
      sessionStorage.setItem(intentStorageKey, JSON.stringify(body));
    } catch {
      setError(
        "No se pudo conservar el intento de envío. Habilita el almacenamiento de sesión del navegador antes de enviar.",
      );
      setBusy(false);
      return;
    }
    try {
      const response = await paymentMailSend(projectId, paymentId, body, options);
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      setSent(response.data);
      if (pendingKey(intentStorageKey, query.data) === operationKey)
        sessionStorage.removeItem(intentStorageKey);
      void queryClient.invalidateQueries({ queryKey: ["mail", orgId] });
    } catch (caught) {
      setError(
        actionErrorDetail(
          caught,
          "No se pudo registrar el envío. Revisa la conexión; volver a intentarlo conserva la misma operación.",
        ),
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="mail-composer">
      {!open ? (
        <Button
          onClick={() => {
            setOperationKey(pendingKey(intentStorageKey, query.data) ?? crypto.randomUUID());
            setSent(null);
            setOpen(true);
          }}
        >
          Enviar comprobante por correo
        </Button>
      ) : (
        <section aria-label="Revisar correo antes de enviar">
          <h3>Correo de pago registrado</h3>
          {query.isPending ? (
            <LoadingState label="Preparando la vista previa" />
          ) : query.isError ? (
            <ErrorState
              title="No se pudo preparar el correo"
              body={actionErrorDetail(query.error, "Revisa la emisión y los datos del cliente.")}
              onRetry={() => {
                setConfirmed(false);
                void query.refetch();
              }}
            />
          ) : query.data.recipient ? (
            <>
              <p>
                Para: <strong>{query.data.recipient}</strong> · {query.data.reference}
              </p>
              {query.data.provider === "sandbox" ? (
                <p className="mail-hint">
                  Sandbox: el mensaje queda en Mailpit. El dominio de envío aún no está conectado.
                </p>
              ) : null}
              <MailFrame html={query.data.html} title="Vista previa del correo al cliente" />
              {query.data.document_url ? (
                <div className="mail-document">
                  <a
                    className="mail-document-link"
                    href={query.data.document_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Abrir PDF sellado · {query.data.document_name}
                  </a>
                  <p>Este es el documento que se adjuntará al correo.</p>
                </div>
              ) : (
                <BlockedState
                  reason="Falta el PDF de este comprobante. Revisa el pago registrado antes de enviar."
                  action={
                    <Button disabled={query.isFetching} onClick={() => void query.refetch()}>
                      Revisar comprobante
                    </Button>
                  }
                />
              )}
              {sent ? (
                <p role="status">
                  Envío registrado · {STATE[sent.state] ?? "Revisar estado en la bandeja"}. La
                  bandeja muestra la respuesta del servidor.
                </p>
              ) : (
                <>
                  <label className="mail-confirm">
                    <input
                      type="checkbox"
                      checked={confirmed}
                      disabled={!query.data.document_sha256 || query.isFetching || busy}
                      onChange={(event) => setConfirmed(event.target.checked)}
                    />
                    Revisé el destinatario, el documento y autorizo este envío.
                  </label>
                  <Button
                    variant="primary"
                    disabled={!confirmed || busy || query.isFetching || !query.data.document_sha256}
                    onClick={() => {
                      void send();
                    }}
                  >
                    {busy ? "Registrando envío" : "Enviar al cliente"}
                  </Button>
                </>
              )}
            </>
          ) : (
            <BlockedState
              reason="Esta emisión no tiene correo de cliente. Completa el contacto y emite una nueva revisión antes de enviar."
              action={
                <Button
                  onClick={() => {
                    setOpen(false);
                  }}
                >
                  Cerrar revisión
                </Button>
              }
            />
          )}
          {error ? <p role="alert">{error}</p> : null}
          <Button
            variant="ghost"
            disabled={busy}
            onClick={() => {
              setOpen(false);
              setConfirmed(false);
            }}
          >
            Cerrar vista previa
          </Button>
        </section>
      )}
    </div>
  );
}

export function MailHistory({
  orgId,
  projectId,
}: {
  orgId: string;
  projectId?: string;
}): JSX.Element {
  const auth = useAuthSession();
  const canWrite = ["OWNER", "ESTIMATOR"].includes(auth.me?.active_organization?.role ?? "");
  const confirm = useConfirm();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const options = { headers: { "X-Organization-ID": orgId } };
  const query = useQuery({
    queryKey: ["mail", orgId, projectId],
    queryFn: async ({ signal }) => {
      const response = await mailList(projectId ? { project_id: projectId } : undefined, {
        ...options,
        signal,
      });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
    refetchInterval: (current) =>
      current.state.data?.some((item) => ["QUEUED", "DISPATCHING"].includes(item.state))
        ? 2000
        : false,
  });
  async function recover(row: MailRecord): Promise<void> {
    if (
      !(await confirm({
        title: "Comprobar antes de reenviar",
        body: "Revisa el servidor de correo y confirma con el destinatario que no recibió este mensaje. Una entrega sin respuesta puede haber llegado. Reenviar conserva el contenido y deja un nuevo intento en el historial.",
        confirmLabel: "Comprobé que no llegó; reenviar",
      }))
    )
      return;
    setBusy(true);
    setError(null);
    try {
      const response = await mailRecover(
        row.id,
        { expected_attempt: row.attempt, confirmed_remote_absence: true },
        options,
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      await query.refetch();
    } catch (caught) {
      setError(
        actionErrorDetail(
          caught,
          "No se pudo reencolar el correo. Actualiza el estado antes de intentar de nuevo.",
        ),
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="mail-history" aria-label="Bandeja de correo">
      <h3>Bandeja de correo</h3>
      {query.isPending ? (
        <LoadingState label="Consultando envíos" />
      ) : query.isError ? (
        <ErrorState
          title="No se pudo consultar la bandeja"
          onRetry={() => {
            void query.refetch();
          }}
        />
      ) : query.data.length === 0 ? (
        <EmptyState
          title="No hay correos registrados"
          body="Los envíos al cliente requieren revisar el destinatario y confirmar. Los avisos internos se activan en Ajustes."
        />
      ) : (
        <ul>
          {query.data.map((row) => (
            <li key={row.id}>
              <strong>
                {KIND[row.kind] ?? "Correo"} · {STATE[row.state] ?? "Estado por revisar"}
              </strong>
              <p>
                {row.recipient} · {formatDateTime(row.created_at)}
              </p>
              <p>{row.subject}</p>
              {row.state === "UNCERTAIN" ? (
                <p role="status">
                  La respuesta se perdió. Comprueba la entrega antes de volver a enviar.
                </p>
              ) : null}
              {row.error_code === "mail_quote_link_inactive" ? (
                <p>
                  El enlace venció o fue revocado. Revisa su historial y regenera el acceso si
                  corresponde; el envío anterior se conserva.
                </p>
              ) : row.error_code === "mail_payment_voided" ? (
                <p>
                  El pago fue anulado. Este comprobante no se puede volver a enviar como un pago
                  vigente.
                </p>
              ) : row.error_code === "mail_purchase_cancelled" ? (
                <p>
                  La OC fue cancelada. Este correo se conserva como historial; revisa la nueva
                  compra antes de enviar.
                </p>
              ) : null}
              {canWrite && row.error_code === "mail_quote_link_inactive" && row.project_id ? (
                <Link
                  className="mail-document-link"
                  to={`/projects/${row.project_id}?section=quote`}
                >
                  Revisar enlace de cotización
                </Link>
              ) : (canWrite ||
                  (row.kind === "PURCHASE" &&
                    auth.me?.active_organization?.role === "WORKSHOP_MANAGER")) &&
                row.error_code !== "mail_payment_voided" &&
                row.error_code !== "mail_purchase_cancelled" &&
                ["FAILED", "UNCERTAIN"].includes(row.state) ? (
                <Button
                  disabled={busy}
                  onClick={() => {
                    void recover(row);
                  }}
                >
                  Comprobar y reenviar
                </Button>
              ) : null}
              {row.error_code ? (
                <details>
                  <summary>Detalles técnicos</summary>
                  <p>{row.error_code}</p>
                </details>
              ) : null}
            </li>
          ))}
        </ul>
      )}
      {error ? <p role="alert">{error}</p> : null}
      <Button
        variant="ghost"
        disabled={query.isFetching}
        onClick={() => {
          void query.refetch();
        }}
      >
        Actualizar bandeja
      </Button>
    </section>
  );
}

export function MailIntegrationCard({ orgId }: { orgId: string }): JSX.Element {
  const query = useQuery({
    queryKey: ["mail-integration", orgId],
    queryFn: async ({ signal }) => {
      const response = await mailIntegrationStatus({
        headers: { "X-Organization-ID": orgId },
        signal,
      });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
  });
  return (
    <div className="settings-card">
      <h3>Correo</h3>
      {query.isPending ? (
        <LoadingState label="Consultando conexión de correo" />
      ) : query.isError ? (
        <ErrorState
          title="No se pudo comprobar el correo"
          onRetry={() => {
            void query.refetch();
          }}
        />
      ) : (
        <>
          <p>{query.data.connected ? "Conectado" : "No conectado · sandbox Mailpit"}</p>
          <p className="settings-hint">{query.data.instructions}</p>
        </>
      )}
      <MailHistory orgId={orgId} />
    </div>
  );
}
