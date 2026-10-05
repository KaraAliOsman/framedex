import { type PropsWithChildren, type ReactNode, useEffect, useState } from "react";

import { t } from "../i18n/es-CL";
import { Button } from "./Controls";
import { DimLoader } from "./Signature";

export function EmptyState({
  title,
  body,
  action,
}: {
  title: string;
  body?: string;
  action?: ReactNode;
}): JSX.Element {
  return (
    <div className="ui-empty">
      <p className="ui-empty__title">{title}</p>
      {body ? <p className="ui-empty__body">{body}</p> : null}
      {action ? <div className="ui-empty__action">{action}</div> : null}
    </div>
  );
}

export function ErrorState({
  title,
  body,
  onRetry,
  technical,
}: {
  title?: string;
  body?: string;
  onRetry?: () => void;
  technical?: string;
}): JSX.Element {
  return (
    <div className="ui-empty ui-empty--error" role="alert">
      <p className="ui-empty__title">{title ?? t("ui.errorTitle")}</p>
      {body ? <p className="ui-empty__body">{body}</p> : null}
      <p className="ui-empty__body">
        Revisa la conexión y los datos. Si continúa, comparte los detalles con el dueño de la
        organización.
      </p>
      {technical ? (
        <details className="ui-tech">
          <summary>Detalles técnicos</summary>
          <pre>{technical}</pre>
        </details>
      ) : null}
      {onRetry ? (
        <div className="ui-empty__action">
          <Button variant="primary" onClick={onRetry}>
            {t("ui.retry")}
          </Button>
        </div>
      ) : null}
    </div>
  );
}

/** Permission wall: a role landed on a surface it cannot operate — give the
 * reason, the way out, and a lock glyph instead of a bare alert line on an
 * otherwise empty page (review VM7). */
export function DeniedState({ reason }: { reason: string }): JSX.Element {
  return (
    <div className="ui-empty ui-empty--denied" role="alert">
      <svg className="ui-empty__glyph" aria-hidden="true" viewBox="0 0 16 16">
        <rect x="3" y="7" width="10" height="7" rx="1.5" />
        <path d="M5.5 7V5.5a2.5 2.5 0 0 1 5 0V7" />
      </svg>
      <p className="ui-empty__title">{t("ui.deniedTitle")}</p>
      <p className="ui-empty__body">{reason}</p>
      <div className="ui-empty__action">
        {/* Plain anchor — permission walls render outside the router in unit
         * tests, and a full reload is acceptable on this rare path. */}
        <a className="ui-button" href="/dashboard">
          {t("ui.backToDashboard")}
        </a>
      </div>
    </div>
  );
}

export function Skeleton({ lines = 3 }: { lines?: number }): JSX.Element {
  return (
    <div aria-busy="true" className="ui-skeleton" role="status">
      {Array.from({ length: lines }, (_, index) => (
        <span className="ui-skeleton__line" key={index} style={{ width: `${88 - index * 14}%` }} />
      ))}
    </div>
  );
}

export function LoadingState({
  label = "Cargando los datos",
  shape,
}: {
  label?: string;
  shape?: ReactNode;
}): JSX.Element {
  const [long, setLong] = useState(false);
  useEffect(() => {
    const timer = window.setTimeout(() => setLong(true), 1000);
    return () => clearTimeout(timer);
  }, []);
  return (
    <div className="ui-loading-state" aria-busy="true" aria-label={label} role="status">
      {shape ?? <Skeleton />}
      {long ? <DimLoader label={label} /> : null}
      <span className="ui-visually-hidden">{label}</span>
    </div>
  );
}

export function BlockedState({
  reason,
  action,
}: {
  reason: string;
  action: ReactNode;
}): JSX.Element {
  return (
    <div className="ui-empty ui-empty--blocked" role="status">
      <p className="ui-empty__title">Falta un requisito para continuar</p>
      <p className="ui-empty__body">{reason}</p>
      <div className="ui-empty__action">{action}</div>
    </div>
  );
}

/** Technical banner for blocking/unknown-authority surfaces — a fact plus
 * the action that resolves it, not a decorative alert. */
export function WarningBanner({
  tone = "warning",
  title,
  action,
  children,
}: PropsWithChildren<{
  tone?: "warning" | "danger" | "blocked" | "unknown" | "info";
  title: string;
  action?: ReactNode;
}>): JSX.Element {
  return (
    <div className={`ui-banner ui-banner--${tone}`} role="status">
      <div className="ui-banner__text">
        <p className="ui-banner__title">{title}</p>
        {children ? <div className="ui-banner__body">{children}</div> : null}
      </div>
      {action ? <div className="ui-banner__action">{action}</div> : null}
    </div>
  );
}

/** A compact reference to the evidence/source behind a value — document,
 * page, row, or system of record. */
export function EvidenceChip({ label, title }: { label: string; title?: string }): JSX.Element {
  return (
    <span className="ui-evidence" title={title}>
      {label}
    </span>
  );
}
