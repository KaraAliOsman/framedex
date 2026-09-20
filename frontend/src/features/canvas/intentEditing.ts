import { normalizeDimensionCandidate } from "./snapping";

export const OPENINGS = [
  "FIXED",
  "TURN_LEFT",
  "TURN_RIGHT",
  "TILT_TURN_LEFT",
  "TILT_TURN_RIGHT",
  "SLIDING_2L",
  "AWNING",
  "DOOR_ENTRY",
] as const;

export type Opening = (typeof OPENINGS)[number];
export type SplitType = "SPLIT_V" | "SPLIT_H";

export type IntentNode = {
  id: string;
  type: "ROOT" | SplitType | "BAY";
  width_mm?: string | null;
  height_mm?: string | null;
  split_offset_mm?: string | null;
  mullion_profile_sku?: string | null;
  children?: IntentNode[];
  opening_type?: Opening | null;
  glass_thickness_mm?: string | null;
  glass_spec?: string | null;
  glass_article_sku?: string | null;
  panel_article_sku?: string | null;
  hardware_set_sku?: string | null;
  handle_height_mm?: string | null;
};

export function walkIntent(tree: IntentNode): IntentNode[] {
  const nodes: IntentNode[] = [];
  const ids = new Set<string>();

  function visit(node: IntentNode): void {
    if (!node.id || ids.has(node.id)) throw new Error("invalid_node_identity");
    ids.add(node.id);
    nodes.push(node);
    for (const child of node.children ?? []) visit(child);
  }

  visit(tree);
  return nodes;
}

export function intentBays(tree: IntentNode): IntentNode[] {
  return walkIntent(tree).filter((node) => node.type === "BAY");
}

export function topIntent(tree: IntentNode): IntentNode {
  if (tree.type !== "ROOT") return tree;
  if (tree.children?.length !== 1 || !tree.children[0]) {
    throw new Error("invalid_root");
  }
  return tree.children[0];
}

export function selectedBay(tree: IntentNode, id: string): IntentNode {
  const node = walkIntent(tree).find((candidate) => candidate.id === id);
  if (!node || node.type !== "BAY") throw new Error("bay_unavailable");
  return node;
}

/** Formatting only: no rounding, unit conversion, or geometry calculation. */
export function exactMm(value: string): string {
  const normalized = normalizeDimensionCandidate(value.trim().replace(",", "."));
  if (normalized === null) throw new Error("invalid_dimension");
  return normalized;
}

function omitDimensions(node: IntentNode): IntentNode {
  const result = { ...node };
  delete result.width_mm;
  delete result.height_mm;
  return result;
}

/** The API envelope owns nominal dimensions. Derived child dimensions are untouched. */
export function requestTree(tree: IntentNode): IntentNode {
  walkIntent(tree);
  const root = omitDimensions(tree);
  if (root.type !== "ROOT") return root;
  return { ...root, children: [omitDimensions(topIntent(tree))] };
}

function replaceNode(tree: IntentNode, id: string, replacement: IntentNode): IntentNode {
  if (tree.id === id) return replacement;
  if (!tree.children?.length) return tree;
  const children = tree.children.map((child) => replaceNode(child, id, replacement));
  return children.every((child, index) => child === tree.children?.[index])
    ? tree
    : { ...tree, children };
}

export function changeOpening(tree: IntentNode, bayId: string, opening: Opening): IntentNode {
  const bay = selectedBay(tree, bayId);
  if (!OPENINGS.includes(opening)) throw new Error("unsupported_opening");
  if (opening === "DOOR_ENTRY" && topIntent(tree).id !== bayId) {
    throw new Error("door_requires_top_bay");
  }

  // Preserve explicit catalog choices. Engine validates their compatibility.
  return requestTree(replaceNode(tree, bayId, { ...bay, opening_type: opening }));
}

export function splitBay(
  tree: IntentNode,
  bayId: string,
  division: {
    type: SplitType;
    offsetMm: string;
    mullionSku: string;
  },
  ids: { split: string; secondBay: string },
): IntentNode {
  const bay = selectedBay(tree, bayId);
  if (bay.opening_type === "DOOR_ENTRY") {
    throw new Error("door_requires_top_bay");
  }
  if (!["SPLIT_V", "SPLIT_H"].includes(division.type) || !division.mullionSku.trim()) {
    throw new Error("invalid_division");
  }

  const existing = new Set(walkIntent(tree).map((node) => node.id));
  if (
    !ids.split ||
    !ids.secondBay ||
    ids.split === ids.secondBay ||
    existing.has(ids.split) ||
    existing.has(ids.secondBay)
  ) {
    throw new Error("invalid_node_identity");
  }

  const first = omitDimensions(bay);
  const replacement: IntentNode = {
    id: ids.split,
    type: division.type,
    split_offset_mm: exactMm(division.offsetMm),
    mullion_profile_sku: division.mullionSku,
    children: [first, { ...first, id: ids.secondBay }],
  };

  return requestTree(replaceNode(tree, bayId, replacement));
}

/** Explicit user action replaces the layout while retaining the chosen infill. */
export function moveDivision(tree: IntentNode, divisionId: string, offset: string): IntentNode {
  const node = walkIntent(tree).find((item) => item.id === divisionId);
  if (!node || (node.type !== "SPLIT_H" && node.type !== "SPLIT_V"))
    throw new Error("division_unavailable");
  return requestTree(replaceNode(tree, divisionId, { ...node, split_offset_mm: exactMm(offset) }));
}

/** Explicit user action replaces the layout while retaining the chosen infill. */
export function singleBayTemplate(tree: IntentNode, bayId: string, opening: Opening): IntentNode {
  if (!OPENINGS.includes(opening)) throw new Error("unsupported_opening");
  const bay = omitDimensions(selectedBay(tree, bayId));
  return { ...bay, opening_type: opening };
}
