import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { apiMutator } from "../../api/apiMutator";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { formatDateTime, formatRevision } from "../../format";
import { ErrorState, LoadingState } from "../../ui";
import { ValidatedForm } from "../../ui/FormValidation";
import { actionErrorDetail } from "../errors";
import { Projection, type Operation } from "./ProjectPrices";
import "./pricing.css";

const states: Record<string, string> = {
  PENDING: "Espera aprobación",
  APPLIED: "Aprobada y aplicada",
  REJECTED: "Rechazada",
  WITHDRAWN: "Retirada",
  PREVIEW: "Propuesta sin aplicar",
};

export function PriceDecision({
  operationId,
  owner,
}: {
  operationId: string;
  owner: boolean;
}): JSX.Element {
  const org = useAuthSession().me!.active_organization!;
  const [comment, setComment] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const live = useRef<AbortController | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    live.current = controller;
    return () => controller.abort();
  }, []);
  const query = useQuery({
    queryKey: ["price-decision", org.id, operationId],
    retry: false,
    queryFn: async ({ signal }) => {
      const response = await apiMutator<{ data: Operation }>(
        `/api/v1/pricing/operations/${operationId}/`,
        { signal, headers: { "X-Organization-ID": org.id } },
      );
      return response.data;
    },
  });
  async function decide(kind: "approve" | "reject" | "read"): Promise<void> {
    if (busy || live.current?.signal.aborted) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await apiMutator(
        `/api/v1/pricing/${kind === "read" ? "acknowledge/" : `operations/${operationId}/apply/`}`,
        {
          method: "POST",
          signal: live.current?.signal,
          headers: { "X-Organization-ID": org.id, "Content-Type": "application/json" },
          body: JSON.stringify(
            kind === "read"
              ? { operation_ids: [operationId] }
              : { reason: comment, confirmed, reject: kind === "reject" },
          ),
        },
      );
      if (live.current?.signal.aborted) return;
      setNotice(
        kind === "read"
          ? "Decisión marcada como leída."
          : kind === "reject"
            ? "Solicitud rechazada. El solicitante verá tu decisión."
            : "Precio aprobado y aplicado. El solicitante verá tu decisión.",
      );
      setConfirmed(false);
      await query.refetch();
      window.dispatchEvent(new Event("dekopen:pricing-changed"));
    } catch (failure) {
      if (!live.current?.signal.aborted)
        setError(
          actionErrorDetail(
            failure,
            "No se guardó la decisión. Revisa el estado de la solicitud y vuelve a intentar.",
          ),
        );
    } finally {
      if (!live.current?.signal.aborted) setBusy(false);
    }
  }
  if (query.isPending) return <LoadingState label="Cargando la propuesta de precio" />;
  if (query.isError)
    return (
      <ErrorState
        title="No se pudo abrir la propuesta"
        body="La operación puede haber cambiado o no estar disponible para tu rol. Reintenta la consulta."
        onRetry={() => void query.refetch()}
      />
    );
  const operation = query.data;
  return (
    <div className="pricing-page price-inline-decision">
      <p className="ui-value">
        {operation.project_code} · {formatRevision(operation.revision_code)}
      </p>
      <h3>{states[operation.state] ?? "Sin dato · estado sin reconocer"}</h3>
      <p>{operation.reason}</p>
      <p>
        Solicitó {operation.requested_by_email ?? "un integrante del taller"} ·{" "}
        {operation.created_at && formatDateTime(operation.created_at)}
      </p>
      {operation.approved_at && (
        <p>Decisión registrada · {formatDateTime(operation.approved_at)}</p>
      )}
      <Projection operation={operation} owner={owner} />
      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}
      {operation.state === "PENDING" && owner && (
        <ValidatedForm
          onSubmit={(event) => {
            event.preventDefault();
            void decide("approve");
          }}
        >
          <label>
            Motivo de la decisión
            <textarea
              required
              value={comment}
              onChange={(event) => setComment(event.target.value)}
            />
          </label>
          <label className="price-decision-confirm">
            <input
              type="checkbox"
              checked={confirmed}
              onChange={(event) => setConfirmed(event.target.checked)}
            />
            Confirmo las condiciones comerciales de esta propuesta
          </label>
          <div className="price-decision-actions">
            <button
              type="submit"
              className="ui-button ui-button--primary"
              disabled={busy || !confirmed || !comment.trim()}
            >
              Aprobar y aplicar
            </button>
            <button
              type="button"
              className="ui-button ui-button--danger"
              disabled={busy || !confirmed || !comment.trim()}
              onClick={() => void decide("reject")}
            >
              Rechazar
            </button>
          </div>
        </ValidatedForm>
      )}
      {operation.notification_unread && (
        <button
          type="button"
          className="ui-button"
          disabled={busy}
          onClick={() => void decide("read")}
        >
          Marcar decisión como leída
        </button>
      )}
      <Link to={`/projects/${operation.project_id}/pricing?operation=${operationId}`}>
        Abrir el precio del proyecto
      </Link>
    </div>
  );
}
