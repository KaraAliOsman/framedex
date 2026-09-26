import { FormEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { ApiError } from "../../api/apiMutator";
import { portalQuoteDecide, portalQuoteRetrieve } from "../../api/generated/dekopen";
import type { PortalPosition, PortalQuote } from "../../api/generated/models";
import { WhiteColorEnum } from "../../api/generated/models";
import type { PositionDesign } from "../../api/generated/models";
import { t, TranslationKey } from "../../i18n/es-CL";
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

const typologyKeys: Record<string, TranslationKey> = {
  FIXED: "typology.fixed",
  TURN: "typology.turn",
  TILT_TURN: "typology.tiltTurn",
  SLIDING_2L: "typology.sliding2l",
  SLIDING_3L: "typology.sliding3l",
  SLIDING_4L: "typology.sliding4l",
  AWNING: "typology.awning",
  DOOR_ENTRY: "typology.doorEntry",
  COMPOSITE: "typology.composite",
};

function typologyLabel(raw: string | null | undefined): string {
  const key = raw ? typologyKeys[raw] : undefined;
  return key ? t(key) : raw ?? "";
}

/** Identical openings collapse into one proposal card — a 15-unit block of
 * the same window reads as one group with its locations, not fifteen cards. */
function groupPositions(positions: PortalPosition[]): {
  key: string;
  position: PortalPosition;
  locations: string[];
  indexes: string[];
  quantity: number;
  totalNet: number;
}[] {
  const groups = new Map<
    string,
    {
      key: string;
      position: PortalPosition;
      locations: string[];
      indexes: string[];
      quantity: number;
      totalNet: number;
    }
  >();
  for (const position of positions) {
    const key = JSON.stringify([
      position.typology,
      position.width_mm,
      position.height_mm,
      position.color_interior,
      position.color_exterior,
      position.glass_specs,
      position.price_net,
      position.parametric_tree,
    ]);
    const group = groups.get(key);
    const location = position.location_tag?.trim();
    const index = position.position_index != null ? String(position.position_index) : null;
    if (group) {
      if (location && !group.locations.includes(location)) group.locations.push(location);
      if (index) group.indexes.push(index);
      group.quantity += position.quantity ?? 1;
      group.totalNet += Number(position.price_net) || 0;
    } else {
      groups.set(key, {
        key,
        position,
        locations: location ? [location] : [],
        indexes: index ? [index] : [],
        quantity: position.quantity ?? 1,
        totalNet: Number(position.price_net) || 0,
      });
    }
  }
  return [...groups.values()];
}

function PositionGroupCard({
  group,
  currency,
}: {
  group: ReturnType<typeof groupPositions>[number];
  currency: string;
}): JSX.Element {
  const { position } = group;
  const [variant, setVariant] = useState<"studio" | "elevation">("studio");
  const specs = position.glass_specs ?? [];
  const finished = position.finish ?? null;
  const locations =
    group.locations.length > 0
      ? group.locations.join(", ")
      : `Pos. ${group.indexes.join(", ") || "—"}`;
  return (
    <article className="portal-position">
      <div className="portal-position__thumb">
        <PositionThumb design={positionDesign(position)} variant={variant} />
        <div className="portal-position__views" role="group" aria-label={t("portal.views")}>
          <button
            type="button"
            className="portal-view-toggle"
            data-active={variant === "studio"}
            onClick={() => setVariant("studio")}
          >
            {t("portal.viewStudio")}
          </button>
          <button
            type="button"
            className="portal-view-toggle"
            data-active={variant === "elevation"}
            onClick={() => setVariant("elevation")}
          >
            {t("portal.viewTechnical")}
          </button>
        </div>
      </div>
      <div className="portal-position__body">
        <p className="portal-position__id">
          {locations}
          {group.quantity > 1 ? (
            <span className="portal-position__count">×{group.quantity}</span>
          ) : null}
        </p>
        <p className="portal-position__typology">{typologyLabel(position.typology)}</p>
        <dl className="portal-position__facts">
          <div>
            <dt>{t("portal.dims")}</dt>
            <dd>
              {Math.round(Number(position.width_mm))} × {Math.round(Number(position.height_mm))} mm
            </dd>
          </div>
          <div>
            <dt>{t("portal.qty")}</dt>
            <dd>{group.quantity}</dd>
          </div>
          {specs.length > 0 ? (
            <div>
              <dt>{t("portal.glass")}</dt>
              <dd>{specs.join(" · ")}</dd>
            </div>
          ) : null}
          {finished ? (
            <div>
              <dt>{t("portal.finish")}</dt>
              <dd>{finished}</dd>
            </div>
          ) : null}
        </dl>
        <p className="portal-position__price">
          <span>{t("portal.lineNet")}</span>
          <strong>{money(String(group.totalNet), currency)}</strong>
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
              {groupPositions(quote.positions).map((group) => (
                <PositionGroupCard key={group.key} group={group} currency={quote.currency} />
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
