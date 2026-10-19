/** Recognisable profile family illustrations (encargo O17). They help tell a
 * frame from a sash or a bead when the catalog has no verified section. They
 * are scaled to the declared face width and depth only; the shape itself is
 * illustrative and is always labelled as such — never a fabrication section. */

export type ProfileFamily =
  "frame" | "sash" | "mullion" | "bead" | "threshold" | "coupler" | "generic";

export function familyForRole(role: string | null | undefined): ProfileFamily {
  const value = (role ?? "").toUpperCase();
  if (value.startsWith("FRAME") || value === "OUTER_FRAME") return "frame";
  if (value.startsWith("SASH") || value.includes("LEAF")) return "sash";
  if (value.startsWith("MULLION") || value.startsWith("TRANSOM")) return "mullion";
  if (value.includes("BEAD")) return "bead";
  if (value.includes("THRESHOLD") || value.includes("SILL")) return "threshold";
  if (value.includes("COUPLER")) return "coupler";
  return "generic";
}

export const FAMILY_LABEL: Record<ProfileFamily, string> = {
  frame: "Marco",
  sash: "Hoja",
  mullion: "Montante o travesaño",
  bead: "Junquillo",
  threshold: "Umbral",
  coupler: "Acople",
  generic: "Perfil",
};

/** Typical depth used only to give the illustration a plausible proportion
 * when no depth is declared. It is never shown as a measurement. */
const TYPICAL_DEPTH: Record<ProfileFamily, number> = {
  frame: 70,
  sash: 78,
  mullion: 70,
  bead: 22,
  threshold: 70,
  coupler: 70,
  generic: 60,
};

type P = [number, number];
function pts(list: P[], w: number, d: number): string {
  const at = (value: number) => Math.round(value * 100) / 100;
  return list.map(([x, y]) => `${at(x * w)},${at(y * d)}`).join(" ");
}

/** Outline in unit space (x across the face, y through the depth; y=0 is the
 * room side). */
const OUTLINES: Record<ProfileFamily, P[]> = {
  frame: [
    [0, 0],
    [1, 0],
    [1, 0.16],
    [0.58, 0.16],
    [0.58, 0.3],
    [1, 0.3],
    [1, 1],
    [0, 1],
  ],
  sash: [
    [0, 0.08],
    [0.72, 0.08],
    [0.72, 0],
    [1, 0],
    [1, 0.84],
    [0.38, 0.84],
    [0.38, 1],
    [0, 1],
  ],
  mullion: [
    [0, 0],
    [1, 0],
    [1, 0.16],
    [0.78, 0.16],
    [0.78, 1],
    [0.22, 1],
    [0.22, 0.16],
    [0, 0.16],
  ],
  bead: [
    [0, 0],
    [1, 0],
    [1, 0.25],
    [0.35, 1],
    [0, 1],
  ],
  threshold: [
    [0, 0.55],
    [0.2, 0.55],
    [0.2, 0.35],
    [1, 0.35],
    [1, 1],
    [0, 1],
  ],
  coupler: [
    [0, 0],
    [1, 0],
    [1, 0.12],
    [0.62, 0.12],
    [0.62, 0.88],
    [1, 0.88],
    [1, 1],
    [0, 1],
    [0, 0.88],
    [0.38, 0.88],
    [0.38, 0.12],
    [0, 0.12],
  ],
  generic: [
    [0, 0],
    [1, 0],
    [1, 1],
    [0, 1],
  ],
};

export function familyDepth(family: ProfileFamily, declared?: number | null): number {
  return declared && declared > 0 ? declared : TYPICAL_DEPTH[family];
}

export function FamilyIllustration({
  family,
  widthMm,
  depthMm,
  material,
  fill,
  edge,
}: {
  family: ProfileFamily;
  widthMm: number;
  depthMm: number;
  material: string;
  fill: string;
  edge: string;
}): JSX.Element {
  const w = Math.max(widthMm, 1);
  const d = Math.max(depthMm, 1);
  const aluminium = material.toUpperCase().startsWith("ALUMIN");
  const outline = OUTLINES[family];
  const chambers =
    !aluminium && ["frame", "sash", "mullion", "threshold"].includes(family)
      ? [0.18, 0.42, 0.66].map((y) => (
          <rect
            key={y}
            className="section-family__chamber"
            x={w * 0.12}
            y={d * (y + 0.06)}
            width={w * 0.76}
            height={d * 0.16}
            style={{ stroke: edge }}
          />
        ))
      : null;
  return (
    <g className="section-family">
      <polygon
        className="section-family__shape"
        points={pts(outline, w, d)}
        style={{ fill, stroke: edge }}
      />
      {chambers}
      {aluminium && family !== "bead" ? (
        <rect
          className="section-family__break"
          x={0}
          y={d * 0.47}
          width={w}
          height={d * 0.08}
          style={{ fill: edge }}
        />
      ) : null}
    </g>
  );
}
