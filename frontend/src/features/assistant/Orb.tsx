import { t } from "../../i18n/es-CL";
import "./orb.css";

/** An abstract aperture with static poses that reflect the real job state. */
export type OrbState =
  | "idle"
  | "input"
  | "queued"
  | "thinking"
  | "working"
  | "waiting"
  | "approval"
  | "success"
  | "error"
  | "canceled";

/** Durable job lifecycle → orb state. Unknown future states degrade to idle —
 * never pass the API state through unmapped. */
export function orbStateFor(jobState?: string): OrbState {
  switch (jobState) {
    case "QUEUED":
      return "queued";
    case "PLANNING":
      return "thinking";
    case "RUNNING":
      return "working";
    case "WAITING_FOR_USER":
      return "waiting";
    case "WAITING_FOR_APPROVAL":
      return "approval";
    case "SUCCEEDED":
      return "success";
    case "FAILED":
    case "FAILED_RETRYABLE":
      return "error";
    case "CANCELED":
      return "canceled";
    default:
      return "idle";
  }
}

/** OrbState → i18n key — explicit state text for accessibility, per mandate. */
const STATE_TEXT: Record<OrbState, Parameters<typeof t>[0]> = {
  idle: "assistant.state.idle",
  input: "assistant.state.input",
  queued: "assistant.state.queued",
  thinking: "assistant.state.thinking",
  working: "assistant.state.working",
  waiting: "assistant.state.waiting",
  approval: "assistant.state.approval",
  success: "assistant.state.success",
  error: "assistant.state.error",
  canceled: "assistant.state.canceled",
};

export function Orb({
  state = "idle",
  size = 28,
  title,
}: {
  state?: OrbState;
  size?: number;
  /** Accessible label — omit for decorative use inside a labelled control.
   * When present, the current state is announced with it. */
  title?: string;
}): JSX.Element {
  const label = title ? `${title} — ${t(STATE_TEXT[state] ?? STATE_TEXT.idle)}` : undefined;
  return (
    <svg
      className={`orb is-${state}${size < 28 ? " orb--s" : ""}`}
      viewBox="0 0 48 48"
      width={size}
      height={size}
      role={label ? "img" : undefined}
      aria-hidden={label ? undefined : true}
      aria-label={label}
    >
      <rect className="orb__tile" x="2" y="2" width="44" height="44" rx="15" />
      <g
        className="orb__aperture"
        fill="none"
        stroke="currentColor"
        strokeWidth="3.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M15 32V19a6 6 0 0 1 6-6h12" />
        <path d="M33 16v13a6 6 0 0 1-6 6H15" />
        <path className="orb__bridge" d="M21 24h6" />
      </g>
      <circle className="orb__signal" cx="38" cy="9" r="4.5" />
    </svg>
  );
}
