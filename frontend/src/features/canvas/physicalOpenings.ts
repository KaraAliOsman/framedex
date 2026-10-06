import type { IntentNode, Opening as LegacyOpening } from "./intentEditing";
import type { DesignOptions } from "../../api/generated/models";

export type PhysicalOpening = {
  movement:
    | "FIXED"
    | "TURN"
    | "TILT"
    | "TILT_TURN"
    | "TOP_HUNG"
    | "BOTTOM_HUNG"
    | "SLIDE"
    | "LIFT_SLIDE"
    | "PARALLEL_SLIDE"
    | "FOLD"
    | "PIVOT_V"
    | "PIVOT_H"
    | "VERTICAL_SLIDE";
  hinge_side: "LEFT" | "RIGHT" | "TOP" | "BOTTOM" | "NONE";
  direction: "INWARD" | "OUTWARD";
  leaf_role: "SINGLE" | "ACTIVE" | "PASSIVE";
  fixed_in_sash: boolean;
};
export type HingedLayout = {
  leaves: { slot: "LEFT" | "RIGHT"; opening: PhysicalOpening; hardware_set_sku?: string | null }[];
};
export type OpeningChoice = {
  id: string;
  label: string;
  opening: PhysicalOpening;
  use: "WINDOW" | "DOOR";
  layout?: HingedLayout;
  source: string;
};
export type OpeningLeafFact = {
  bay_id: string;
  leaf_id: string | null;
  opening: PhysicalOpening;
  use: string;
  x_mm: string;
  y_mm: string;
  width_mm: string;
  height_mm: string;
  source: string;
  handle: {
    side: string;
    x_mm: string;
    y_mm: string;
    height_from_bottom_mm: string;
    minimum_height_from_bottom_mm: string;
    maximum_height_from_bottom_mm: string;
    minimum_from_top_mm: string;
    maximum_from_top_mm: string;
    source: string;
  } | null;
};
export type Capability = {
  use: "WINDOW" | "DOOR";
  movement: PhysicalOpening["movement"];
  direction: PhysicalOpening["direction"];
  leaf_role: PhysicalOpening["leaf_role"];
  fixed_in_sash: boolean;
  hinge_sides: PhysicalOpening["hinge_side"][];
  hardware_kit_skus: string[];
  source: string;
  handle_rule: {
    vertical_reference: string;
    default_height_mm: string | null;
    minimum_from_top_mm: string;
    minimum_from_bottom_mm: string;
    closing_edge_offset_mm: string;
    source: string;
  } | null;
};

/** Presentation decoder only: new intents keep their full physical object. */
export function visualOpening(node: IntentNode): LegacyOpening {
  if (!node.opening) return node.opening_type ?? "FIXED";
  const physical = node.opening;
  if (physical.movement === "FIXED") return "FIXED";
  if (physical.movement === "SLIDE") return "SLIDING";
  if (node.opening_use === "DOOR") return node.hinged_layout ? "DOOR_DOUBLE" : "DOOR_ENTRY";
  if (["TILT", "TOP_HUNG"].includes(physical.movement)) return "AWNING";
  return `${physical.movement === "TILT_TURN" ? "TILT_TURN" : "TURN"}_${physical.hinge_side === "LEFT" ? "LEFT" : "RIGHT"}` as LegacyOpening;
}

