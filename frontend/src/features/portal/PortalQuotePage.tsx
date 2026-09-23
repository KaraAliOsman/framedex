import { FormEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { ApiError } from "../../api/apiMutator";
import { portalQuoteDecide, portalQuoteRetrieve } from "../../api/generated/dekopen";
import type { PortalQuote } from "../../api/generated/models";
import { t } from "../../i18n/es-CL";

function money(raw: string): string {
  const value = Number(raw);
  if (!Number.isFinite(value)) return raw;
  return new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    maximumFractionDigits: 0,
  }).format(value);
}

export function PortalQuotePage(): JSX.Element {
  const { token = "" } = useParams();
  const [quote, setQuote] = useState<PortalQuote | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
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
    setBusy(true);
    try {
      const response = await portalQuoteDecide(token, {
        decision,
        decided_by: name.trim(),
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
        <section className="portal-card">
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

  return (
    <main className="portal-page">
      <section className="portal-card">
        <p className="eyebrow">DEKOPEN · {quote.revision_code}</p>
        <h1>{t("portal.title")}</h1>
        <dl className="portal-facts">
          <div>
            <dt>{t("portal.project")}</dt>
            <dd>
              {quote.project_code} · {quote.project_name}
            </dd>
          </div>
          <div>
            <dt>{t("portal.client")}</dt>
            <dd>{quote.client_name}</dd>
          </div>
          <div>
            <dt>{t("portal.emitted")}</dt>
            <dd>
              <time dateTime={quote.emitted_at}>
                {new Date(quote.emitted_at).toLocaleDateString("es-CL")}
              </time>
            </dd>
          </div>
          <div>
            <dt>{t("portal.net")}</dt>
            <dd>{money(quote.total_price_net)}</dd>
          </div>
          <div>
            <dt>{t("portal.tax")}</dt>
            <dd>{money(quote.total_price_tax)}</dd>
          </div>
          <div>
            <dt>{t("portal.gross")}</dt>
            <dd>
              <strong>{money(quote.total_price_gross)}</strong>
            </dd>
          </div>
          <div>
            <dt>{t("portal.validUntil")}</dt>
            <dd>
              <time dateTime={quote.expires_at}>
                {new Date(quote.expires_at).toLocaleDateString("es-CL")}
              </time>
            </dd>
          </div>
        </dl>

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
            <div className="projects-actions">
              <button className="primary-action" disabled={busy || !name.trim()}>
                {t("portal.approve")}
              </button>
              <button
                type="button"
                disabled={busy || !name.trim()}
                onClick={() => void decide("DECLINED")}
              >
                {t("portal.decline")}
              </button>
            </div>
          </form>
        )}
      </section>
    </main>
  );
}
