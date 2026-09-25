export type StatusTone =
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "unknown"
  | "blocked"
  | "neutral";

export function StatusBadge({
  tone = "neutral",
  label,
  title,
}: {
  tone?: StatusTone;
  label: string;
  title?: string;
}): JSX.Element {
  return (
    <span className={`ui-badge ui-badge--${tone}`} title={title}>
      <span aria-hidden className="ui-badge__dot" />
      {label}
    </span>
  );
}
