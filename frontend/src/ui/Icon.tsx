import { type SVGProps } from "react";

/** The single icon family (constitution §3.6): 24 px grid, 1.75 px monoline,
 * round caps and joins. Common actions keep their familiar metaphor; trade
 * symbols (mullion, transom, dimension, section) share the same stroke so they
 * read as one set next to the generic ones. */
type Shape =
  | string
  | { circle: readonly [cx: number, cy: number, r: number]; fill?: boolean }
  | { rect: readonly [x: number, y: number, w: number, h: number, r?: number] };

const dot = (cx: number, cy: number): Shape => ({ circle: [cx, cy, 1.1], fill: true });

const ICONS = {
  // Navigation areas
  today: [{ rect: [4, 5.5, 16, 15, 2] }, "M8 3.5v4M16 3.5v4M4 10h16", "m8.5 15 2.2 2.2 4.8-4.8"],
  projects: [
    "M3 7.5A1.5 1.5 0 0 1 4.5 6H9l2 2h8.5A1.5 1.5 0 0 1 21 9.5v8a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 17.5z",
  ],
  clients: [
    { circle: [9, 8.5, 3.5] },
    "M2.75 20c0-3.3 2.8-5.5 6.25-5.5s6.25 2.2 6.25 5.5",
    "M15.5 5.2a3.5 3.5 0 0 1 0 6.6",
    "M18 14.9c1.9.7 3.25 2.4 3.25 5.1",
  ],
  catalogs: [
    { rect: [3.5, 4, 4, 16, 1] },
    { rect: [9.5, 4, 4, 16, 1] },
    "m15.6 5.3 3.4-.8 3 14.6-3.4.8z",
  ],
  workshop: ["M3 20V10l5 3v-3l5 3v-3l5 3V4h3v16z", "M7 16.5h1.5M11.5 16.5H13M16 16.5h1.5"],
  company: [
    "M4 21V5a1 1 0 0 1 1-1h9a1 1 0 0 1 1 1v16",
    "M15 9h4a1 1 0 0 1 1 1v11",
    "M2.5 21h19M8 8h3M8 12h3M8 16h3",
  ],
  analytics: ["M4 4v16h16", "M8.5 16v-4M12.5 16V8M16.5 16v-6"],
  // Generic actions
  plus: ["M12 5v14M5 12h14"],
  search: [{ circle: [11, 11, 6.5] }, "m20 20-4.4-4.4"],
  bell: ["M6 16.5V11a6 6 0 1 1 12 0v5.5l1.5 1.5h-15z", "M10 20.5a2 2 0 0 0 4 0"],
  close: ["M6 6l12 12M18 6 6 18"],
  check: ["m5 12.5 4.5 4.5L19 7"],
  chevronRight: ["m9.5 6 6 6-6 6"],
  chevronLeft: ["m14.5 6-6 6 6 6"],
  chevronDown: ["m6 9.5 6 6 6-6"],
  chevronUp: ["m6 14.5 6-6 6 6"],
  arrowRight: ["M5 12h14M13 6l6 6-6 6"],
  arrowLeft: ["M19 12H5M11 6l-6 6 6 6"],
  more: [dot(5.5, 12), dot(12, 12), dot(18.5, 12)],
  menu: ["M4 6.5h16M4 12h16M4 17.5h16"],
  sidebar: [{ rect: [3.5, 4, 17, 16, 2] }, "M9.5 4v16"],
  edit: ["M4 20h4L19 9a2.1 2.1 0 0 0-3-3L5 17z", "m14.5 7.5 3 3"],
  copy: [
    { rect: [8, 8, 12, 12, 1.5] },
    "M16 8V5.5A1.5 1.5 0 0 0 14.5 4h-9A1.5 1.5 0 0 0 4 5.5v9A1.5 1.5 0 0 0 5.5 16H8",
  ],
  trash: ["M4 7h16M9.5 7V4.5h5V7", "M6.5 7l1 13h9l1-13", "M10 11v5M14 11v5"],
  undo: ["M9 14 4 9l5-5", "M4 9h10.5a5.5 5.5 0 0 1 0 11H11"],
  redo: ["m15 14 5-5-5-5", "M20 9H9.5a5.5 5.5 0 0 0 0 11H13"],
  eyeOff: [
    "M3 3l18 18",
    "M10.6 5.6A10 10 0 0 1 12 5.5c6 0 9.5 6.5 9.5 6.5a17 17 0 0 1-2.6 3.4",
    "M6.6 6.6C3.9 8.3 2.5 12 2.5 12S6 18.5 12 18.5a9.6 9.6 0 0 0 4.3-1",
    "M9.9 9.9a3 3 0 0 0 4.2 4.2",
  ],
  download: ["M12 4v11", "m7 10.5 5 5 5-5", "M4.5 19.5h15"],
  upload: ["M12 15.5v-11", "m7 9 5-5 5 5", "M4.5 19.5h15"],
  maximize: ["M4.5 9V4.5H9", "M15 4.5h4.5V9", "M19.5 15v4.5H15", "M9 19.5H4.5V15"],
  minimize: ["M9 4.5V9H4.5", "M15 4.5V9h4.5", "M19.5 15H15v4.5", "M4.5 15H9v4.5"],
  restore: ["M9 4.5V9H4.5", "M15 4.5V9h4.5", "M15 19.5V15h4.5", "M9 19.5V15H4.5"],
  paperclip: [
    "m20 11.5-8.2 8.2a5 5 0 0 1-7.1-7.1l8.6-8.6a3.4 3.4 0 0 1 4.8 4.8l-8.6 8.6a1.7 1.7 0 0 1-2.4-2.4l7.9-7.9",
  ],
  external: ["M14 4h6v6M20 4l-8.5 8.5", "M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"],
  link: [
    "M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1",
    "M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1",
  ],
  send: ["M4 11.5 20 4l-6.5 16-2.7-6.8z", "m10.8 13.2 9.2-9.2"],
  refresh: [
    "M19.5 10.5A7.75 7.75 0 0 0 5.4 7.4L4 9",
    "M4 4.5V9h4.5",
    "M4.5 13.5a7.75 7.75 0 0 0 14.1 3.1L20 15",
    "M20 19.5V15h-4.5",
  ],
  filter: ["M4 5h16l-6 7.5V19l-4 1.5v-8z"],
  grid: [
    { rect: [4, 4, 7, 7, 1.5] },
    { rect: [13, 4, 7, 7, 1.5] },
    { rect: [4, 13, 7, 7, 1.5] },
    { rect: [13, 13, 7, 7, 1.5] },
  ],
  list: ["M9 6.5h11M9 12h11M9 17.5h11", dot(4.75, 6.5), dot(4.75, 12), dot(4.75, 17.5)],
  eye: [
    "M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z",
    { circle: [12, 12, 3] },
  ],
  stop: [{ rect: [6.5, 6.5, 11, 11, 1.5] }],
  logout: ["M10 4H5a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h5", "m15 8 4 4-4 4", "M19 12H9"],
  keyboard: [
    { rect: [2.5, 6, 19, 12, 2] },
    "M7 14.5h10",
    dot(6.5, 10),
    dot(10, 10),
    dot(14, 10),
    dot(17.5, 10),
  ],
  // Status
  warning: [
    "M10.3 4.3a2 2 0 0 1 3.4 0l7.6 13.2A2 2 0 0 1 19.6 20H4.4a2 2 0 0 1-1.7-2.5z",
    "M12 9.5V14",
    dot(12, 17),
  ],
  info: [{ circle: [12, 12, 9] }, "M12 11v5.5", dot(12, 7.75)],
  clock: [{ circle: [12, 12, 9] }, "M12 7v5l3.5 2"],
  blocked: [{ circle: [12, 12, 9] }, "m5.6 5.6 12.8 12.8"],
  // Work objects
  document: [
    "M6 3h8l4 4v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z",
    "M14 3v4h4",
    "M8.5 12h7M8.5 16h7",
  ],
  cut: [{ circle: [6, 6.5, 2.5] }, { circle: [6, 17.5, 2.5] }, "M8.2 7.9 20 17", "M8.2 16.1 20 7"],
  materials: [{ rect: [3, 6, 18, 3.5, 1] }, { rect: [3, 14.5, 18, 3.5, 1] }, "M7 9.5v5M17 9.5v5"],
  purchasing: [
    "M3 4h2.5l2.2 11h10.6l2-8H6.6",
    { circle: [9.5, 19.5, 1.25] },
    { circle: [17, 19.5, 1.25] },
  ],
  inventory: [
    { rect: [3.5, 11, 7.5, 9, 1] },
    { rect: [13, 11, 7.5, 9, 1] },
    { rect: [8.25, 3, 7.5, 8, 1] },
  ],
  dispatch: [
    "M3 6.5h11v10H3zM14 9.5h4l3 3.5v3.5h-7",
    { circle: [7, 17.5, 1.75] },
    { circle: [17.5, 17.5, 1.75] },
  ],
  calendar: [{ rect: [3.5, 5, 17, 15.5, 2] }, "M3.5 10h17M8 3v4M16 3v4"],
  location: [
    "M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z",
    { circle: [12, 9.5, 2.5] },
  ],
  mail: [{ rect: [3, 5, 18, 14, 2] }, "m3.5 6.5 8.5 6.5 8.5-6.5"],
  lock: [{ rect: [5, 10.5, 14, 10, 2] }, "M8 10.5V7.5a4 4 0 0 1 8 0v3"],
  hash: ["M5 9h14M5 15h14M10.5 4 8.5 20M15.5 4l-2 16"],
  price: [
    "M20 12.6 12.6 20a1.5 1.5 0 0 1-2.1 0L4 13.5V4h9.5l6.5 6.5a1.5 1.5 0 0 1 0 2.1z",
    dot(8.5, 8.5),
  ],
  image: [{ rect: [3.5, 4.5, 17, 15, 2] }, { circle: [9, 9.5, 1.75] }, "m20.5 15.5-5-5L6 20"],
  layers: ["m12 3.5 9 5-9 5-9-5z", "m3 13.5 9 5 9-5"],
  cube: ["M12 3 20 7.5v9L12 21l-8-4.5v-9z", "M4 7.5 12 12l8-4.5M12 12v9"],
  swatch: [{ rect: [3.5, 3.5, 7, 17, 2] }, "M10.5 8.5 15 4l4.5 4.5-9 9", "M10.5 15h9.5v5.5H7"],
  glass: [{ rect: [5, 3, 14, 18, 1] }, "m9 9.5 3.5-3.5M9 14l6-6"],
  window: [{ rect: [4, 3, 16, 18, 1] }, { rect: [7, 6, 10, 12, 0.5] }],
  door: ["M6 21V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v17", "M3.5 21h17", dot(14.75, 12.5)],
  user: [{ circle: [12, 8, 4] }, "M4.5 21c0-4 3.4-6.5 7.5-6.5s7.5 2.5 7.5 6.5"],
  shield: ["M12 3 4.5 6v6c0 4.5 3.2 7.8 7.5 9 4.3-1.2 7.5-4.5 7.5-9V6z"],
  // Trade symbols (same stroke as the family)
  dimension: ["M3 7.5v9M21 7.5v9M3 12h18", "M6 9.5 3.5 12 6 14.5M18 9.5l2.5 2.5-2.5 2.5"],
  mullion: [{ rect: [3.5, 3.5, 17, 17, 1] }, "M12 3.5v17"],
  transom: [{ rect: [3.5, 3.5, 17, 17, 1] }, "M3.5 12h17"],
  profile: [{ rect: [3.5, 3.5, 17, 17, 1] }, { rect: [7, 7, 10, 10, 0.5] }, "M10.5 7v10"],
} satisfies Record<string, readonly Shape[]>;

