import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { ApiError } from "../../api/apiMutator";
import { flowSimulationConfirm, flowSimulationStatus } from "../../api/generated/dekopen";
import { actionErrorDetail } from "../errors";
import { DateOnly, ErrorState, LoadingState, Money } from "../../ui";
import "./portal.css";

const states: Record<string, string> = {
  PENDING: "Pendiente de pago",
  PAID: "Pago de prueba registrado",
  FAILED: "Pago de prueba rechazado",
  EXPIRED: "Enlace de prueba vencido",
  CANCELLED: "Enlace de prueba cancelado",
};

export function FlowSimulationPage({ returnMode = false }: { returnMode?: boolean }): JSX.Element {
  const params = useParams();
  const [search] = useSearchParams();
  const navigate = useNavigate();
  const id = params.linkId ?? search.get("sim") ?? "";
  const token = search.get("token") ?? "";
  const query = useQuery({
    queryKey: ["flow-simulation", id, token],
    retry: false,
    queryFn: async () => {
      const result = await flowSimulationStatus(id, { token });
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      return result.data;
    },
  });
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  async function settle(outcome: "PAID" | "FAILED") {
    setBusy(true);
    setMessage("");
    try {
      const result = await flowSimulationConfirm(id, { token, outcome });
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      await query.refetch();
      navigate(`/pago/retorno?sim=${encodeURIComponent(id)}&token=${encodeURIComponent(token)}`);
    } catch (error) {
      setMessage(actionErrorDetail(error, "No se completó la prueba. Solicite un enlace vigente."));
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="portal-page" data-density="document">
      <section className="portal-card portal-card--narrow">
        <h1>{returnMode ? "Resultado del pago de prueba" : "Prueba de pago"}</h1>
        <p>Simulador Flow — no se moverá dinero ni se comunicarán datos a Flow.</p>
        {query.isPending ? (
          <LoadingState label="Consultando el cobro de prueba" />
        ) : query.isError ? (
          <ErrorState
            title="Acceso de prueba no disponible"
            body={actionErrorDetail(
              query.error,
              "Solicite un enlace vigente a quien emitió su cotización.",
            )}
            onRetry={() => void query.refetch()}
          />
        ) : (
          <>
            <dl>
              <dt>Monto de prueba</dt>
              <dd>
                <Money value={query.data.amount} />
              </dd>
              <dt>Vencimiento</dt>
              <dd>
                <DateOnly value={query.data.expires_at} />
              </dd>
              <dt>Estado</dt>
              <dd>{states[query.data.status]}</dd>
            </dl>
            {query.data.status === "PENDING" && !returnMode && (
              <div className="collection-payer-actions">
                <button
                  type="button"
                  className="primary-action"
                  onClick={() => void settle("PAID")}
                  disabled={busy}
                >
                  Simular pago aprobado
                </button>
                <button type="button" onClick={() => void settle("FAILED")} disabled={busy}>
                  Simular pago rechazado
                </button>
              </div>
            )}
            {query.data.status === "PAID" && (
              <p>
                La confirmación de prueba registró un único movimiento simulado y su recibo. Quien
                emitió la cotización puede consultarlos en Cobranza.
              </p>
            )}
            {query.data.status === "PENDING" && returnMode && (
              <Link to={`/pago/simulado/${id}?token=${encodeURIComponent(token)}`}>
                Volver a la prueba
              </Link>
            )}
          </>
        )}
        {message && <p role="alert">{message}</p>}
      </section>
    </main>
  );
}
