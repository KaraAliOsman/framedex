import { useEffect, useRef } from "react";

import { t } from "../../i18n/es-CL";
import "./companion.css";

/** The DEKOPEN copilot character (constitution §5.11, contract 06).
 *
 * Grammar of the reference character: one clean round body and two dark,
 * negative vertical pill eyes — no face plate, shine, ring or antenna. The
 * personality is in the gesture: body volume, orientation and eyes move
 * together, with expressive clips of several seconds (the 280 ms control cap
 * does not flatten them). Every gesture comes from a real job state; a
 * gesture never claims progress, never starts a call and never steals focus.
 *
 * Motion runs on a local clock that writes SVG attributes directly (no React
 * renders per frame), pauses when the figure is off screen or the tab is
 * hidden and resumes in the current state without replaying missed time.
 * Reduced motion shows the equivalent static pose. A `clock` prop freezes
 * the figure at a given time for the internal pose catalog. */
export type CompanionState =
  | "idle"
  | "input"
  | "queued"
  | "thinking"
  | "working"
  | "waiting"
  | "approval"
  | "success"
  | "error"
  | "canceled"
  | "unavailable";

/** Durable job lifecycle → companion pose. Unknown future states degrade to
 * idle — the API state is never passed through unmapped. */
export function companionStateFor(jobState?: string): CompanionState {
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

const STATE_TEXT: Record<CompanionState, Parameters<typeof t>[0]> = {
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
  unavailable: "assistant.state.unavailable",
};

export function companionStateText(state: CompanionState): string {
  return t(STATE_TEXT[state] ?? STATE_TEXT.idle);
}

/** Pose parameters, all relative: the body is a circle of radius R at the
 * center of a 100-unit box with margin for deformation. */
type Pose = {
  /** body squash/stretch */
  sx: number;
  sy: number;
  /** body tilt (deg) and lift (units, negative = up) */
  tilt: number;
  lift: number;
  /** gaze offset of the eyes (units) */
  gx: number;
  gy: number;
  /** eye openness (1 open, 0 closed) and width factor */
  open: number;
  wide: number;
  /** eye tilt (deg), mirrored per eye for expressions */
  brow: number;
};

const REST: Pose = { sx: 1, sy: 1, tilt: 0, lift: 0, gx: 0, gy: 0, open: 1, wide: 1, brow: 0 };

type Key = { at: number; pose: Partial<Pose> };
/** A clip: keyframes over `length` ms, looping unless `once`. */
type Clip = { length: number; keys: Key[]; once?: boolean };

const CLIPS: Record<CompanionState, Clip[]> = {
  idle: [
    {
      length: 5200,
      keys: [
        { at: 0, pose: {} },
        { at: 0.35, pose: { sy: 1.012, sx: 0.994, gx: 1.2 } },
        { at: 0.5, pose: { sy: 1.012, sx: 0.994, gx: 1.2, open: 0.08 } },
        { at: 0.54, pose: { sy: 1.012, sx: 0.994, gx: 1.2 } },
        { at: 0.8, pose: { sy: 0.996, sx: 1.004, gx: -0.8 } },
        { at: 1, pose: {} },
      ],
    },
    {
      length: 4600,
      keys: [
        { at: 0, pose: {} },
        { at: 0.4, pose: { sy: 1.01, gy: -0.8, gx: -1 } },
        { at: 0.7, pose: { sy: 0.996, gx: 0.6 } },
        { at: 0.86, pose: { open: 0.08 } },
        { at: 0.9, pose: {} },
        { at: 1, pose: {} },
      ],
    },
  ],
  input: [
    {
      length: 3800,
      keys: [
        { at: 0, pose: { gx: -2.2, gy: 2.6, tilt: -2 } },
        { at: 0.5, pose: { gx: -1.6, gy: 2.8, tilt: -2.5, sy: 1.008 } },
        { at: 0.7, pose: { gx: -1.6, gy: 2.8, tilt: -2.5, open: 0.1 } },
        { at: 0.74, pose: { gx: -1.6, gy: 2.8, tilt: -2.5 } },
        { at: 1, pose: { gx: -2.2, gy: 2.6, tilt: -2 } },
      ],
    },
  ],
  queued: [
    {
      length: 4400,
      keys: [
        { at: 0, pose: { open: 0.62, gy: 1 } },
        { at: 0.5, pose: { open: 0.58, gy: 1.2, sy: 0.992, sx: 1.006 } },
        { at: 1, pose: { open: 0.62, gy: 1 } },
      ],
    },
  ],
  thinking: [
    {
      length: 5600,
      keys: [
        { at: 0, pose: { gx: 2.4, gy: -2.4, open: 0.78, tilt: 4, brow: 6 } },
        { at: 0.45, pose: { gx: -2.2, gy: -2.6, open: 0.74, tilt: -3, brow: -5, sy: 1.015 } },
        { at: 0.6, pose: { gx: -2.2, gy: -2.6, open: 0.1, tilt: -3 } },
        { at: 0.64, pose: { gx: -2.2, gy: -2.6, open: 0.74, tilt: -3, brow: -5 } },
        { at: 1, pose: { gx: 2.4, gy: -2.4, open: 0.78, tilt: 4, brow: 6 } },
      ],
    },
  ],
  working: [
    {
      // reading: the gaze scans lines
      length: 6400,
      keys: [
        { at: 0, pose: { gx: -3, gy: 1.6, open: 0.8, wide: 0.92 } },
        { at: 0.22, pose: { gx: 3, gy: 1.6, open: 0.8, wide: 0.92 } },
        { at: 0.28, pose: { gx: -3, gy: 2.6, open: 0.8, wide: 0.92 } },
        { at: 0.5, pose: { gx: 3, gy: 2.6, open: 0.8, wide: 0.92, sy: 1.01 } },
        { at: 0.56, pose: { gx: -3, gy: 3.4, open: 0.8, wide: 0.92 } },
        { at: 0.78, pose: { gx: 3, gy: 3.4, open: 0.8, wide: 0.92 } },
        { at: 1, pose: { gx: -3, gy: 1.6, open: 0.8, wide: 0.92 } },
      ],
    },
    {
      // doing: a contained working rhythm of the whole volume
      length: 4800,
      keys: [
        { at: 0, pose: { gy: 1.4, open: 0.72 } },
        { at: 0.18, pose: { sy: 0.965, sx: 1.03, lift: 1.2, gy: 2, open: 0.62 } },
        { at: 0.32, pose: { sy: 1.025, sx: 0.985, lift: -1.4, gy: 1, open: 0.8 } },
        { at: 0.5, pose: { gy: 1.4, open: 0.72 } },
        { at: 0.68, pose: { sy: 0.965, sx: 1.03, lift: 1.2, gy: 2, open: 0.62, tilt: 2 } },
        { at: 0.82, pose: { sy: 1.025, sx: 0.985, lift: -1.4, gy: 1, open: 0.8, tilt: -2 } },
        { at: 1, pose: { gy: 1.4, open: 0.72 } },
      ],
    },
  ],
  waiting: [
    {
      length: 6000,
      keys: [
        { at: 0, pose: { wide: 1.08, open: 1, gy: -0.6 } },
        { at: 0.5, pose: { wide: 1.08, open: 1, gy: -0.6, tilt: 3 } },
        { at: 0.82, pose: { wide: 1.08, open: 0.1, gy: -0.6, tilt: 3 } },
        { at: 0.86, pose: { wide: 1.08, open: 1, gy: -0.6, tilt: 3 } },
        { at: 1, pose: { wide: 1.08, open: 1, gy: -0.6 } },
      ],
    },
  ],
  approval: [
    {
      // one review gesture, then attentive hold
      length: 1600,
      once: true,
      keys: [
        { at: 0, pose: {} },
        { at: 0.3, pose: { sx: 1.04, sy: 1.04, gy: 2.4, lift: -0.8 } },
        { at: 0.65, pose: { sx: 1.02, sy: 1.02, gy: 2.8, gx: 1.4 } },
        { at: 1, pose: { gy: 1.6, gx: 0.6, open: 0.94 } },
      ],
    },
  ],
  success: [
    {
      // brief acknowledgement, then rest — never replayed on reload
      length: 1300,
      once: true,
      keys: [
        { at: 0, pose: {} },
        { at: 0.2, pose: { sy: 0.92, sx: 1.07, lift: 2 } },
        { at: 0.45, pose: { sy: 1.06, sx: 0.96, lift: -6, open: 0.34, wide: 1.12 } },
        { at: 0.7, pose: { sy: 0.97, sx: 1.03, lift: 0.5, open: 0.4, wide: 1.1 } },
        { at: 1, pose: {} },
      ],
    },
  ],
  error: [
    {
      length: 1400,
      once: true,
      keys: [
        { at: 0, pose: {} },
        { at: 0.15, pose: { tilt: -5, gx: -1.4 } },
        { at: 0.32, pose: { tilt: 5, gx: 1.4 } },
        { at: 0.48, pose: { tilt: -3, gx: -0.8 } },
        { at: 0.7, pose: { tilt: 0, gy: 2.2, open: 0.6, brow: -7, sy: 0.985 } },
        { at: 1, pose: { gy: 2.2, open: 0.6, brow: -7, sy: 0.985 } },
      ],
    },
  ],
  canceled: [
    {
      length: 1500,
      once: true,
      keys: [
        { at: 0, pose: {} },
        { at: 0.5, pose: { open: 0.14, gy: 1.6, sy: 0.985 } },
        { at: 1, pose: { open: 0.86, gy: 0.6 } },
      ],
    },
  ],
  unavailable: [
    { length: 1000, once: true, keys: [{ at: 0, pose: { open: 0.42, gy: 1.8, sy: 0.99 } }] },
  ],
};

/** Static poses for reduced motion: same expression, no movement. */
const STILL: Record<CompanionState, Partial<Pose>> = {
  idle: {},
  input: { gx: -2.2, gy: 2.6, tilt: -2 },
  queued: { open: 0.62, gy: 1 },
  thinking: { gx: 2.4, gy: -2.4, open: 0.78, tilt: 4, brow: 6 },
  working: { gy: 1.6, open: 0.8, wide: 0.92 },
  waiting: { wide: 1.08, gy: -0.6 },
  approval: { gy: 1.6, gx: 0.6, open: 0.94 },
  success: { open: 0.4, wide: 1.1 },
  error: { gy: 2.2, open: 0.6, brow: -7 },
  canceled: { open: 0.86, gy: 0.6 },
  unavailable: { open: 0.42, gy: 1.8, sy: 0.99 },
};

const FIELDS = Object.keys(REST) as (keyof Pose)[];

function full(partial: Partial<Pose>): Pose {
  return { ...REST, ...partial };
}

function ease(value: number): number {
  return value < 0.5 ? 2 * value * value : 1 - (-2 * value + 2) ** 2 / 2;
}

function mix(from: Pose, to: Pose, amount: number): Pose {
  const out = { ...from };
  for (const field of FIELDS) out[field] = from[field] + (to[field] - from[field]) * amount;
  return out;
}

function sample(clip: Clip, elapsed: number): Pose {
  const progress = clip.once
    ? Math.min(1, elapsed / clip.length)
    : (elapsed % clip.length) / clip.length;
  const keys = clip.keys;
  if (keys.length === 1) return full(keys[0]!.pose);
  for (let index = 0; index < keys.length - 1; index += 1) {
    const current = keys[index]!;
    const next = keys[index + 1]!;
    if (progress >= current.at && progress <= next.at) {
      const span = next.at - current.at || 1;
      return mix(full(current.pose), full(next.pose), ease((progress - current.at) / span));
    }
  }
  return full(keys[keys.length - 1]!.pose);
}

/** A small stable hash so copies on screen do not blink in sync. */
function seedOf(text: string): number {
  let hash = 2166136261;
  for (let index = 0; index < text.length; index += 1)
    hash = Math.imul(hash ^ text.charCodeAt(index), 16777619);
  return Math.abs(hash);
}

const R = 34;
const EYE_W = R * 2 * 0.125;
const EYE_H = R * 2 * 0.28;
const EYE_DX = R * 2 * 0.155;

function prefersReducedMotion(): boolean {
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

export function Companion({
  state = "idle",
  size = 28,
  title,
  clock,
}: {
  state?: CompanionState;
  size?: number;
  /** Accessible label — omit for decorative use inside a labelled control.
   * When present, the current state is announced with it. */
  title?: string;
  /** Freeze the figure at this time (ms) — internal pose catalog only. */
  clock?: number;
}): JSX.Element {
  const label = title ? `${title} — ${companionStateText(state)}` : undefined;
  const svg = useRef<SVGSVGElement>(null);
  const body = useRef<SVGGElement>(null);
  const eyes = useRef<SVGGElement>(null);
  const left = useRef<SVGRectElement>(null);
  const right = useRef<SVGRectElement>(null);
  const instance = useRef(seedOf(`${Math.random()}`));
  /** The previous state, to decide whether one-shot gestures may play: a
   * success/error seen at mount (a reload) shows its rest pose only. */
  const previous = useRef<CompanionState | null>(null);
  const current = useRef<Pose>(full(STILL[state]));

  useEffect(() => {
    const node = svg.current;
    if (!node) return;
    const compact = size < 48;
    const amplitude = compact ? 0.6 : 1;
    const firstSight = previous.current === null;
    const transitionFrom = { ...current.current };
    previous.current = state;
    const clips = CLIPS[state];
    const clipIndex = (instance.current + state.length) % clips.length;
    let clip = clips[clipIndex]!;
    const oneShotAtMount = firstSight && clip.once;

    const draw = (pose: Pose): void => {
      current.current = pose;
      const scale = (value: number) => 1 + (value - 1) * amplitude;
      body.current?.setAttribute(
        "transform",
        `translate(50 ${50 + pose.lift * amplitude}) rotate(${pose.tilt * amplitude}) scale(${scale(pose.sx)} ${scale(pose.sy)}) translate(-50 -50)`,
      );
      eyes.current?.setAttribute(
        "transform",
        `translate(${pose.gx * amplitude} ${pose.gy * amplitude})`,
      );
      const open = Math.max(0.06, Math.min(1, pose.open));
      for (const [eye, side] of [
        [left.current, -1],
        [right.current, 1],
      ] as const) {
        if (!eye) continue;
        const cx = 50 + side * EYE_DX;
        eye.setAttribute(
          "transform",
          `translate(${cx} 50) rotate(${pose.brow * side * amplitude}) scale(${scale(pose.wide)} ${open}) translate(${-cx} -50)`,
        );
      }
    };

    const still = clock === undefined && prefersReducedMotion();
    if (still || oneShotAtMount) {
      draw(full(STILL[state]));
      return;
    }
    if (clock !== undefined) {
      draw(sample(clip, clock));
      return;
    }

    let frame = 0;
    let visible = true;
    let started = performance.now();
    let pausedAt: number | null = null;
    const blend = 220;
    const tick = (now: number): void => {
      const elapsed = now - started;
      let pose = sample(clip, elapsed);
      if (elapsed < blend) pose = mix(transitionFrom, pose, ease(elapsed / blend));
      draw(pose);
      if (clip.once && elapsed >= clip.length) {
        // One-shot gestures settle on their rest pose; nothing keeps looping.
        if (state === "success" || state === "canceled") {
          clip = CLIPS.idle[instance.current % CLIPS.idle.length]!;
          started = now;
        } else return;
      } else if (!clip.once && elapsed > clip.length * 3 && clips.length > 1) {
        // Alternate variants of the same intention instead of one loop.
        clip = clips[(clips.indexOf(clip) + 1) % clips.length]!;
        started = now;
      }
      frame = window.requestAnimationFrame(tick);
    };
    const start = (): void => {
      if (frame || !visible || document.hidden) return;
      if (pausedAt !== null) {
        // Resume in the current state without replaying the missed time.
        started += performance.now() - pausedAt;
        pausedAt = null;
      }
      frame = window.requestAnimationFrame(tick);
    };
    const stop = (): void => {
      if (!frame) return;
      window.cancelAnimationFrame(frame);
      frame = 0;
      pausedAt = performance.now();
    };
    const onVisibility = (): void => (document.hidden ? stop() : start());
    document.addEventListener("visibilitychange", onVisibility);
    let observer: IntersectionObserver | null = null;
    if (typeof IntersectionObserver === "function") {
      observer = new IntersectionObserver((entries) => {
        visible = entries.some((entry) => entry.isIntersecting);
        if (visible) start();
        else stop();
      });
      observer.observe(node);
    }
    start();
    return () => {
      document.removeEventListener("visibilitychange", onVisibility);
      observer?.disconnect();
      if (frame) window.cancelAnimationFrame(frame);
    };
  }, [state, size, clock]);

  const rest = full(STILL[state]);
  return (
    <svg
      ref={svg}
      className={`companion is-${state}${size < 48 ? " companion--compact" : ""}`}
      viewBox="0 0 100 100"
      width={size}
      height={size}
      role={label ? "img" : undefined}
      aria-hidden={label ? undefined : true}
      aria-label={label}
      data-state={state}
    >
      <g
        ref={body}
        transform={`translate(50 ${50 + rest.lift}) scale(${rest.sx} ${rest.sy}) translate(-50 -50)`}
      >
        <circle className="companion__body" cx="50" cy="50" r={R} />
        <g ref={eyes} transform={`translate(${rest.gx} ${rest.gy})`}>
          <rect
            ref={left}
            className="companion__eye"
            x={50 - EYE_DX - EYE_W / 2}
            y={50 - EYE_H / 2}
            width={EYE_W}
            height={EYE_H}
            rx={EYE_W / 2}
          />
          <rect
            ref={right}
            className="companion__eye"
            x={50 + EYE_DX - EYE_W / 2}
            y={50 - EYE_H / 2}
            width={EYE_W}
            height={EYE_H}
            rx={EYE_W / 2}
          />
        </g>
      </g>
    </svg>
  );
}

/** Internal pose catalog with a controllable clock — for the final review
 * (07), reachable from the assistant workspace; not a product screen. */
export const COMPANION_STATES: CompanionState[] = [
  "idle",
  "input",
  "queued",
  "thinking",
  "working",
  "waiting",
  "approval",
  "success",
  "error",
  "canceled",
  "unavailable",
];
