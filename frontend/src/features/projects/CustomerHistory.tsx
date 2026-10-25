import { Link } from "react-router-dom";
import { formatCode } from "../../format";
import type { ClientDossierResponse } from "../../api/generated/models";
import { EmptyState, StatusBadge } from "../../ui";
import { formatDate, formatMoney } from "../money";

const statuses: Record<string, string> = {
  DRAFT: "Borrador",
  QUOTED: "Cotizado",
  APPROVED: "Aprobado",
  IN_PRODUCTION: "En producción",
  COMPLETED: "Terminado",
  CANCELLED: "Cancelado",
};

export function CustomerHistory({ history }: { history: ClientDossierResponse }): JSX.Element {
  return (
    <div className="customer-history">
      <section>
        <h3>Cuenta por moneda</h3>
        <p className="customer-hint">
          Origen: acuerdo elegido y pagos vigentes. El motor calcula cada saldo; las monedas se
          muestran por separado.
        </p>
        {history.balances.map((account) => (
          <dl className="customer-account" key={account.currency}>
            <div>
              <dt>Venta · {account.currency}</dt>
              <dd>{formatMoney(account.total, account.currency)}</dd>
            </div>
            <div>
              <dt>Cobrado</dt>
              <dd>{formatMoney(account.collected, account.currency)}</dd>
            </div>
            <div>
              <dt>Saldo</dt>
              <dd>{formatMoney(account.balance, account.currency)}</dd>
            </div>
            {account.simulated_collected !== "0" && (
              <div>
                <dt>Incluye pagos simulados</dt>
                <dd>{formatMoney(account.simulated_collected, account.currency)}</dd>
              </div>
            )}
          </dl>
        ))}
        {history.unknown_projects > 0 && (
          <p>
            Sin importe comercial en {history.unknown_projects} obras. Abre cada obra y aplica el
            precio para completar la cuenta.
          </p>
        )}
        {!history.balances.length && !history.unknown_projects && (
          <p>Sin acuerdos comerciales todavía.</p>
        )}
      </section>
      <section>
        <h3>Obras</h3>
        {history.projects.length ? (
          <ul className="customer-history-list">
            {history.projects.map((project) => (
              <li key={project.id}>
                <Link to={`/projects/${project.id}`}>
                  <strong>
                    {formatCode(project.code, true)} · {project.name}
                  </strong>
                </Link>
                <StatusBadge
                  label={statuses[project.status] ?? "Estado sin registrar"}
                  tone="neutral"
                />
                <span>
                  {project.balance === null
                    ? `Falta completar · ${project.money_cause}`
                    : `Saldo ${formatMoney(project.balance, project.currency ?? "CLP")}${project.simulated ? " · incluye simulación" : ""}`}
                </span>
                <time>{formatDate(project.updated_at)}</time>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            title="Sin obras"
            body="Crea su primer proyecto y elige una dirección de esta ficha."
            action={
              <Link className="ui-button" to={`/projects?create=1&client=${history.client.id}`}>
                Crear proyecto
              </Link>
            }
          />
        )}
      </section>
      <section>
        <h3>Cotizaciones</h3>
        {history.quotations.length ? (
          <ul className="customer-history-list">
            {history.quotations.map((quote) => (
              <li key={quote.version_id}>
                <Link to={`/projects/${quote.project_id}?section=quote`}>
                  {quote.project_code} · {quote.revision_code.replace("REV-", "Revisión ")}
                </Link>
                <span>
                  {quote.total === null
                    ? "Sin importe registrado"
                    : formatMoney(quote.total, quote.currency ?? "CLP")}
                </span>
                {quote.selected && <StatusBadge label="Acuerdo de cobro" tone="success" />}
                <time>{formatDate(quote.emitted_at)}</time>
              </li>
            ))}
          </ul>
        ) : (
          <p>Sin cotizaciones emitidas.</p>
        )}
      </section>
      <section>
        <h3>Pagos</h3>
        {history.payments.length ? (
          <ul className="customer-history-list">
            {history.payments.map((payment) => (
              <li key={payment.id}>
                <Link to={`/projects/${payment.project_id}?section=payments`}>
                  {payment.receipt_code ?? payment.project_code}
                </Link>
                <span>
                  {payment.currency
                    ? formatMoney(payment.amount, payment.currency)
                    : "Moneda por completar · revisa el comprobante"}
                  {payment.simulated ? " · Simulado" : ""}
                </span>
                {payment.voided_at && <StatusBadge label="Anulado" tone="warning" />}
                <time>{formatDate(payment.recorded_at)}</time>
              </li>
            ))}
          </ul>
        ) : (
          <p>Sin pagos registrados.</p>
        )}
      </section>
      <section>
        <h3>Documentos</h3>
        {history.documents.length ? (
          <ul className="customer-history-list">
            {history.documents.map((doc) => (
              <li key={`${doc.kind}-${doc.id}`}>
                <Link
                  to={`/projects/${doc.project_id}?section=${doc.kind === "QUOTE" ? "documents" : "payments"}`}
                >
                  {doc.project_code} · {doc.label.replace(/REV-/u, "Revisión ")}
                </Link>
                <time>{formatDate(doc.created_at)}</time>
              </li>
            ))}
          </ul>
        ) : (
          <p>Sin documentos emitidos.</p>
        )}
      </section>
      <section>
        <h3>Notas y decisiones</h3>
        {history.notes.map((note) => (
          <article className="customer-evidence" key={note.id}>
            <p>{note.body}</p>
            <p className="customer-hint">
              {note.author_label} ·{" "}
              {formatDate(
                note.is_legacy && note.source_updated_at ? note.source_updated_at : note.created_at,
              )}
            </p>
          </article>
        ))}
        {history.merges.map((merge) => (
          <article className="customer-evidence" key={merge.id}>
            <p>
              Fusión: {merge.source_name} → {merge.target_name}
            </p>
            <p>{merge.reason}</p>
            <p className="customer-hint">
              {merge.actor_label} · {formatDate(merge.created_at)}
            </p>
          </article>
        ))}
        {!history.notes.length && !history.merges.length && (
          <p>Sin notas registradas. Cada nueva nota conserva autor y fecha.</p>
        )}
      </section>
    </div>
  );
}
