import { Icon } from "./Glyphs";
import type { HTMLAttributes, ReactNode } from "react";

export type StatusTone =
  "success" | "warning" | "danger" | "info" | "unknown" | "blocked" | "neutral" | "person";

export function statusTone(code: string | undefined): StatusTone {
  const state = code?.toLowerCase().replaceAll("_", "-");
  if (!state) return "neutral";
  if (
    ["success", "warning", "danger", "info", "unknown", "blocked", "neutral", "person"].includes(
      state,
    )
  )
    return state as StatusTone;
  if (
    [
      "done",
      "completed",
      "installed",
      "delivered",
      "approved",
      "paid",
      "succeeded",
      "confirmed",
      "verified-structured",
      "ok",
      "ready",
      "in-production",
      "production",
    ].includes(state)
  )
    return "success";
  if (
    [
      "failed",
      "failed-retryable",
      "declined",
      "revoked",
      "rejected",
      "missing",
      "blocked",
      "bad",
      "fail",
      "invalid",
    ].includes(state)
  )
    return "danger";
  if (
    [
      "waiting-for-user",
      "waiting-for-approval",
      "review-ready",
      "review-required",
      "hold",
      "frozen",
    ].includes(state)
  )
    return "person";
  if (["warning", "warn", "low", "uncertain"].includes(state)) return "warning";
  if (
    [
      "queued",
      "planning",
      "running",
      "released",
      "in-progress",
      "quoted",
      "priced",
      "dispatched",
      "on-route",
      "scheduled",
      "evaluated",
      "pending",
      "uploaded",
      "extracting",
      "high-candidate",
    ].includes(state)
  )
    return "info";
  return "neutral";
}

export function StatusBadge({
  tone,
  label,
  children,
  className = "",
  showIcon = true,
  ...props
}: {
  tone?: StatusTone;
  label?: string;
  children?: ReactNode;
  showIcon?: boolean;
  "data-state"?: string;
  "data-status"?: string;
  "data-tone"?: string;
} & HTMLAttributes<HTMLSpanElement>): JSX.Element {
  const legacyState =
    /(?:status-|delivery-|imports-status-|imports-confidence-|link-)([\w-]+)/.exec(className)?.[1];
  const resolvedTone =
    tone ??
    statusTone(
      props["data-state"] ??
        props["data-status"] ??
        props["data-tone"] ??
        legacyState ??
        (className.includes("production-chip-danger")
          ? "danger"
          : className.includes("is-ready")
            ? "ready"
            : className.includes("is-warn")
              ? "warn"
              : undefined),
    );
  return (
    <span
      {...props}
      className={`ui-badge ui-badge--${resolvedTone}${className ? ` ${className}` : ""}`}
    >
      {showIcon ? (
        <Icon
          kind={
            resolvedTone === "success"
              ? "check"
              : resolvedTone === "danger"
                ? "stop"
                : resolvedTone === "blocked" ||
                    resolvedTone === "warning" ||
                    resolvedTone === "person"
                  ? "warning"
                  : "info"
          }
        />
      ) : null}
      {label ?? children}
    </span>
  );
}
