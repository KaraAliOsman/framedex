import { useEffect, useSyncExternalStore } from "react";

import { t } from "../../i18n/es-CL";
import type {
  CommandArgs,
  CommandContext,
  CommandSpec,
  CommandSurface,
  DesignOp,
  ResolvedCommand,
} from "./types";
import type { ProductJson } from "../canvas/productEditing";

/** One registered command surface at a time (the editor contributes its
 * commands while mounted). Listeners fire on register/unregister so an open
 * palette always reflects the live surface. */
let current: CommandSurface | null = null;
const listeners = new Set<() => void>();

function emit(): void {
  for (const listener of listeners) listener();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** Register the surface's commands while the surface is mounted. Pass a
 * memoized `CommandSurface` — the palette reads it directly. */
export function useRegisterCommands(surface: CommandSurface | null): void {
  useEffect(() => {
    if (!surface) return;
    current = surface;
    emit();
    return () => {
      if (current === surface) {
        current = null;
        emit();
      }
    };
  }, [surface]);
}

export function useCommandSurface(): CommandSurface | null {
  return useSyncExternalStore(
    subscribe,
    () => current,
    () => null,
  );
}

/** Resolve the registry's specs against the live context into the surface
 * list: titles translated, params collected, `run` bound to the single
 * dispatch path. */
export function resolveCommands(ctx: CommandContext, specs: CommandSpec[]): ResolvedCommand[] {
  return specs.map((spec) => ({
    id: spec.id,
    title: t(spec.title),
    keywords: spec.keywords,
    params: spec.params?.(ctx),
    describe: spec.describe,
    run: (args: CommandArgs) => runCommand(ctx, spec, args),
  }));
}

/** Execute a command through the single shared path: mutation commands commit
 * `apply`'s result (one undoable transaction), non-mutating commands run their
 * own effect. Palette, shortcuts, context menus and AI all land here. */
export function runCommand(ctx: CommandContext, spec: CommandSpec, args: CommandArgs = {}): void {
  if (spec.apply) {
    ctx.commit(spec.apply(ctx, args));
  } else {
    spec.run?.(ctx, args);
  }
}

/** Resolve a wire op to its command spec (the AI seam). */
export function specForOp(specs: CommandSpec[], op: string): CommandSpec | null {
  return specs.find((spec) => spec.ai?.op === op) ?? null;
}

/** Apply one backend-validated wire op through the shared command table. The
 * op decodes to the same args a palette would collect, then hits the same
 * `apply` a human action uses. Unknown/undecodable ops are refused. Several
 * specs may share an op name (e.g. add_unit left/right) — the first whose
 * decoder accepts the op wins. */
export function applyDesignOpOn(
  specs: CommandSpec[],
  product: ProductJson,
  op: DesignOp,
): ProductJson {
  for (const spec of specs) {
    if (spec.ai?.op !== op.op || !spec.apply) continue;
    const args = spec.ai.decode(op, product);
    if (args === null) continue;
    const ctx: CommandContext = {
      product,
      selection: null,
      catalog: {
        glassThicknesses: [],
        glassSkus: [],
        couplerSkus: [],
        panelSkus: [],
        mullionSkus: {},
      },
      disabled: false,
      commit: () => {},
      select: () => {},
    };
    return spec.apply(ctx, args);
  }
  return product;
}
