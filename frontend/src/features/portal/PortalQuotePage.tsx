import { FormEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { ApiError } from "../../api/apiMutator";
import { portalQuoteDecide, portalQuoteRetrieve } from "../../api/generated/dekopen";
import type { PortalPosition, PortalQuote } from "../../api/generated/models";
import { WhiteColorEnum } from "../../api/generated/models";
import type { PositionDesign } from "../../api/generated/models";
import { t } from "../../i18n/es-CL";
import { formatRevision } from "../../format";
import { PositionThumb } from "../projects/PositionThumb";
import "./portal.css";

function money(raw: string, currency: string): string {
  const value = Number(raw);
  if (!Number.isFinite(value)) return raw;
  try {
    return new Intl.NumberFormat("es-CL", {
      style: "currency",
      currency: currency || "CLP",
      maximumFractionDigits: 0,
    }).format(value);
  } catch {
    return `${value.toFixed(0)} ${currency}`;
  }
}

function positionDesign(position: PortalPosition): PositionDesign {
  return {
    system_id: "",
    nominal_width_mm: position.width_mm,
    nominal_height_mm: position.height_mm,
    color: WhiteColorEnum.WHITE,
    parametric_tree: position.parametric_tree,
  };
}

function PositionCard({
  position,
  currency,
}: {
  position: PortalPosition;
  currency: string;
}): JSX.Element {
  const qty = position.quantity ?? 1;
  return (
    <article className="portal-position">
      <div className="portal-position__thumb">
        <PositionThumb design={positionDesign(position)} variant="studio" />
      </div>
      <div className="portal-position__body">
        <p className="portal-position__id">
          {position.location_tag || `Pos. ${position.position_index ?? "—"}`}
        </p>
        <p className="portal-position__typology">{position.typology ?? ""}</p>
        <dl className="portal-position__facts">
          <div>
            <dt>{t("portal.dims")}</dt>
            <dd>
              {Math.round(Number(position.width_mm))} × {Math.round(Number(position.height_mm))} mm
            </dd>
          </div>
          <div>
            <dt>{t("portal.qty")}</dt>
            <dd>{qty}</dd>
          </div>
        </dl>
        <p className="portal-position__price">
          <span>{t("portal.lineNet")}</span>
          <strong>{money(position.price_net, currency)}</strong>
        </p>
      </div>
    </article>
  );
}

export function PortalQuotePage(): JSX.Element {
  const { token = "" } = useParams();
  const [quote, setQuote] = useState<PortalQuote | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const response = await portalQuoteRetrieve(token);
        if (!active) return;
        if (response.status !== 200) {
          setError(response.status === 404 ? t("portal.notFound") : t("portal.loadError"));
          return;
        }
        setQuote(response.data);
      } catch {
        if (active) setError(t("portal.loadError"));
      }
    })();
    return () => {
      active = false;
    };
  }, [token]);

  async function decide(decision: "APPROVED" | "DECLINED"): Promise<void> {
    if (!name.trim() || busy) return;
    if (decision === "DECLINED" && !note.trim()) return;
    setBusy(true);
    try {
      const response = await portalQuoteDecide(token, {
        decision,
        decided_by: name.trim(),
        note: note.trim() || undefined,
      });
      if (response.status !== 200) {
        throw new ApiError(response.status, response.data);
      }
      setQuote(response.data);
    } catch {
      setError(t("portal.decideError"));
    } finally {
      setBusy(false);
    }
  }

  if (error !== null) {
    return (
      <main className="portal-page">
        <section className="portal-card portal-card--narrow">
          <p className="eyebrow">DEKOPEN</p>
          <h1>{t("portal.title")}</h1>
          <p role="alert">{error}</p>
        </section>
      </main>
    );
  }

  if (quote === null) {
    return (
      <main className="portal-page">
        <p role="status">{t("portal.loading")}</p>
      </main>
    );
  }

  const decided = quote.approval_status !== "PENDING";
  const issuer = quote.organization?.name || "DEKOPEN";

  return (
    <main className="portal-page">
      <article className="portal-proposal">
        <header className="portal-proposal__head">
          <div className="portal-proposal__issuer">
            <p className="portal-proposal__org">{issuer}</p>
            {quote.organization?.tax_id ? (
              <p className="portal-proposal__taxid">{quote.organization.tax_id}</p>
            ) : null}
          </div>
          <div className="portal-proposal__refs">
            <h1>{t("portal.proposalTitle")}</h1>
            <p className="portal-proposal__ref">
              {quote.project_name ? `${quote.project_name} · ` : ""}
              {quote.project_code} · {formatRevision(quote.revision_code)} ·{" "}
              <time dateTime={quote.emitted_at}>
                {new Date(quote.emitted_at).toLocaleDateString("es-CL")}
              </time>
            </p>
          </div>
        </header>

        <section className="portal-proposal__summary">
          <dl className="portal-facts">
            <div>
              <dt>{t("portal.client")}</dt>
              <dd>{quote.client_name}</dd>
            </div>
            <div>
              <dt>{t("portal.validUntil")}</dt>
              <dd>
                <time dateTime={quote.valid_until ?? ""}>
                  {quote.valid_until
                    ? new Date(quote.valid_until).toLocaleDateString("es-CL")
                    : "—"}
                </time>
              </dd>
            </div>
          </dl>
          <dl className="portal-totals">
            <div>
              <dt>{t("portal.net")}</dt>
              <dd>{money(quote.total_price_net, quote.currency)}</dd>
            </div>
            <div>
              <dt>{t("portal.tax")}</dt>
              <dd>{money(quote.total_price_tax, quote.currency)}</dd>
            </div>
            <div className="portal-totals__gross">
              <dt>{t("portal.gross")}</dt>
              <dd>{money(quote.total_price_gross, quote.currency)}</dd>
            </div>
          </dl>
        </section>

        {quote.positions.length > 0 ? (
          <section className="portal-proposal__positions">
            <h2>{t("portal.positions")}</h2>
            <div className="portal-positions">
              {quote.positions.map((position, index) => (
                <PositionCard
                  key={position.id || index}
                  position={position}
                  currency={quote.currency}
                />
              ))}
            </div>
          </section>
        ) : null}

        {(quote.payment_terms || quote.payment) && (
          <section className="portal-proposal__commercial">
            {quote.payment_terms ? (
              <div className="portal-terms">
                <h3>{t("portal.terms")}</h3>
                <p>{quote.payment_terms}</p>
              </div>
            ) : null}
            {quote.payment ? (
              <dl className="portal-payment">
                <div>
                  <dt>{t("portal.paymentLabel")}</dt>
                  <dd>
                    <span
                      className={`portal-payment__state portal-payment__state--${quote.payment.status.toLowerCase()}`}
                    >
                      {t(
                        quote.payment.status === "PAID"
                          ? "portal.payment.PAID"
                          : quote.payment.status === "PARTIAL"
                            ? "portal.payment.PARTIAL"
                            : "portal.payment.PENDING",
                      )}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt>{t("portal.collected")}</dt>
                  <dd>{money(quote.payment.collected, quote.currency)}</dd>
                </div>
                <div>
                  <dt>{t("portal.balance")}</dt>
                  <dd>{money(quote.payment.balance, quote.currency)}</dd>
                </div>
              </dl>
            ) : null}
          </section>
        )}

        {quote.quote_pdf_url ? (
          <a
            className="portal-doc"
            href={quote.quote_pdf_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            {t("portal.openPdf")}
          </a>
        ) : null}

        {decided ? (
          <p className="portal-decided" role="status">
            {quote.approval_status === "APPROVED"
              ? t("portal.wasApproved")
              : t("portal.wasDeclined")}{" "}
            {quote.decided_by ? `· ${quote.decided_by}` : ""}
            {quote.decided_note ? ` — ${quote.decided_note}` : ""}
          </p>
        ) : quote.superseded ? (
          <p className="portal-decided" role="status">
            {t("portal.superseded")}
          </p>
        ) : quote.validity_expired ? (
          <p className="portal-decided" role="status">
            {t("portal.validityExpired")}
          </p>
        ) : (
          <form
            className="portal-decision"
            onSubmit={(event: FormEvent<HTMLFormElement>) => {
              event.preventDefault();
              void decide("APPROVED");
            }}
          >
            <label htmlFor="portal-name">{t("portal.nameLabel")}</label>
            <input
              id="portal-name"
              required
              maxLength={255}
              value={name}
              onChange={(event) => setName(event.target.value)}
              disabled={busy}
              autoComplete="name"
            />
            <label htmlFor="portal-note">{t("portal.noteLabel")}</label>
            <textarea
              id="portal-note"
              maxLength={500}
              rows={3}
              value={note}
              onChange={(event) => setNote(event.target.value)}
              disabled={busy}
              placeholder={t("portal.notePlaceholder")}
            />
            <div className="projects-actions">
              <button className="primary-action" disabled={busy || !name.trim()}>
                {t("portal.approve")}
              </button>
              <button
                type="button"
                disabled={busy || !name.trim() || !note.trim()}
                onClick={() => void decide("DECLINED")}
              >
                {t("portal.requestChange")}
              </button>
            </div>
          </form>
        )}

        <footer className="portal-proposal__brand">{t("portal.brand")}</footer>
      </article>
    </main>
  );
}
