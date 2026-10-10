import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { ApiError } from "../../api/apiMutator";
import {
  projectPaymentLinkCreate,
  projectPaymentLinkRecover,
  projectPaymentLinksList,
} from "../../api/generated/dekopen";
import type {
  CollectionIntegration,
  PaymentKindEnum,
  PaymentLinkStatusEnum,
} from "../../api/generated/models";
import { actionErrorDetail } from "../errors";
import { compareDecimal, decimalInputValue, parseDecimalInput } from "../../decimal";
import { DateOnly, ErrorState, LoadingState, Money, StatusBadge, MoneyField } from "../../ui";
import { ValidatedForm } from "../../ui/FormValidation";

const states: Record<PaymentLinkStatusEnum, string> = {
  DISPATCHING: "Preparando cobro",
  PENDING: "Pendiente de pago",
  PAID: "Pagado",
  FAILED: "Rechazado",
  UNCERTAIN: "Resultado por verificar",
  CANCELLED: "Cancelado",
  EXPIRED: "Vencido",
};
const kinds: Record<string, string> = {
  ANTICIPO: "Anticipo",
  PARCIAL: "Abono parcial",
  SALDO: "Saldo",
};

export function ProjectPaymentLinksPanel({
  projectId,
  orgId,
  canWrite,
  isOwner = false,
  integration,
  balance,
  onChanged,
  onDirtyChange,
}: {
  projectId: string;
  orgId: string;
  canWrite: boolean;
  isOwner?: boolean;
  integration?: CollectionIntegration | null;
  balance?: string | null;
  onChanged: () => void;
  onDirtyChange?: (dirty: boolean) => void;
}): JSX.Element {
  const options = { headers: { "X-Organization-ID": orgId } };
  const query = useQuery({
    queryKey: ["projects", "payment-links", orgId, projectId],
    queryFn: async ({ signal }) => {
      const result = await projectPaymentLinksList(projectId, { ...options, signal });
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      return result.data.links;
    },
  });
  const [showForm, setShowForm] = useState(false);
  const [simulated, setSimulated] = useState(false);
  const [kind, setKind] = useState<PaymentKindEnum>("SALDO");
  const [amount, setAmount] = useState("");
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const operation = useRef("");
  const live = query.data?.some((link) =>
    ["PENDING", "UNCERTAIN", "DISPATCHING"].includes(link.status),
  );
  useEffect(() => {
    onDirtyChange?.(showForm && (amount !== "" || email !== ""));
  }, [showForm, amount, email, onDirtyChange]);
  async function create(event: FormEvent) {
    event.preventDefault();
    const parsed = parseDecimalInput(amount, 0);
    if (parsed === null || compareDecimal(parsed, "0") <= 0) {
      setMessage("Escribe un monto CLP entero mayor que cero.");
      return;
    }
    setBusy(true);
    setMessage("");
    try {
      const result = await projectPaymentLinkCreate(
        projectId,
        {
          operation_key: operation.current,
          kind,
          amount: parsed,
          payer_email: email.trim(),
          simulated,
        },
        options,
      );
      if (result.status !== 201) throw new ApiError(result.status, result.data);
      setShowForm(false);
      await query.refetch();
      onChanged();
    } catch (error) {
      setMessage(actionErrorDetail(error, "No se preparó el enlace. Revisa el saldo y reintenta."));
    } finally {
      setBusy(false);
    }
  }
  function open(simulation: boolean) {
    operation.current = crypto.randomUUID();
    setAmount(balance ? decimalInputValue(balance).replace(".", ",") : "");
    setSimulated(simulation);
    setShowForm(true);
    setMessage("");
  }
  async function recover(id: string) {
    setBusy(true);
    setMessage("");
    try {
      const result = await projectPaymentLinkRecover(projectId, id, options);
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      await query.refetch();
      onChanged();
    } catch (error) {
      setMessage(
        actionErrorDetail(error, "No se verificó el cobro. Reintenta consultar su estado."),
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="payment-links" aria-labelledby="payment-links-title">
      <div className="projects-actions">
        <h3 id="payment-links-title">Enlaces de pago</h3>
        {canWrite && !showForm && !live && balance && compareDecimal(balance, "0") > 0 && (
          <>
            {integration?.flow_connected && (
              <button type="button" onClick={() => open(false)} disabled={busy}>
                Crear enlace Flow
              </button>
            )}
            {integration?.simulation_enabled && (
              <button type="button" onClick={() => open(true)} disabled={busy}>
                Crear enlace de prueba
              </button>
            )}
          </>
        )}
      </div>
      {integration && !integration.flow_connected && (
        <p>
          Flow: No conectado.{" "}
          {isOwner ? (
            <Link to="/settings#cobranza-integraciones">Conectar en Ajustes</Link>
          ) : (
            "El dueño puede conectarlo en Ajustes."
          )}{" "}
          {integration.simulation_enabled &&
            "Puedes probar el flujo con un enlace marcado como simulado."}
        </p>
      )}
      {!canWrite && (
        <p>
          El dueño o estimador puede crear y verificar cobros. Tu rol permite consultar los enlaces.
        </p>
      )}
      {message && (
        <p className="form-error" role="status">
          {message}
        </p>
      )}
      {showForm && (
        <ValidatedForm className="payments-form" onSubmit={create}>
          <p className="payments-form-wide">
            {simulated
              ? "Pago simulado — no se moverá dinero."
              : integration?.flow_environment === "production"
                ? "Este enlace cobrará dinero real mediante Flow."
                : "Flow sandbox — prueba en el entorno del proveedor."}{" "}
            Vigencia configurada:{" "}
            <span className="ui-value">{integration?.payment_link_days} días</span>.
          </p>
          <label>
            Concepto
            <select
              value={kind}
              onChange={(event) => setKind(event.target.value as PaymentKindEnum)}
            >
              <option value="ANTICIPO">Anticipo</option>
              <option value="PARCIAL">Abono parcial</option>
              <option value="SALDO">Saldo</option>
            </select>
          </label>
          <label>
            Monto CLP
            <MoneyField required min="1" value={amount} onValueChange={setAmount} />
          </label>
          <label>
            Correo del pagador
            <input
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <div className="payments-form-actions">
            <button type="submit" className="primary-action" disabled={busy}>
              {simulated ? "Preparar cobro simulado" : "Preparar cobro Flow"}
            </button>
            <button type="button" onClick={() => setShowForm(false)} disabled={busy}>
              Cancelar
            </button>
          </div>
        </ValidatedForm>
      )}
      {query.isPending ? (
        <LoadingState label="Consultando los enlaces de pago" />
      ) : query.isError ? (
        <ErrorState
          title="No se cargaron los enlaces de pago"
          body="Los cobros registrados se conservan. Reintenta la consulta."
          onRetry={() => void query.refetch()}
        />
      ) : query.data.length === 0 ? (
        <p>No hay enlaces de pago en este proyecto.</p>
      ) : (
        <div className="collection-table">
          <table className="payments-table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Concepto</th>
                <th className="num">Monto CLP</th>
                <th>Vencimiento</th>
                <th>Estado</th>
                <th>Acceso</th>
              </tr>
            </thead>
            <tbody>
              {query.data.map((link) => (
                <tr key={link.id}>
                  <td>
                    <DateOnly value={link.created_at} />
                  </td>
                  <td>
                    {kinds[link.kind]}
                    <p>
                      {link.environment === "simulated"
                        ? "Simulado · sin dinero real"
                        : link.environment === "sandbox"
                          ? "Flow sandbox"
                          : "Flow producción"}
                    </p>
                  </td>
                  <td className="num">
                    <Money value={link.amount} />
                  </td>
                  <td>
                    <DateOnly value={link.expires_at} />
                  </td>
                  <td>
                    <StatusBadge>{states[link.status]}</StatusBadge>
                  </td>
                  <td>
                    {link.url && link.status === "PENDING" && (
                      <a className="ui-button" href={link.url} target="_blank" rel="noreferrer">
                        {link.environment === "simulated" ? "Abrir prueba de pago" : "Abrir pago"}
                      </a>
                    )}
                    {link.url && (
                      <button
                        type="button"
                        onClick={() =>
                          void navigator.clipboard
                            .writeText(link.url!)
                            .then(() => setMessage("Enlace copiado."))
                            .catch(() => setMessage("No se pudo copiar. Usa Abrir pago."))
                        }
                      >
                        Copiar enlace
                      </button>
                    )}
                    {canWrite && ["PENDING", "UNCERTAIN"].includes(link.status) && (
                      <button type="button" disabled={busy} onClick={() => void recover(link.id)}>
                        Verificar pago
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
