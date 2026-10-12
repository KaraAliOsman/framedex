import type { FinishColor } from "../../api/generated/models";
import type { HardwareClass } from "./hardwareContracts";
import type { IntentNode } from "./intentEditing";
import type { MemberGeometry } from "./members";

/** The selected/default handle color is declared by the hardware class. */
export function bayHardwareColor(
  members: MemberGeometry,
  bay: IntentNode,
): FinishColor | undefined {
  const kit = members.kitFor(bay.hardware_set_sku ?? null);
  const authority = kit?.class_authority as HardwareClass | null | undefined;
  const handle = authority?.handles?.find(
    (h) => h.code === (bay.hardware_selection?.handle_code ?? authority.default_handle),
  );
  const code = bay.hardware_selection?.color_code ?? handle?.default_color;
  return members.finish?.handle_colors?.find((color) => color.code === code);
}
