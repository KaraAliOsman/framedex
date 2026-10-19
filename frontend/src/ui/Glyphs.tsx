import { OpeningSymbol } from "./OpeningSymbol";
import { legacySymbolOpening } from "./openingSymbols";
import { type SVGProps } from "react";
import { domainLabel, domainStatus } from "../i18n/domainLabels";
import { Icon, type IconName } from "./Icon";
/** Status vocabulary used by domain labels, mapped onto the single icon family. */
export type IconKind = "check" | "warning" | "stop" | "clock" | "info";
const STATUS_ICON: Record<IconKind, IconName> = {
  check: "check",
  warning: "warning",
  stop: "blocked",
  clock: "clock",
  info: "info",
};
export function StatusChip({ status, title }: { status: string; title?: string }): JSX.Element {
  const meta = domainStatus(status);
  return (
    <span className={`ui-badge ui-badge--${meta.tone}`} title={title}>
      <Icon name={STATUS_ICON[meta.icon]} size={16} />
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
  const physical = legacySymbolOpening(
    type === "DOOR" ? "DOOR_ENTRY" : type,
    type === "DOOR" ? "LEFT" : undefined,
  );
  if (type !== "AWNING") physical.direction = direction === "inward" ? "INWARD" : "OUTWARD";
  const left = (physical.hinge_side === "LEFT") !== (view === "exterior");
  const sliding = type.startsWith("SLIDING");
  const turn = ["TURN", "TILT_TURN"].includes(physical.movement);
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
      <rect x="5" y="5" width="14" height="14" />
      {sliding ? (
        <>
          <line x1="12" y1="3" x2="12" y2="21" />
          {["RIGHT", "LEFT"].map((travel, index) => (
            <OpeningSymbol
              key={travel}
              opening={physical}
              x={3 + index * 9}
              y={3}
              width={9}
              height={18}
              travel={travel as "LEFT" | "RIGHT"}
              view={view}
            />
          ))}
        </>
      ) : (
        <OpeningSymbol opening={physical} x={0} y={0} width={24} height={24} view={view} />
      )}
      {turn && <path data-handle="true" d={left ? "M20 11v3" : "M4 11v3"} />}
    </svg>
  );
}
