import { applyDesignOpOn } from "../commands/registry";
import type { CommandSpec, DesignOp } from "../commands/types";
import { ASSEMBLY_COMMANDS } from "./assemblyCommands";
import type { ProductJson } from "./productEditing";

export type { DesignOp };

/** Wire op → product: dispatched through the shared command registry — the
 * same `apply` a palette row or context-menu action commits. The backend has
 * already bounds-checked the op; unknown or undecodable ops are refused. */
export function applyDesignOp(
  product: ProductJson,
  op: DesignOp,
  specs: CommandSpec[] = ASSEMBLY_COMMANDS,
): ProductJson {
  return applyDesignOpOn(specs, product, op);
}

export function applyDesignOps(
  product: ProductJson,
  ops: DesignOp[],
  specs: CommandSpec[] = ASSEMBLY_COMMANDS,
): ProductJson {
  return ops.reduce((current, op) => applyDesignOp(current, op, specs), product);
}

/** Human one-line description of a wire op — the registry spec's `describe`
 * fed with the decoded args (so `módulo 2`, not a raw id). */
export function describeDesignOp(
  op: DesignOp,
  product: ProductJson,
  specs: CommandSpec[] = ASSEMBLY_COMMANDS,
): string {
  for (const spec of specs) {
    if (spec.ai?.op !== op.op || !spec.describe) continue;
    const args = spec.ai.decode(op, product);
    if (args === null) continue;
    return spec.describe(args);
  }
  return String(op.op);
}
