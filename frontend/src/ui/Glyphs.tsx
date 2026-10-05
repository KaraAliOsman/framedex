import { type SVGProps } from "react";
import { domainLabel, domainStatus } from "../i18n/domainLabels";
export type IconKind =
  | "check"
  | "warning"
  | "stop"
  | "clock"
  | "info"
  | "close"
  | "copy"
  | "search"
  | "profile"
  | "dimension"
  | "mullion"
  | "transom"
  | "cut";
const paths: Record<IconKind, string> = {
  check: "M4 12l5 5L20 6",
  warning: "M12 3L2 21h20L12 3Zm0 5v6m0 3v1",
  stop: "M5 5h14v14H5V5Zm3 3l8 8m0-8-8 8",
  clock: "M4 4h16v16H4V4Zm8 3v6h5",
  info: "M4 4h16v16H4V4Zm8 6v7m0-11v1",
  close: "M5 5l14 14M19 5L5 19",
  copy: "M7 7h13v13H7V7ZM4 16H2V2h14v2",
  search: "M3 3h12v12H3V3Zm12 12 6 6",
  profile: "M3 3h18v18H3V3Zm3 3h12v12H6V6Zm4 0v12",
  dimension: "M3 4v16M21 4v16M3 12h18M1 14l4-4m14 4 4-4",
  mullion: "M3 3h18v18H3V3Zm8 0v18m2-18v18",
  transom: "M3 3h18v18H3V3Zm0 8h18M3 13h18",
  cut: "M3 3v18h18M6 3v15h15M3 21 6 18",
};
export function Icon({
  kind,
  ...props
}: SVGProps<SVGSVGElement> & { kind: IconKind }): JSX.Element {
  return (
    <svg
      {...props}
      className={`ui-glyph ${props.className ?? ""}`}
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="square"
      strokeLinejoin="miter"
    >
      <path d={paths[kind]} />
    </svg>
  );
}
export function StatusChip({ status, title }: { status: string; title?: string }): JSX.Element {
  const meta = domainStatus(status);
  return (
    <span className={`ui-badge ui-badge--${meta.tone}`} title={title}>
      <Icon kind={meta.icon} />
      {meta.label}
    </span>
  );
}
export type OpeningKind =
  | "FIXED"
  | "TURN_LEFT"
  | "TURN_RIGHT"
  | "TILT"
  | "TILT_TURN_LEFT"
  | "TILT_TURN_RIGHT"
  | "AWNING"
  | "SLIDING"
  | "SLIDING_2L"
  | "DOOR";
export function OpeningGlyph({
  type,
  view = "interior",
  direction = "inward",
  ...props
}: Omit<SVGProps<SVGSVGElement>, "type"> & {
  type: OpeningKind;
  view?: "interior" | "exterior";
  direction?: "inward" | "outward";
}): JSX.Element {
  const left = type.endsWith("LEFT") !== (view === "exterior");
  const turn = type.startsWith("TURN") || type.startsWith("TILT_TURN") || type === "DOOR";
  const tilt = type === "TILT" || type.startsWith("TILT_TURN");
  const sliding = type.startsWith("SLIDING");
  const away = (direction === "inward") === (view === "exterior");
  return (
    <svg
      {...props}
      className={`ui-opening-glyph ${props.className ?? ""}`}
      viewBox="0 0 24 24"
      role="img"
      aria-label={`${type === "TILT" ? "Abatimiento" : domainLabel(type)} · Vista ${view === "interior" ? "interior" : "exterior"}`}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="square"
      strokeLinejoin="miter"
    >
      <rect x="2.75" y="2.75" width="18.5" height="18.5" />
      {sliding ? (
        <>
          <path d="M12 3v18M5 10h4m-2-2 2 2-2 2M19 15h-4m2-2-2 2 2 2M3 23h18" />
        </>
      ) : (
        <>
          <rect x="5" y="5" width="14" height="14" />
          {turn ? (
            <path
              data-symbol="turn"
              d={left ? "M5 5L19 12L5 19" : "M19 5L5 12L19 19"}
              strokeDasharray={away ? "3 2" : undefined}
            />
          ) : null}
          {tilt ? (
            <path
              data-symbol="tilt"
              d="M5 19L12 5L19 19"
              strokeDasharray={away ? "3 2" : undefined}
            />
          ) : null}
          {type === "AWNING" ? (
            <path
              data-symbol="awning"
              d="M5 5L12 19L19 5"
              strokeDasharray={away ? "3 2" : undefined}
            />
          ) : null}
          {turn ? <path data-handle="true" d={left ? "M20 11v3" : "M4 11v3"} /> : null}
          {tilt && !turn ? <path data-handle="true" d="M11 4h3" /> : null}
        </>
      )}
    </svg>
  );
}
