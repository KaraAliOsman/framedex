import { type PropsWithChildren, type ReactNode } from "react";

import { t } from "../i18n/es-CL";

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
}: {
  title?: string;
  body?: string;
  onRetry?: () => void;
}): JSX.Element {
  return (
    <div className="ui-empty ui-empty--error" role="alert">
      <p className="ui-empty__title">{title ?? t("ui.errorTitle")}</p>
      {body ? <p className="ui-empty__body">{body}</p> : null}
      {onRetry ? (
        <div className="ui-empty__action">
          <button className="ui-button--primary" onClick={onRetry} type="button">
            {t("ui.retry")}
          </button>
        </div>
      ) : null}
    </div>
  );
}

export function Skeleton({ lines = 3 }: { lines?: number }): JSX.Element {
  return (
    <div aria-busy="true" className="ui-skeleton" role="status">
      {Array.from({ length: lines }, (_, index) => (
        <span
          className="ui-skeleton__line"
          key={index}
          style={{ width: `${88 - index * 14}%` }}
        />
      ))}
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