export function physicalLabel(opening: PhysicalOpening, use: string = "WINDOW"): string {
  if (opening.movement === "FIXED") return opening.fixed_in_sash ? "Fijo en hoja" : "Fijo en marco";
  if (opening.movement === "TILT") return "Solo abatimiento (banderola)";
  if (opening.movement === "TOP_HUNG") return "Proyectante hacia afuera";
  if (opening.movement === "SLIDE") return "Corredera";
  const kind =
    use === "DOOR"
      ? "Puerta simple"
      : opening.movement === "TILT_TURN"
        ? "Oscilobatiente"
        : "Abatible";
  return `${kind} hacia ${opening.direction === "INWARD" ? "adentro" : "afuera"} — bisagras a la ${opening.hinge_side === "LEFT" ? "izquierda" : "derecha"}`;
}
export function physicalNodeLabel(node: IntentNode): string | null {
  if (!node.opening) return null;
  const active = node.hinged_layout?.leaves.find((leaf) => leaf.opening.leaf_role === "ACTIVE");
  return active
    ? `${node.opening_use === "DOOR" ? "Puerta doble" : "Francesa 2 hojas"} — activa ${active.slot === "LEFT" ? "izquierda" : "derecha"} · hacia ${node.opening.direction === "INWARD" ? "adentro" : "afuera"}`
    : physicalLabel(node.opening, node.opening_use ?? "WINDOW");
}
export function openingChoices(options: DesignOptions | undefined): OpeningChoice[] {
  const caps = (options?.opening_capabilities ?? []) as unknown as Capability[];
  const choices: OpeningChoice[] = [];
  for (const cap of caps) {
    if (cap.leaf_role === "PASSIVE") continue;
    for (const side of cap.hinge_sides) {
      const opening: PhysicalOpening = {
        movement: cap.movement,
        hinge_side: side,
        direction: cap.direction,
        leaf_role: cap.leaf_role,
        fixed_in_sash: cap.fixed_in_sash,
      };
      const choice: OpeningChoice = {
        id: [cap.use, cap.movement, cap.direction, cap.leaf_role, cap.fixed_in_sash, side].join(
          "-",
        ),
        opening,
        use: cap.use,
        label: physicalLabel(opening, cap.use),
        source: cap.source,
      };
      if (cap.leaf_role === "ACTIVE") {
        const passive = caps.find(
          (other) =>
            other.use === cap.use &&
            other.movement === cap.movement &&
            other.direction === cap.direction &&
            other.leaf_role === "PASSIVE" &&
            other.hinge_sides.includes(side === "LEFT" ? "RIGHT" : "LEFT"),
        );
        if (!passive || !options?.paired_leaf_rule) continue;
        choice.layout = {
          leaves: (["LEFT", "RIGHT"] as const).map((slot) => ({
            slot,
            opening: {
              ...opening,
              hinge_side: slot,
              leaf_role: slot === side ? "ACTIVE" : "PASSIVE",
            },
          })),
        };
        choice.label = `${cap.use === "DOOR" ? "Puerta doble" : "Francesa 2 hojas"} — activa ${side === "LEFT" ? "izquierda" : "derecha"} · hacia ${cap.direction === "INWARD" ? "adentro" : "afuera"}`;
      }
      choices.push(choice);
    }
  }
  return choices;
}
export function choicePatch(choice: OpeningChoice): Partial<IntentNode> {
  return {
    opening_type: null,
    opening: choice.opening,
    opening_use: choice.use,
    hinged_layout: choice.layout ?? null,
    hardware_set_sku: null,
    handle_height_mm: null,
    door_handedness: null,
    panel_article_sku: null,
    sliding_layout:
      choice.opening.movement === "SLIDE"
        ? {
            tracks: 2,
            panels: [
              { slot: "S1", kind: "MOVING", track: 0 },
              { slot: "S2", kind: "MOVING", track: 1 },
            ],
          }
        : null,
  };
}

/** JSON member order is irrelevant after API serialization or reopening. */
export function choiceMatches(bay: IntentNode, choice: OpeningChoice): boolean {
  const physical = bay.opening;
  return Boolean(
    physical &&
    (Object.keys(choice.opening) as (keyof PhysicalOpening)[]).every(
      (key) => physical[key] === choice.opening[key],
    ) &&
    (bay.opening_use ?? "WINDOW") === choice.use &&
    Boolean(bay.hinged_layout) === Boolean(choice.layout),
  );
}

export function structuredOpeningPatch(value: unknown): Partial<IntentNode> | null {
  if (!value || typeof value !== "object") return null;
  const data = value as Record<string, unknown>;
  function physical(raw: unknown): raw is PhysicalOpening {
    if (!raw || typeof raw !== "object") return false;
    const opening = raw as PhysicalOpening;
    return (
      ["FIXED", "TURN", "TILT", "TILT_TURN", "TOP_HUNG", "SLIDE"].includes(opening.movement) &&
      ["LEFT", "RIGHT", "TOP", "BOTTOM", "NONE"].includes(opening.hinge_side) &&
      ["INWARD", "OUTWARD"].includes(opening.direction) &&
      ["SINGLE", "ACTIVE", "PASSIVE"].includes(opening.leaf_role) &&
      typeof opening.fixed_in_sash === "boolean"
    );
  }
  if (!physical(data.opening) || !["DOOR", "WINDOW"].includes(String(data.opening_use)))
    return null;
  const layout = data.hinged_layout as HingedLayout | null | undefined;
  if (
    layout &&
    (!Array.isArray(layout.leaves) ||
      layout.leaves.length !== 2 ||
      layout.leaves.some((leaf) => !physical(leaf.opening)) ||
      layout.leaves[0]?.slot !== "LEFT" ||
      layout.leaves[1]?.slot !== "RIGHT")
  )
    return null;
  const sliding = data.sliding_layout as IntentNode["sliding_layout"];
  if (
    sliding &&
    (!Number.isInteger(sliding.tracks) ||
      !Array.isArray(sliding.panels) ||
      sliding.panels.some(
        (panel) => !["MOVING", "FIXED"].includes(panel.kind) || !Number.isInteger(panel.track),
      ))
  )
    return null;
  return {
    opening: data.opening,
    opening_type: null,
    opening_use: data.opening_use as "DOOR" | "WINDOW",
    hinged_layout: layout ?? null,
    sliding_layout: sliding ?? null,
    hardware_set_sku: null,
    handle_height_mm: null,
    door_handedness: null,
  };
}