export type IconName = keyof typeof ICONS;
export const ICON_NAMES = Object.keys(ICONS) as IconName[];

export function Icon({
  name,
  size = 20,
  label,
  className = "",
  ...props
}: Omit<SVGProps<SVGSVGElement>, "name"> & {
  name: IconName;
  size?: 16 | 20 | 24;
  /** Accessible name; omit when the icon sits beside visible text. */
  label?: string;
}): JSX.Element {
  return (
    <svg
      {...props}
      className={`ui-icon ${className}`.trim()}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={size === 16 ? 2 : 1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      focusable="false"
    >
      {ICONS[name].map((shape: Shape, index: number) =>
        typeof shape === "string" ? (
          <path key={index} d={shape} />
        ) : "circle" in shape ? (
          <circle
            key={index}
            cx={shape.circle[0]}
            cy={shape.circle[1]}
            r={shape.circle[2]}
            fill={shape.fill ? "currentColor" : undefined}
            stroke={shape.fill ? "none" : undefined}
          />
        ) : (
          <rect
            key={index}
            x={shape.rect[0]}
            y={shape.rect[1]}
            width={shape.rect[2]}
            height={shape.rect[3]}
            rx={shape.rect[4] ?? 0}
          />
        ),
      )}
    </svg>
  );
}
