import type {
  DesignOperationRequest,
  OperationSetBaySpecRequest,
} from "../../api/generated/models";
import type { IntentNode, SlidingLayout } from "./intentEditing";

/** Translate declared inspector choices to the shared contract. All derived
 * geometry, glazing thickness and hardware validation belongs to the engine. */
export function bayOperations(
  module: string,
  bay: string,
  patch: Partial<IntentNode>,
): DesignOperationRequest[] {
  const ops: DesignOperationRequest[] = [];
  if (patch.opening || patch.opening_type) {
    ops.push({
      op: "set_opening",
      module,
      bay,
      opening: patch.opening ?? patch.opening_type!,
      ...(patch.opening_use ? { opening_use: patch.opening_use } : {}),
      ...(patch.hinged_layout !== undefined ? { hinged_layout: patch.hinged_layout } : {}),
      ...(patch.sliding_layout !== undefined ? { sliding_layout: patch.sliding_layout } : {}),
    });
  }
  if (patch.glass_article_sku)
    ops.push({ op: "set_glass", module, bay, sku: patch.glass_article_sku });
  if (patch.panel_article_sku !== undefined)
    ops.push({ op: "set_panel", module, bay, sku: patch.panel_article_sku });
  if (patch.handle_height_mm)
    ops.push({
      op: "set_handle_height",
      module,
      bay,
      height_mm: patch.handle_height_mm,
      reference: "LEAF_BOTTOM",
    });
  const declared: OperationSetBaySpecRequest["patch"] = {};
  if (patch.hardware_set_sku !== undefined) declared.hardware_set_sku = patch.hardware_set_sku;
  if (patch.hardware_selection !== undefined)
    declared.hardware_selection = patch.hardware_selection;
  if (patch.glass_processing !== undefined) declared.glass_processing = patch.glass_processing;
  if (patch.sill_height_mm !== undefined) declared.sill_height_mm = patch.sill_height_mm;
  if (patch.is_sidelight != null) declared.is_sidelight = patch.is_sidelight;
  if (patch.door_handedness !== undefined) declared.door_handedness = patch.door_handedness;
  if (Object.keys(declared).length) ops.push({ op: "set_bay_spec", module, bay, patch: declared });
  return ops;
}

export function slidingOperation(
  module: string,
  bay: string,
  layout: SlidingLayout,
): DesignOperationRequest {
  return {
    op: "set_sliding_layout",
    module,
    bay,
    tracks: layout.tracks,
    panels: layout.panels.map((panel) => (panel.kind === "MOVING" ? "X" : "O")).join(""),
    panel_tracks: layout.panels.map((panel) => panel.track),
  };
}
