import type { DesignOptions } from "../../api/generated/models";
import type { IntentNode } from "./intentEditing";
import type { ProductJson } from "./productEditing";
import { choicePatch, openingChoices, visualOpening } from "./physicalOpenings";

/** New coupled recipes use the sourced physical opening grammar. Old saved
 * designs retain their original intent and catalog bytes. Recipe openings
 * are inward, in-frame fixed and single-leaf unless explicitly paired. */
export function sourcedStarter(product: ProductJson, options?: DesignOptions): ProductJson {
  if (!options || product.assembly.modules.length < 2) return product;
  const choices = openingChoices(options);
  function visit(node: IntentNode): IntentNode {
    if (node.type !== "BAY") return { ...node, children: node.children?.map(visit) };
    if (node.opening) return node;
    const matches = choices.filter(
      (choice) =>
        choice.opening.direction === "INWARD" &&
        !choice.opening.fixed_in_sash &&
        choice.opening.leaf_role === "SINGLE" &&
        (node.opening_type !== "DOOR_ENTRY" ||
          choice.opening.hinge_side === node.door_handedness) &&
        visualOpening({ ...node, ...choicePatch(choice) }) === (node.opening_type ?? "FIXED"),
    );
    return matches.length === 1
      ? { ...node, ...choicePatch(matches[0]!), panel_article_sku: node.panel_article_sku }
      : node;
  }
  return {
    ...product,
    assembly: {
      ...product.assembly,
      modules: product.assembly.modules.map((module) => ({ ...module, tree: visit(module.tree) })),
    },
  };
}
