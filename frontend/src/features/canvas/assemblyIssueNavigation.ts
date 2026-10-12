import type { ProductIssue } from "../../api/generated/models";
import type { ProductJson } from "./productEditing";

/** An issue must lead to the control that can repair it, rather than merely
 * highlight a joint whose dimensions live in a different inspector. */
export function assemblyIssueDestination(issue: ProductIssue, product: ProductJson) {
  const { modules, couplings } = product.assembly;
  const jointIndex = couplings.findIndex((item) => `coupling:${item.id}` === issue.target);
  const joint = couplings[jointIndex];
  let target = issue.target;
  let field = issue.params.field;
  if (issue.code === "coupler_height_mismatch" || issue.code === "coupler_width_mismatch") {
    target = `module:${joint?.modules?.[0] ?? modules[Math.max(0, jointIndex)]?.id}`;
    field = issue.code === "coupler_height_mismatch" ? "height_mm" : "width_mm";
  } else if (
    ["coupler_angle_incompatible", "coupler_profile_missing", "coupler_profile_unknown"].includes(
      issue.code,
    )
  ) {
    field = "coupler_profile_sku";
  } else if (
    ["assembly_folds_back", "plan_self_intersection", "plan_depth_collision"].includes(issue.code)
  ) {
    target = joint ? issue.target : `coupling:${couplings.at(-1)?.id}`;
    field = "angle_deg";
  } else if (
    issue.code === "module_geometry_failed" &&
    /glass_thickness_mm|glass_spec/i.test(issue.params.reason ?? "")
  ) {
    field = "glass";
  } else if (
    issue.code === "coupler_reinforcement_nonpositive" ||
    (issue.code === "module_geometry_failed" && joint)
  ) {
    field = "catalog";
  }
  const labels: Record<string, string> = {
    height_mm: "Alto",
    width_mm: "Ancho",
    coupler_profile_sku: "Acoplador",
    angle_deg: "Ángulo",
    glass: "Vidrio",
  };
  return { target, field, label: labels[field ?? ""], catalog: field === "catalog" };
}
