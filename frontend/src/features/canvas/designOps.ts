import { applyDesignOpOn } from "../commands/registry";
import type { CommandSpec, DesignOp, DesignOpState } from "../commands/types";
import { ASSEMBLY_COMMANDS } from "./assemblyCommands";
import type { ProductJson } from "./productEditing";
import type { DesignOperation } from "../../api/generated/models";

export type { DesignOp };

/** Content fingerprint (FNV-1a over the normalized wire payload) the backend
 * persists on each turn — a restored ops step refuses to apply when the live
 * product no longer matches the product its ops were validated against. */
export function productFingerprint(product: unknown): string {
  function canonical(value: unknown): unknown {
    if (Array.isArray(value)) return value.map(canonical);
    if (value && typeof value === "object") {
      return Object.fromEntries(
        Object.entries(value)
          .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
          .map(([key, item]) => [key, canonical(item)]),
      );
    }
    return value;
  }
  const text = JSON.stringify(canonical(product)) ?? "";
  let hash = 0x811c9dc5;
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

/** Both assistant surfaces send the complete graph, including bay geometry,
 * opening authority and context. Every content change invalidates a plan. */
export function designAssistProduct(product: ProductJson): ProductJson {
  return product;
}

/** Live edits consume complete engine effects. Intent-only legacy records may
 * be read below, but cannot authorize a new editor mutation. */
export function applyOperationEffects(
  product: ProductJson,
  ops: readonly DesignOperation[],
): ProductJson {
  return ops.reduce((current, op) => {
    if (typeof op.base_sig !== "string" || !op.result || typeof op.result !== "object") {
      throw new Error("operation_effect_required");
    }
    if (productFingerprint(current) !== op.base_sig) throw new Error("proposal_stale");
    const next = op.result as ProductJson;
    if (next.version !== "product-v2" || !Array.isArray(next.assembly?.modules)) {
      throw new Error("invalid_operation_effect");
    }
    return next;
  }, product);
}

/** Wire op → product: dispatched through the shared command registry — the
 * same `apply` a palette row or context-menu action commits. The backend has
 * already bounds-checked the op; unknown or undecodable ops are refused. */
export function applyDesignOp(
  product: ProductJson,
  op: DesignOp,
  specs: CommandSpec[] = ASSEMBLY_COMMANDS,
  state?: DesignOpState,
): ProductJson {
  // New registry operations carry the engine's complete, validated effect.
  // The browser performs no geometric or commercial arithmetic here.
  if (typeof op.base_sig === "string" && op.result && typeof op.result === "object") {
    if (productFingerprint(product) !== op.base_sig) throw new Error("proposal_stale");
    const next = op.result as ProductJson;
    if (next.version !== "product-v2" || !Array.isArray(next.assembly?.modules)) {
      throw new Error("invalid_operation_effect");
    }
    return next;
  }
  return applyDesignOpOn(specs, product, op, state);
}

/** Ids minted by one apply — the modules/couplings in `next` absent from
 * `before` — join the sequence's synthetic-ref state in creation order. */
function harvestAdded(state: DesignOpState, before: ProductJson, next: ProductJson): void {
  const moduleIds = new Set(before.assembly.modules.map((module) => module.id));
  const couplingIds = new Set(before.assembly.couplings.map((coupling) => coupling.id));
  state.addedModules.push(
    ...next.assembly.modules
      .filter((module) => !moduleIds.has(module.id))
      .map((module) => module.id),
  );
  state.addedCouplings.push(
    ...next.assembly.couplings
      .filter((coupling) => !couplingIds.has(coupling.id))
      .map((coupling) => coupling.id),
  );
}

export function applyDesignOps(
  product: ProductJson,
  ops: (DesignOp | DesignOperation)[],
  specs: CommandSpec[] = ASSEMBLY_COMMANDS,
): ProductJson {
  // Synthetic refs resolve in apply order: after each structural op, the ids
  // it minted join the state so `added_m1`/`added_c2` in a later op points at
  // the real entity the sequence produced, never a guess.
  const state: DesignOpState = { addedModules: [], addedCouplings: [], origin: product };
  return ops.reduce((current, op) => {
    const next = applyDesignOp(current, { ...op }, specs, state);
    harvestAdded(state, current, next);
    return next;
  }, product);
}

/** Human one-line description of a wire op — the registry spec's `describe`
 * fed with the decoded args (so `módulo 2`, not a raw id). `priorOps` replays
 * the sequence's earlier ops so refs minted mid-sequence ('módulo nueva 1')
 * resolve to the entity they'd produce. */
export function describeDesignOp(
  op: DesignOp | DesignOperation,
  product: ProductJson,
  priorOps: (DesignOp | DesignOperation)[] = [],
  specs: CommandSpec[] = ASSEMBLY_COMMANDS,
): string {
  if (typeof op.description === "string") return op.description;
  const state: DesignOpState = { addedModules: [], addedCouplings: [], origin: product };
  const evolved = priorOps.reduce((current, prior) => {
    const next = applyDesignOp(current, { ...prior }, specs, state);
    harvestAdded(state, current, next);
    return next;
  }, product);
  for (const spec of specs) {
    if (spec.ai?.op !== op.op || !spec.describe) continue;
    const args = spec.ai.decode({ ...op }, evolved, state);
    if (args === null) continue;
    return spec.describe(args);
  }
  return String(op.op);
}
