import { useCallback, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { ApiError } from "../../api/apiMutator";
import {
  portalQuoteDecide,
  portalQuotePay,
  portalQuoteRetrieve,
  portalPaymentReturn,
} from "../../api/generated/dekopen";
import type {
  CommercialTerms,
  PortalOption,
  PortalOrganization,
  PortalQuote,
} from "../../api/generated/models";
import { applyAppBrand } from "../../brand/head";
import { formatCode, formatDate, formatDateTime, formatRevision, isValidRut } from "../../format";
import { DemoBadge, Loading, Money, StatusBadge, UnknownValue, ValidatedForm } from "../../ui";
import { actionErrorDetail } from "../errors";
import { ProposalDrawing, ProposalThumb } from "./proposalDrawing";
import "./portal.css";

type Decision = "APPROVED" | "CHANGES_REQUESTED" | "DECLINED";
type Failure = { code: string; detail: string; organization?: PortalOrganization };
const titles: Record<string, string> = {
  APPROVED: "Propuesta aprobada",
  CHANGES_REQUESTED: "Cambios solicitados",
  DECLINED: "Propuesta rechazada",
  PENDING: "Propuesta vigente",
};

function Issuer({ organization }: { organization?: PortalOrganization }): JSX.Element {
  const name = organization?.commercial_name || organization?.name || "Emisor sin identificar";
  return (
    <div className="portal-issuer">
      {organization?.brand_logo_url && (
        <img src={organization.brand_logo_url} alt="Logo del fabricante" width={160} height={48} />
      )}
      <p className="portal-issuer-name">{name}</p>
      {organization?.tax_id && <p className="technical-number">{organization.tax_id}</p>}
      <Contact organization={organization} />
    </div>
  );
}
function Contact({ organization }: { organization?: PortalOrganization }): JSX.Element {
  return (
    <address className="portal-contact">
      {organization?.brand_address && <span>{organization.brand_address}</span>}
      {organization?.brand_phone && (
        <a href={`tel:${organization.brand_phone.replace(/[^+\d]/g, "")}`}>
          {organization.brand_phone}
        </a>
      )}
      {organization?.brand_email && (
        <a href={`mailto:${organization.brand_email}`}>{organization.brand_email}</a>
      )}
      {!organization?.brand_phone && !organization?.brand_email && (
        <span>Contacte al fabricante que le envió este enlace.</span>
      )}
    </address>
  );
}
function useProposalHead(organization?: PortalOrganization, code?: string): void {
  useEffect(() => {
    const previousPortal = document.body.dataset.portalDocument;
    document.body.dataset.portalDocument = "true";
    const title = document.title;
    const icons = [
      ...document.querySelectorAll<HTMLLinkElement>(
        'link[rel="icon"],link[rel="apple-touch-icon"],link[rel="manifest"]',
      ),
    ];
    const saved = icons.map((link) => ({
      link,
      href: link.getAttribute("href"),
      type: link.getAttribute("type"),
    }));
    const issuer = organization?.commercial_name || organization?.name;
    document.title = [issuer, "Cotización", code].filter(Boolean).join(" · ");
    for (const link of icons) {
      if (link.rel === "manifest") link.removeAttribute("href");
      else {
        link.setAttribute("href", organization?.brand_logo_url || "/portal-favicon.svg");
        link.removeAttribute("type");
      }
    }
    return () => {
      if (previousPortal) document.body.dataset.portalDocument = previousPortal;
      else delete document.body.dataset.portalDocument;
      document.title = title;
      for (const { link, href, type } of saved) {
        if (href) link.setAttribute("href", href);
        else link.removeAttribute("href");
        if (type) link.setAttribute("type", type);
        else link.removeAttribute("type");
      }
      applyAppBrand(document.documentElement.dataset.theme === "dark" ? "dark" : "light");
    };
  }, [organization, code]);
}
function PriceSource({ option }: { option: PortalOption }): JSX.Element {
  return (
    <details className="portal-price-source">
      <summary>¿De dónde sale el precio?</summary>
      <p>{option.price_source}</p>
      <p>
        Los precios unitarios y de línea incluyen el impuesto de la cotización. Los ajustes se
        muestran por separado para conservar el total de la revisión.
      </p>
      <details>
        <summary>Detalles técnicos</summary>
        <p>{formatRevision(option.revision_code)}</p>
        <code>{option.snapshot_sha256}</code>
      </details>
    </details>
  );
}
function ProposalState({ quote }: { quote: PortalQuote }): JSX.Element {
  return (
    <section className="portal-state" aria-label="Estado de la propuesta">
      <StatusBadge data-status={quote.approval_status.toLowerCase()}>
        {titles[quote.approval_status] || "Estado por completar"}
      </StatusBadge>
      {quote.decided_at && (
        <p>
          Decisión registrada el{" "}
          <time dateTime={quote.decided_at}>{formatDateTime(quote.decided_at)}</time> ·{" "}
          {formatRevision(quote.selected_revision || quote.revision_code)}.
        </p>
      )}
      {quote.approval_status === "APPROVED" ? (
        <p>
          El fabricante se contactará con usted para coordinar la medición final y el anticipo. La
          solución aceptada conserva sus condiciones.
        </p>
      ) : quote.approval_status === "CHANGES_REQUESTED" ? (
        <p>
          El fabricante revisará su comentario y preparará una nueva propuesta. Este enlace conserva
          su solicitud; no se iniciará un pago.
        </p>
      ) : quote.approval_status === "DECLINED" ? (
        <p>Su rechazo quedó registrado. Si necesita otra propuesta, contacte al fabricante.</p>
      ) : (
        <p>Revise las ventanas, el importe y las condiciones antes de aceptar.</p>
      )}
    </section>
  );
}
function Conditions({ option }: { option: PortalOption }): JSX.Element {
  const terms = (option.commercial_terms ?? {}) as CommercialTerms;
  return (
    <section className="portal-section" aria-label="Condiciones y documentos">
      <h2>Condiciones y documentos</h2>
      <div className="portal-conditions">
        <div>
          <h3>Calendario de pagos</h3>
          {option.payment_schedule.length ? (
            <ol className="portal-schedule">
              {option.payment_schedule.map((item, i) => (
                <li key={i}>
                  <strong>{String(item.label ?? "Hito sin nombre")}</strong>
                  <Money
                    value={typeof item.amount === "string" ? item.amount : null}
                    currency={option.currency}
                  />
                  <span>
                    {item.due_on
                      ? formatDate(String(item.due_on))
                      : item.due_event === "APPROVAL"
                        ? "Al aprobar"
                        : item.due_event === "DELIVERY"
                          ? "Contra entrega completa con comprobante"
                          : "Sin fecha declarada · acuerde el vencimiento con el fabricante"}
                  </span>
                </li>
              ))}
            </ol>
          ) : (
            <p>
              {option.payment_terms ||
                "Falta completar · el fabricante debe declarar el calendario de pagos."}
            </p>
          )}
        </div>
        {(() => {
          const conditions = (
            [
              ["delivery_text", "Plazo de entrega"],
              ["installation_text", "Instalación"],
              ["exclusions", "Exclusiones"],
              ["warranty", "Garantía"],
              ["jurisdiction", "Jurisdicción"],
            ] as const
          ).map(([key, label]) => ({ key, label, value: terms[key] }));
          const declared = conditions.filter((condition) => condition.value);
          const missing = conditions.filter((condition) => !condition.value);
          // Undeclared terms read as one sentence instead of five «Sin dato» rows.
          return (
            <dl>
              {declared.map(({ key, label, value }) => (
                <div key={key}>
                  <dt>{label}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
              {missing.length ? (
                <div className="portal-conditions-missing">
                  <dt>Sin declarar</dt>
                  <dd>
                    <UnknownValue
                      cause={`${missing.map((condition) => condition.label).join(", ")} · contacte al fabricante antes de aceptar`}
                    />
                  </dd>
                </div>
              ) : null}
            </dl>
          );
        })()}
      </div>
      {option.notes_commercial && <p className="portal-note">{option.notes_commercial}</p>}
      {option.quote_pdf_url ? (
        <a
          className="portal-document-link"
          href={option.quote_pdf_url}
          target="_blank"
          rel="noopener noreferrer"
        >
          Descargar cotización · {formatRevision(option.revision_code)}
        </a>
      ) : (
        <p>Sin PDF disponible · solicite al fabricante el documento de esta opción.</p>
      )}
    </section>
  );
}
function PortalPayment({
  quote,
  token,
  onRefresh,
}: {
  quote: PortalQuote;
  token: string;
  onRefresh: () => Promise<void>;
}): JSX.Element {
  const payableInput = (quote.payment?.balance ?? "").replace(/\.0+$/, "");
  const [amount, setAmount] = useState(payableInput);
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [operationKey] = useState(() => crypto.randomUUID());
  useEffect(() => setAmount(payableInput), [payableInput]);
  const [search] = useSearchParams();
  const context = search.get("pago") ?? "";
  const access = search.get("access") ?? "";
  const returning = Boolean(context && context !== "retorno" && access);
  const result = useQuery({
    queryKey: ["proposal-payment-return", context, access],
    enabled: returning,
    retry: false,
    refetchInterval: (query) =>
      ["DISPATCHING", "PENDING", "UNCERTAIN"].includes(query.state.data?.status ?? "")
        ? 10000
        : false,
    queryFn: async () => {
      const response = await portalPaymentReturn(context, { access });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      if (!response.data.portal_path.startsWith(`/cotizacion/${token}?`))
        throw new Error("El resultado pertenece a otro enlace del fabricante.");
      return response.data;
    },
  });
  useEffect(() => {
    if (result.data?.status === "PAID") void onRefresh();
  }, [result.data?.status, onRefresh]);
  const paymentStates: Record<string, string> = {
    PAID: result.data?.simulated
      ? "Pago de prueba registrado; no se transfirió dinero."
      : "Pago confirmado y registrado.",
    FAILED: "El pago fue rechazado. El saldo no se descontó.",
    CANCELLED: "El cobro fue cancelado. El saldo no se descontó.",
    DISPATCHING: "El proveedor está preparando el cobro; todavía no hay un pago registrado.",
    PENDING: "El proveedor aún no confirma el pago. Consultaremos nuevamente su resultado.",
    UNCERTAIN: "La confirmación sigue en consulta. No repita el pago hasta verificar su resultado.",
  };
  return (
    <section className="portal-section" aria-label="Pago de la propuesta">
      <h2>Pago de la propuesta</h2>
      {returning && (
        <p role="status">
          {result.isPending
            ? "Consultando el resultado del pago…"
            : result.isError
              ? "No se pudo verificar el resultado. Contacte al fabricante antes de repetir el pago."
              : (paymentStates[result.data.status] ??
                "Estado del proveedor por completar. Contacte al fabricante.")}
        </p>
      )}
      {quote.payment ? (
        <dl className="portal-payment-ledger">
          <div>
            <dt>Registrado</dt>
            <dd>
              <Money value={quote.payment.collected} currency={quote.currency} />
            </dd>
          </div>
          <div>
            <dt>Saldo</dt>
            <dd>
              <Money value={quote.payment.balance} currency={quote.currency} />
            </dd>
          </div>
        </dl>
      ) : (
        <UnknownValue cause="No se pudo establecer un saldo; contacte al fabricante" />
      )}
      {quote.payment?.simulated && (
        <p>El saldo incluye movimientos de prueba, sin dinero transferido.</p>
      )}
      {quote.payment_provider && quote.payment_url ? (
        <div className="portal-pending-payment">
          {quote.payment_provider === "SIMULATED" && (
            <StatusBadge tone="neutral">Modo de prueba</StatusBadge>
          )}
          <p>
            Ya hay un cobro preparado para esta propuesta. Continúe el mismo pago para evitar
            duplicarlo.
          </p>
          <a className="primary-action portal-document-link" href={quote.payment_url}>
            Continuar pago pendiente
          </a>
        </div>
      ) : (
        quote.payment_provider && (
          <ValidatedForm
            className="portal-pay-form"
            onSubmit={async (event) => {
              event.preventDefault();
              if (busy) return;
              if (!/^\d+$/.test(amount) || !/[\w.+-]+@[^\s@]+\.[^\s@]+/.test(email)) {
                setMessage("Indique un monto CLP entero positivo y su correo para el comprobante.");
                return;
              }
              setBusy(true);
              setMessage("");
              try {
                const result = await portalQuotePay(token, {
                  amount,
                  payer_email: email.trim(),
                  operation_key: operationKey,
                });
                if (result.status !== 200) throw new ApiError(result.status, result.data);
                window.location.assign(result.data.url);
              } catch (error) {
                setMessage(
                  actionErrorDetail(
                    error,
                    "No se pudo preparar el cobro. Revise el saldo y vuelva a intentar.",
                  ),
                );
                await onRefresh();
              } finally {
                setBusy(false);
              }
            }}
          >
            {quote.payment_provider === "SIMULATED" && (
              <StatusBadge tone="neutral">Modo de prueba</StatusBadge>
            )}
            <label htmlFor="portal-pay-amount">Monto a pagar (CLP)</label>
            <input
              id="portal-pay-amount"
              inputMode="numeric"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              disabled={busy}
            />
            <p>
              El monto no puede superar el saldo de{" "}
              <Money value={quote.payment?.balance} currency={quote.currency} />.
            </p>
            <label htmlFor="portal-pay-email">Correo para el comprobante</label>
            <input
              id="portal-pay-email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={busy}
            />
            <button type="submit" className="primary-action" disabled={busy}>
              {busy
                ? "Preparando cobro…"
                : quote.payment_provider === "SIMULATED"
                  ? "Pagar en modo de prueba"
                  : "Pagar con Flow"}
            </button>
            {message && <p role="alert">{message}</p>}
          </ValidatedForm>
        )
      )}
    </section>
  );
}

export function PortalQuotePage(): JSX.Element {
  const { token = "" } = useParams();
  const [quote, setQuote] = useState<PortalQuote | null>(null);
  const [failure, setFailure] = useState<Failure | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState("");
  const [name, setName] = useState("");
  const [rut, setRut] = useState("");
  const [note, setNote] = useState("");
  const [position, setPosition] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [fields, setFields] = useState<Record<string, string>>({});
  const load = useCallback(async () => {
    try {
      const result = await portalQuoteRetrieve(token);
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      setQuote(result.data);
      setFailure(null);
      setSelected((current) =>
        result.data.approval_status === "PENDING" &&
        result.data.options?.some((o) => o.revision_code === current)
          ? current
          : result.data.selected_revision || result.data.revision_code,
      );
    } catch (error) {
      const payload = (error instanceof ApiError ? error.payload : null) as {
        error?: { code?: string; detail?: string; organization?: PortalOrganization };
      } | null;
      setFailure({
        code: payload?.error?.code || "connection",
        detail:
          payload?.error?.detail ||
          "No se pudo consultar la cotización. Revise su conexión y vuelva a intentar.",
        organization: payload?.error?.organization,
      });
    } finally {
      setLoading(false);
    }
  }, [token]);
  useEffect(() => {
    setLoading(true);
    setQuote(null);
    setSelected("");
    void load();
  }, [load]);
  useProposalHead(quote?.organization ?? failure?.organization, quote?.project_code);
  const fallback: PortalOption | null = quote
    ? {
        revision_code: quote.selected_revision || quote.revision_code,
        snapshot_sha256: quote.offering_sha256 || "",
        currency: quote.currency,
        total_price_gross: quote.total_price_gross,
        display_total_gross: quote.display_total_gross ?? null,
        rounding_adjustment: quote.rounding_adjustment ?? null,
        price_cause:
          quote.price_cause ??
          "Esta revisión histórica necesita una proyección comercial nueva; contacte al fabricante.",
        price_source: quote.price_source || "Revisión emitida",
        consent_text: quote.consent_text ?? null,
        positions: quote.positions,
        extras: quote.extras,
        payment_schedule: quote.payment_schedule ?? [],
        commercial_terms: quote.commercial_terms,
        quote_pdf_url: quote.quote_pdf_url,
        payment_terms: quote.payment_terms,
        notes_commercial: quote.notes_commercial,
      }
    : null;
  const option = quote?.options?.find((o) => o.revision_code === selected) ?? fallback;
  async function decide(decision: Decision): Promise<void> {
    if (!quote || !option || busy) return;
    const errors: Record<string, string> = {};
    if (decision === "APPROVED") {
      if (!name.trim()) errors.name = "Indique su nombre completo.";
      if (!rut.trim() || !isValidRut(rut))
        errors.rut = "Ingrese un RUT válido, con dígito verificador.";
      if (!confirmed)
        errors.confirmed = "Marque la aceptación de esta propuesta y sus condiciones.";
    }
    if (decision === "CHANGES_REQUESTED" && !note.trim())
      errors.note = "Describa el cambio que necesita.";
    setFields(errors);
    if (Object.keys(errors).length) return;
    setBusy(true);
    setError("");
    try {
      const result = await portalQuoteDecide(token, {
        decision,
        decided_by: name.trim(),
        decided_rut: rut.trim(),
        note: note.trim(),
        selected_revision: option.revision_code,
        expected_offering_sha256: quote.offering_sha256 || "",
        expected_selected_sha256: option.snapshot_sha256,
        confirmed,
        consent_text: option.consent_text ?? "",
        position_id: position || null,
      });
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      setQuote(result.data);
      setSelected(result.data.selected_revision || result.data.revision_code);
      setConfirmed(false);
    } catch (error) {
      setError(
        actionErrorDetail(
          error,
          "No se registró la decisión. Revise los datos y vuelva a intentar.",
        ),
      );
      if (error instanceof ApiError && (error.status === 409 || error.status === 410)) {
        setConfirmed(false);
        await load();
      }
    } finally {
      setBusy(false);
    }
  }
  if (loading)
    return (
      <main className="portal-page" data-density="document">
        <section className="portal-card portal-card--narrow">
          <h1>Consultando su cotización</h1>
          <Loading label="Consultando la propuesta emitida" />
        </section>
      </main>
    );
  if (failure) {
    const title =
      failure.code === "quote_revoked"
        ? "Enlace revocado"
        : failure.code === "quote_expired"
          ? "Enlace vencido"
          : failure.code === "quote_not_found"
            ? "Cotización no encontrada"
            : "No se pudo consultar la cotización";
    return (
      <main className="portal-page" data-density="document">
        <article className="portal-card portal-card--narrow">
          <Issuer organization={failure.organization} />
          <h1>{title}</h1>
          <p role="alert">{failure.detail}</p>
          <p>
            {failure.code === "quote_not_found"
              ? "Revise que el enlace esté completo o solicite al fabricante el enlace de su propuesta."
              : "Solicite al fabricante un enlace vigente para continuar."}
          </p>
          {failure.code === "connection" && (
            <button
              type="button"
              onClick={() => {
                setLoading(true);
                void load();
              }}
            >
              Reintentar consulta
            </button>
          )}
        </article>
      </main>
    );
  }
  if (!quote || !option)
    return (
      <main className="portal-page" data-density="document">
        <h1>Sin propuesta disponible</h1>
        <p>Solicite al fabricante una cotización emitida.</p>
      </main>
    );
  if (quote.superseded || quote.validity_expired)
    return (
      <main className="portal-page" data-density="document">
        <article className="portal-card portal-card--narrow">
          <Issuer organization={quote.organization} />
          <h1>{quote.superseded ? "Cotización reemplazada" : "Cotización vencida"}</h1>
          <p>
            {quote.superseded
              ? "Esta cotización fue reemplazada por una revisión nueva."
              : "La vigencia de esta propuesta terminó. El fabricante debe emitir una cotización nueva."}
          </p>
          <p>
            {quote.project_name} · {formatCode(quote.project_code)} ·{" "}
            {formatRevision(quote.revision_code)}
          </p>
          {quote.approval_status !== "PENDING" && <ProposalState quote={quote} />}
          <Contact organization={quote.organization} />
          {quote.successor_path && quote.superseded && (
            <Link className="portal-document-link" to={quote.successor_path}>
              Consultar propuesta vigente
            </Link>
          )}
        </article>
      </main>
    );
  const pending = quote.approval_status === "PENDING";
  return (
    <main className="portal-page" data-density="document">
      <article className="portal-proposal">
        <header className="portal-proposal-head">
          <Issuer organization={quote.organization} />
          <div>
            <p className="portal-kicker">Cotización {formatCode(quote.project_code)}</p>
            <h1>{quote.project_name || "Su obra"}</h1>
            <p>
              Para {quote.client_name || "cliente sin identificar"} · Oferta ·{" "}
              {formatRevision(quote.revision_code)}
            </p>
            <p>
              Oferta emitida el{" "}
              <time dateTime={quote.emitted_at}>{formatDate(quote.emitted_at)}</time>
            </p>
          </div>
        </header>
        <section className="portal-summary" aria-label="Resumen de la propuesta">
          <div>
            <h2>
              {option.revision_code !== quote.revision_code ? "Solución elegida · " : ""}
              {formatRevision(option.revision_code)}
            </h2>
            <p>
              {quote.valid_until ? (
                <>
                  Válida hasta{" "}
                  <time dateTime={quote.valid_until}>{formatDate(quote.valid_until)}</time>
                  {quote.validity_days != null ? ` · quedan ${quote.validity_days} días` : ""}
                </>
              ) : (
                <UnknownValue cause="El fabricante no declaró la vigencia" />
              )}
            </p>
          </div>
          <div>
            <p>Total IVA incluido</p>
            <p className="portal-total">
              <Money
                value={option.display_total_gross}
                currency={option.currency}
                cause={option.price_cause ?? undefined}
              />
            </p>
          </div>
        </section>
        <ProposalState quote={quote} />
        {quote.options && quote.options.length > 1 && (
          <section className="portal-section" aria-label="Comparar alternativas">
            <h2>Compare y elija su solución</h2>
            <p>
              Las alternativas son revisiones emitidas completas. La aprobación, los cobros y la
              fabricación usarán la solución que usted elija.
            </p>
            <div className="portal-options">
              {quote.options.map((candidate) => (
                <article
                  className="portal-option"
                  key={candidate.revision_code}
                  data-selected={candidate.revision_code === selected}
                >
                  <h3>
                    {formatRevision(candidate.revision_code)}
                    {candidate.revision_code === quote.revision_code
                      ? " · Propuesta principal"
                      : " · Alternativa"}
                  </h3>
                  {Boolean(candidate.positions[0]?.parametric_tree) && (
                    <>
                      <ProposalThumb position={candidate.positions[0]!} />
                      <p>Vista interior</p>
                    </>
                  )}
                  <p>
                    {candidate.positions[0]?.system_name || "Serie de la cotización"} ·{" "}
                    {candidate.positions[0]?.finish || "Acabado por completar"}
                  </p>
                  <p>{candidate.positions.length} ventanas</p>
                  <p>
                    <Money value={candidate.display_total_gross} currency={candidate.currency} />{" "}
                    IVA incluido
                  </p>
                  {pending ? (
                    <button
                      type="button"
                      aria-pressed={candidate.revision_code === selected}
                      disabled={busy}
                      onClick={() => {
                        setSelected(candidate.revision_code);
                        setPosition("");
                        setConfirmed(false);
                        setFields({});
                      }}
                    >
                      {candidate.revision_code === selected
                        ? "Opción elegida"
                        : "Elegir esta opción"}
                    </button>
                  ) : (
                    candidate.revision_code === selected && (
                      <StatusBadge tone="success">Solución aceptada</StatusBadge>
                    )
                  )}
                </article>
              ))}
            </div>
          </section>
        )}
        {option.price_cause && (
          <p className="portal-blocked" role="status">
            {option.price_cause}
          </p>
        )}
        <section className="portal-section" aria-label="Ventanas de la solución">
          <h2>Lo que usted compra</h2>
          <p>{formatRevision(option.revision_code)} · precios unitarios y de línea IVA incluido.</p>
          <div className="portal-positions">
            {option.positions.map((p) => (
              <article className="portal-position" key={p.id} id={`posicion-${p.position_index}`}>
                <header>
                  <h3>
                    Ventana {p.position_index} · {p.location_tag || "Ubicación sin declarar"}
                  </h3>
                  {p.is_demo && (
                    <DemoBadge source="Catálogo sintético; sin certificación técnica" />
                  )}
                </header>
                <div className="portal-position-body">
                  <ProposalDrawing position={p} />
                  <div className="portal-position-spec">
                    <dl>
                      <div>
                        <dt>Serie</dt>
                        <dd>
                          {p.system_name || (
                            <UnknownValue cause="No consta la serie en la revisión" />
                          )}
                        </dd>
                      </div>
                      <div>
                        <dt>Cantidad</dt>
                        <dd className="technical-number">{p.quantity ?? "Falta completar"}</dd>
                      </div>
                      <div>
                        <dt>Vidrio</dt>
                        <dd>
                          {p.glass_specs.join(" · ") || (
                            <UnknownValue cause="No se declaró vidrio en esta ventana" />
                          )}
                        </dd>
                      </div>
                      <div>
                        <dt>Acabado</dt>
                        <dd>
                          {p.finish || (
                            <UnknownValue cause="No se declaró acabado en esta ventana" />
                          )}
                        </dd>
                      </div>
                      {p.commercial_hardware?.map((hardware, i) => (
                        <div key={i}>
                          <dt>Manilla y herrajes</dt>
                          <dd>
                            {[hardware.handle_name, hardware.handle_color, ...hardware.options]
                              .filter(Boolean)
                              .join(" · ") || "Sin manilla de accionamiento"}
                          </dd>
                        </div>
                      ))}
                    </dl>
                    <dl className="portal-position-prices">
                      <div>
                        <dt>Precio unitario</dt>
                        <dd>
                          <Money value={p.unit_price_gross} currency={option.currency} />
                        </dd>
                      </div>
                      <div>
                        <dt>Total de línea</dt>
                        <dd>
                          <Money value={p.line_price_gross} currency={option.currency} />
                        </dd>
                      </div>
                    </dl>
                    {p.unit_rounding_adjustment && Number(p.unit_rounding_adjustment) !== 0 && (
                      <p>
                        Ajuste por cantidad y redondeo:{" "}
                        <Money value={p.unit_rounding_adjustment} currency={option.currency} />. Ya
                        está incluido en el total de línea.
                      </p>
                    )}
                    {pending && (
                      <button
                        type="button"
                        onClick={() => {
                          setPosition(p.id);
                          document.getElementById("portal-note")?.focus();
                        }}
                      >
                        Solicitar cambio en ventana {p.position_index}
                      </button>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
          {!option.positions.length && (
            <p>
              Sin ventanas · solicite al fabricante una propuesta con el detalle de las ventanas.
            </p>
          )}
        </section>
        {option.extras.length > 0 && (
          <section className="portal-section">
            <h2>Servicios y cargos declarados</h2>
            <dl className="portal-extra-lines">
              {option.extras.map((item, i) => (
                <div key={i}>
                  <dt>
                    {String(item.label ?? "Servicio")} {Boolean(item.synthetic) && <DemoBadge />}
                  </dt>
                  <dd>
                    <Money
                      value={
                        typeof item.line_price_gross === "string" ? item.line_price_gross : null
                      }
                      currency={option.currency}
                    />
                  </dd>
                </div>
              ))}
            </dl>
          </section>
        )}
        {option.rounding_adjustment && Number(option.rounding_adjustment) !== 0 && (
          <p>
            Ajuste de moneda:{" "}
            <Money value={option.rounding_adjustment} currency={option.currency} />. La suma de
            ventanas, servicios, cargos y este ajuste conserva el total emitido.
          </p>
        )}
        <PriceSource option={option} />
        <Conditions option={option} />
        {pending ? (
          <section className="portal-section portal-decision-region" aria-label="Decidir propuesta">
            <h2>Su decisión</h2>
            <ValidatedForm
              className="portal-decision"
              onSubmit={(e) => {
                e.preventDefault();
                void decide("APPROVED");
              }}
            >
              <p>
                {formatRevision(option.revision_code)} ·{" "}
                <Money value={option.display_total_gross} currency={option.currency} /> IVA incluido
              </p>
              <label htmlFor="portal-name">Nombre completo</label>
              <input
                id="portal-name"
                maxLength={255}
                autoComplete="name"
                value={name}
                disabled={busy}
                onChange={(e) => setName(e.target.value)}
                aria-invalid={Boolean(fields.name)}
                aria-describedby={fields.name ? "portal-name-error" : undefined}
              />
              {fields.name && (
                <p id="portal-name-error" role="alert">
                  {fields.name}
                </p>
              )}
              <label htmlFor="portal-rut">RUT</label>
              <input
                id="portal-rut"
                maxLength={32}
                autoComplete="off"
                value={rut}
                disabled={busy}
                onChange={(e) => setRut(e.target.value)}
                aria-invalid={Boolean(fields.rut)}
                aria-describedby={fields.rut ? "portal-rut-error" : undefined}
              />
              {fields.rut && (
                <p id="portal-rut-error" role="alert">
                  {fields.rut}
                </p>
              )}
              <label className="portal-consent">
                <input
                  type="checkbox"
                  checked={confirmed}
                  disabled={busy || !option.consent_text}
                  onChange={(e) => setConfirmed(e.target.checked)}
                />
                <span>
                  {option.consent_text ||
                    "La aceptación requiere un importe y condiciones completos del fabricante."}
                </span>
              </label>
              {fields.confirmed && <p role="alert">{fields.confirmed}</p>}
              <p>
                Su nombre, RUT, fecha, IP y navegador se conservarán como evidencia de esta
                decisión, junto con la revisión y su huella. El fabricante podrá consultarla; no se
                publicará en este enlace.
              </p>
              <button
                type="submit"
                className="primary-action"
                disabled={busy || Boolean(option.price_cause) || !option.consent_text}
              >
                {busy ? "Registrando decisión…" : "Aprobar propuesta"}
              </button>
              <hr />
              <h3>Cambios o rechazo</h3>
              <label htmlFor="portal-position">Ventana a revisar (opcional)</label>
              <select
                id="portal-position"
                value={position}
                disabled={busy}
                onChange={(e) => setPosition(e.target.value)}
              >
                <option value="">Propuesta completa</option>
                {option.positions.map((p) => (
                  <option key={p.id} value={p.id}>
                    Ventana {p.position_index} · {p.location_tag || "Sin ubicación"}
                  </option>
                ))}
              </select>
              <label htmlFor="portal-note">Comentario</label>
              <textarea
                id="portal-note"
                maxLength={500}
                rows={3}
                value={note}
                disabled={busy}
                onChange={(e) => setNote(e.target.value)}
                aria-invalid={Boolean(fields.note)}
                aria-describedby="portal-note-help"
              />
              <p id="portal-note-help">Obligatorio para solicitar cambios; opcional al rechazar.</p>
              {fields.note && <p role="alert">{fields.note}</p>}
              <div className="portal-secondary-decisions">
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void decide("CHANGES_REQUESTED")}
                >
                  Solicitar cambios
                </button>
                <button type="button" disabled={busy} onClick={() => void decide("DECLINED")}>
                  Rechazar propuesta
                </button>
              </div>
              {error && <p role="alert">{error}</p>}
            </ValidatedForm>
          </section>
        ) : (
          quote.approval_status === "APPROVED" && (
            <PortalPayment quote={quote} token={token} onRefresh={load} />
          )
        )}
        <footer className="portal-footer">
          <Contact organization={quote.organization} />
          {quote.organization.portal_attribution === true && <p>Generado con DEKOPEN</p>}
        </footer>
      </article>
    </main>
  );
}
