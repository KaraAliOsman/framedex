import { Icon } from "./Glyphs";

export type StatusTone =
  "success" | "warning" | "danger" | "info" | "unknown" | "blocked" | "neutral";

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
      <Icon
        kind={
          tone === "success"
            ? "check"
            : tone === "danger"
              ? "stop"
              : tone === "blocked" || tone === "warning"
                ? "warning"
                : "info"
        }
      />
      {label}
    </span>
  );
}
