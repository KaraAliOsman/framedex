import { useId } from "react";

type Point = readonly [number, number];
const FAMILIES: Record<
  string,
  { name: string; outline: Point[]; chambers: string; gasket?: string }
> = {
  frame: {
    name: "marco",
    outline: [
      [25, 88],
      [25, 30],
      [100, 30],
      [100, 57],
      [113, 57],
      [113, 88],
    ],
    chambers: "M33 38h24v15H33ZM64 38h28v15H64ZM33 61h23v19H33ZM64 61h16v19H64ZM88 65h17v15H88Z",
    gasket: "M27 31h13",
  },
  sash: {
    name: "hoja",
    outline: [
      [25, 88],
      [25, 42],
      [44, 42],
      [44, 24],
      [104, 24],
      [104, 51],
      [113, 51],
      [113, 88],
    ],
    chambers: "M52 32h19v20H52ZM78 32h18v20H78ZM33 61h23v19H33ZM64 61h16v19H64ZM88 60h17v20H88Z",
    gasket: "M98 26v17h7",
  },
  mullion: {
    name: "montante",
    outline: [
      [25, 88],
      [25, 42],
      [39, 42],
      [39, 27],
      [99, 27],
      [99, 42],
      [113, 42],
      [113, 88],
    ],
    chambers: "M47 35h18v19H47ZM73 35h18v19H73ZM33 62h23v18H33ZM64 62h17v18H64ZM89 62h16v18H89Z",
    gasket: "M40 29h10M88 29h10",
  },
  bead: {
    name: "junquillo",
    outline: [
      [34, 86],
      [34, 52],
      [58, 52],
      [58, 39],
      [80, 39],
      [80, 86],
    ],
    chambers: "M42 78V60h18v-13h12v31Z",
    gasket: "M77 40v11",
  },
  steel: {
    name: "refuerzo",
    outline: [
      [30, 88],
      [30, 32],
      [108, 32],
      [108, 88],
      [97, 88],
      [97, 43],
      [41, 43],
      [41, 88],
    ],
    chambers: "",
  },
};

/** Recognition aid only. This geometry never enters calculations or exports. */
export function ProfileIllustration({
  role = "FRAME",
  material = "PVC",
  depthMm,
  className,
}: {
  role?: string;
  material?: string;
  depthMm?: number;
  className?: string;
}): JSX.Element {
  const id = useId().replace(/:/g, "");
  const key = /BEAD/.test(role)
    ? "bead"
    : /MULLION|TRANSOM|INVER/.test(role)
      ? "mullion"
      : /SASH|LEAF/.test(role)
        ? "sash"
        : /REINFORC/.test(role)
          ? "steel"
          : "frame";
  const family = FAMILIES[key]!;
  const metal = material.startsWith("ALUMINIUM") || key === "steel";
  const offset = depthMm ? Math.max(22, Math.min(54, depthMm * 0.55)) : 38;
  const lift = -offset * 0.48;
  const outline =
    family.outline.map(([x, y], index) => `${index ? "L" : "M"}${x} ${y}`).join("") + "Z";
  return (
    <svg
      className={`profile-illustration ${className ?? ""}`}
      viewBox="0 0 200 150"
      role="img"
      aria-label={`Ilustración de familia · ${family.name}`}
    >
      <defs>
        <linearGradient id={`${id}-side`} x1="0" x2="1" y1="0" y2=".4">
          <stop
            offset="0"
            stopColor={metal ? "var(--mat-aluminium-edge)" : "var(--mat-pvc-edge)"}
          />
          <stop offset="1" stopColor="var(--mat-pvc-fill)" />
        </linearGradient>
        <linearGradient id={`${id}-front`} x1="0" y1="0" x2="0" y2="1">
          <stop stopColor="var(--mat-pvc-highlight)" />
          <stop
            offset="1"
            stopColor={metal ? "var(--mat-aluminium-fill)" : "var(--mat-pvc-fill)"}
          />
        </linearGradient>
      </defs>
      <ellipse cx="102" cy="124" rx="64" ry="9" fill="var(--border-subtle)" opacity=".5" />
      <g
        transform="translate(12 20) rotate(-5 90 55)"
        stroke="var(--mat-pvc-edge)"
        strokeWidth="1.2"
        strokeLinejoin="round"
      >
        <path d={outline} transform={`translate(${offset} ${lift})`} fill="var(--mat-pvc-edge)" />
        {family.outline.map(([x, y], index) => {
          const [nextX, nextY] = family.outline[(index + 1) % family.outline.length]!;
          if ((nextY - y) * offset - (nextX - x) * lift <= 0) return null;
          return (
            <path
              key={index}
              d={`M${x} ${y}L${x + offset} ${y + lift}L${nextX + offset} ${nextY + lift}L${nextX} ${nextY}Z`}
              fill={nextY === y ? "var(--mat-pvc-highlight)" : `url(#${id}-side)`}
            />
          );
        })}
        <path
          d={outline}
          fill={`url(#${id}-front)`}
          stroke="var(--mat-aluminium-edge)"
          strokeWidth="1.5"
        />
        {family.chambers ? (
          <path
            d={family.chambers}
            fill="var(--surface-sheet)"
            stroke="var(--mat-aluminium-edge)"
            strokeWidth={metal ? 1 : 2.6}
          />
        ) : null}
        {family.gasket ? (
          <path d={family.gasket} stroke="var(--mat-gasket)" strokeWidth="3" fill="none" />
        ) : null}
      </g>
    </svg>
  );
}
